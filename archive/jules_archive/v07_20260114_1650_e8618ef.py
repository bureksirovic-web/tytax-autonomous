import os
import re
import git
import requests
import json
import time
import html.parser

# --- CONFIGURATION ---
REPO_PATH = "."
API_KEY = os.environ.get("GEMINI_API_KEY")
MAX_RUNTIME_MINUTES = 45  # GitHub Actions limit is usually 60m
START_TIME = time.time()

if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set!")

MODELS_TO_TRY = [
    "gemini-2.0-flash-exp",
    "gemini-2.5-pro",
    "gemini-3-flash-preview"
]

def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filename, content):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

def get_next_task():
    content = read_file("BACKLOG.md")
    # Matches any bold text after an unchecked box
    match = re.search(r'- \[ \] \*\*(.*?)\*\*', content)
    if match:
        return match.group(1).strip()
    return None

def mark_task_done(task_name):
    content = read_file("BACKLOG.md")
    updated = content.replace(f"- [ ] **{task_name}**", f"- [x] **{task_name}**")
    write_file("BACKLOG.md", updated)

def extract_code_block(response_text):
    match = re.search(r'```html(.*?)```', response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    if "<!DOCTYPE html>" in response_text:
        return response_text
    return None

def validate_html_structure(code):
    """Simple self-correction check."""
    errors = []
    if "<!DOCTYPE html>" not in code:
        errors.append("Missing <!DOCTYPE html> declaration.")
    if "</html>" not in code:
        errors.append("Missing closing </html> tag.")
    if "<script" in code and "</script>" not in code:
        errors.append("Unclosed <script> tag detected.")
    
    # Python's built-in parser to catch nesting errors
    try:
        parser = html.parser.HTMLParser()
        parser.feed(code)
    except Exception as e:
        errors.append(f"HTML Parsing Error: {str(e)}")
        
    return errors

def ask_gemini(prompt):
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for model_name in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
        max_retries = 3
        for attempt in range(max_retries):
            # print(f"🔄 Connecting to {model_name}...") # Quiet mode for logs
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data))
                if response.status_code == 200:
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
                elif response.status_code in [429, 503]:
                    time.sleep(20 * (attempt + 1))
                else:
                    break
            except Exception:
                time.sleep(5)
    return None

def process_single_task():
    task = get_next_task()
    if not task:
        print("✅ No pending tasks found.")
        return False # Stop the loop

    print(f"\n📋 STARTING TASK: {task}")
    
    agents_doc = read_file("AGENTS.md")
    arch_doc = read_file("ARCHITECTURE.md")
    current_code = read_file("index.html")
    original_lines = len(current_code.splitlines())

    prompt = f"""
    {agents_doc}
    CONTEXT: {arch_doc}
    CURRENT CODE: {current_code}
    YOUR MISSION: Implement: "{task}"
    RULES: Return FULL index.html. No shortening.
    """

    # --- ATTEMPT 1: GENERATE ---
    print("💡 Thinking (Attempt 1)...")
    raw_response = ask_gemini(prompt)
    if not raw_response: return True # Skip to next loop if API fails

    new_code = extract_code_block(raw_response)
    if not new_code:
        print("❌ Failed to extract code.")
        return True

    # --- SELF-CORRECTION LOOP ---
    validation_errors = validate_html_structure(new_code)
    
    # Size check is a critical validation error too
    new_lines = len(new_code.splitlines())
    if new_lines < (original_lines * 0.8):
        validation_errors.append(f"Critical Code Loss: File shrank from {original_lines} to {new_lines} lines.")

    if validation_errors:
        print(f"⚠️ SELF-CORRECTION TRIGGERED: {validation_errors}")
        print("🔧 Asking Jules to fix his own mistakes...")
        
        correction_prompt = f"""
        You generated code for "{task}" but it failed validation:
        ERRORS: {'; '.join(validation_errors)}
        
        PREVIOUS ATTEMPT:
        {new_code}
        
        MISSION: Fix these specific errors and return the COMPLETE valid index.html.
        """
        
        raw_response = ask_gemini(correction_prompt)
        fixed_code = extract_code_block(raw_response)
        
        if fixed_code:
            print("✅ Fix received. Verifying again...")
            # Re-validate the fix
            if len(fixed_code.splitlines()) > (original_lines * 0.8):
                new_code = fixed_code # Accept the fix
            else:
                print("❌ Fix failed size check. Aborting task safely.")
                return True
        else:
            print("❌ Fix failed to generate code. Aborting task.")
            return True

    # --- SAVE & COMMIT ---
    print("💾 Saving verified code...")
    write_file("index.html", new_code)

    print("📦 Committing...")
    repo = git.Repo(REPO_PATH)
    repo.git.add(all=True)
    repo.index.commit(f"feat(jules): implemented {task}")
    
    mark_task_done(task)
    repo.git.add("BACKLOG.md")
    repo.index.commit(f"docs: marked {task} as done")
    
    print("🚀 Pushing...")
    try:
        repo.remotes.origin.push()
        print(f"✅ Success! {task} is LIVE.")
    except Exception as e:
        print(f"⚠️ Push failed: {e}")
        
    return True # Continue the loop

def run_loop():
    print("🤖 Jules is entering CONTINUOUS MODE...")
    while True:
        # Check time limit (leave 5 mins buffer for cleanup)
        elapsed = (time.time() - START_TIME) / 60
        if elapsed > (MAX_RUNTIME_MINUTES - 5):
            print("⏰ Time limit reached. Stopping to prevent timeout.")
            break
            
        # Run one task
        more_work = process_single_task()
        
        if not more_work:
            print("🎉 All tasks complete! Going to sleep.")
            break
            
        print("⏳ Taking a breath (10s) before next task...")
        time.sleep(10)

if __name__ == "__main__":
    run_loop()
