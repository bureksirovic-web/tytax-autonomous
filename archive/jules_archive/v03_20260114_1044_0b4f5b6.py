import os
import re
import git
import requests
import json

# --- CONFIGURATION ---
REPO_PATH = "."
API_KEY = os.environ.get("GEMINI_API_KEY")
# We use the direct API URL to bypass library version issues
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set!")

def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filename, content):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

def get_next_task():
    content = read_file("BACKLOG.md")
    # Matches: - [ ] **Task 001: Title**
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
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    
    if response.status_code != 200:
        print(f"❌ API Error {response.status_code}: {response.text}")
        return None
        
    try:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        print(f"❌ Unexpected Response Format: {response.text}")
        return None

def run_agent():
    print("🤖 Jules is waking up (Direct Mode)...")
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
    2. No explanations.
    3. Ensure the code is complete.
    """

    print("💡 Thinking... (Sending Request)")
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
