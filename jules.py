import os
import re
import git
import requests
import json
import time

# --- CONFIGURATION ---
REPO_PATH = "."
API_KEY = os.environ.get("GEMINI_API_KEY")

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
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for model_name in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
        max_retries = 3
        for attempt in range(max_retries):
            print(f"🔄 Connecting to {model_name} (Attempt {attempt+1}/{max_retries})...")
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data))
                if response.status_code == 200:
                    print(f"✅ CONNECTED! Using {model_name}.")
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
                elif response.status_code in [429, 503]:
                    wait_time = 20 * (attempt + 1)
                    print(f"⚠️ Rate Limit. Cooling down for {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Error {response.status_code}")
                    break
            except Exception as e:
                print(f"⚠️ Connection error: {e}")
                time.sleep(5)
    return None

def run_agent():
    print("🤖 Jules is waking up (Safe Mode)...")
    task = get_next_task()
    if not task:
        print("✅ No pending tasks.")
        return

    print(f"📋 Picking up: {task}")
    agents_doc = read_file("AGENTS.md")
    arch_doc = read_file("ARCHITECTURE.md")
    current_code = read_file("index.html")
    
    # 📏 Measure current size for safety check
    original_lines = len(current_code.splitlines())
    print(f"📏 Current File Size: {original_lines} lines")

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
    CRITICAL OUTPUT RULES:
    1. Return the FULL index.html code. Do not summarize.
    2. Do not remove existing features.
    3. If the code is too long, stop and output nothing.
    """

    print("💡 Thinking...")
    raw_response = ask_gemini(prompt)
    
    if not raw_response:
        return

    new_code = extract_code_block(raw_response)
    if not new_code:
        print("❌ Error: Valid HTML not found.")
        return

    # 🛡️ SAFETY VALVE: Check if file shrank suspiciously
    new_lines = len(new_code.splitlines())
    print(f"📏 New File Size: {new_lines} lines")
    
    if new_lines < (original_lines * 0.8): # If new file is < 80% of old file
        print(f"🚨 SAFETY TRIGGERED: New code is too short ({new_lines} vs {original_lines}). Aborting save.")
        print("⚠️ Jules tried to delete code or failed to generate the full file.")
        return

    print("💾 Saving (Safety Check Passed)...")
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
