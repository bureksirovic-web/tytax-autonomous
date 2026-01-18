import os
import re
import git
import requests
import json

# --- CONFIGURATION ---
REPO_PATH = "."
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set!")

# PRIORITY LIST: Tries Gemini 3 first. Falls back if access is denied.
MODELS_TO_TRY = [
    "gemini-3-pro-preview",    # The "Smartest" Brain (Paid/Preview)
    "gemini-3-flash-preview",  # Fast & New
    "gemini-2.5-pro",          # Reliable Previous Gen
    "gemini-2.0-flash-exp",    # Standard Flash
    "gemini-1.5-pro",          # Legacy Backup
    "gemini-1.5-flash"         # Ultimate Safety Net
]

def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filename, content):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

def get_next_task():
    content = read_file("BACKLOG.md")
    match = re.search(r'- \[ \] \*\*(Task \d+:.*?)\*\*', content)
    if match:
        return match.group(1)
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

def ask_gemini(prompt):
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    # "The Handshake": Try each model until one says "Hello"
    for model_name in MODELS_TO_TRY:
        print(f"🔄 Attempting connection to brain: {model_name}...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                print(f"✅ CONNECTED! Using {model_name}.")
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 404:
                 print(f"⚠️ {model_name} not found (might be paid-only). Trying next...")
            else:
                print(f"⚠️ {model_name} error ({response.status_code}). Trying next...")
        except Exception as e:
            print(f"⚠️ Connection error with {model_name}: {e}")

    print("❌ All models failed. Please check your API Key.")
    return None

def run_agent():
    print("🤖 Jules is waking up (Gemini 3 Upgrade)...")
    task = get_next_task()
    if not task:
        print("✅ No pending tasks.")
        return

    print(f"📋 Picking up: {task}")
    agents_doc = read_file("AGENTS.md")
    arch_doc = read_file("ARCHITECTURE.md")
    current_code = read_file("index.html")
    try:
        library = read_file("tytax_library.json")
    except:
        library = ""

    prompt = f"""
    {agents_doc}
    CONTEXT:
    {arch_doc}
    CURRENT LIBRARY SAMPLE:
    {library[:1000]}...
    CURRENT CODE:
    {current_code}
    YOUR MISSION:
    Implement: "{task}"
    OUTPUT RULES:
    1. Return ONLY the full, updated index.html code.
    2. Ensure the code is complete.
    """

    print("💡 Thinking... (Connecting to Google Cloud)")
    raw_response = ask_gemini(prompt)
    
    if not raw_response:
        return

    new_code = extract_code_block(raw_response)
    if not new_code:
        print("❌ Error: Valid HTML not found in response.")
        return

    print("💾 Saving...")
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
        print(f"✅ Success! {task} is live.")
    except Exception as e:
        print(f"⚠️ Push failed: {e}")

if __name__ == "__main__":
    run_agent()
