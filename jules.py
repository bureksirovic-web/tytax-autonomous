import os
import re
import sys
import time
import json
import difflib
from datetime import datetime
import git
import requests

# ============================
# Jules Level 36.1 (MULTI-FILE MODULE)
# ============================

REPO_PATH = os.environ.get("JULES_REPO_PATH", ".")
BACKLOG_FILE = "BACKLOG.md"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Safety & Persistence Settings
MAX_QA_RETRIES = 15
REQUEST_TIMEOUT = 180
ENABLE_FUZZY_PATCH = True

def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f: return f.read()
    except: return ""

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8") as f: f.write(content)

def ask_gemini(prompt, models=["gemini-1.5-pro", "gemini-2.0-flash"]):
    headers = {"Content-Type": "application/json"}
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            log(f"🔄 [AI] {model}")
            resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return "".join([p.get("text", "") for p in resp.json()["candidates"][0]["content"]["parts"]])
        except: continue
    return None

def apply_patch(file_path, patch_text):
    original = read_file(file_path)
    # Detect if this is a NEW file creation
    is_new = not os.path.exists(file_path) or len(original) == 0
    
    # Extract blocks
    blocks = re.findall(r"<<<<<<< SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE", patch_text, re.DOTALL)
    if not blocks: return False, "No valid blocks."

    new_content = original
    for s, r in blocks:
        if is_new or s in new_content:
            new_content = new_content.replace(s, r, 1) if not is_new else r
        else:
            return False, "Search mismatch."
    
    write_file(file_path, new_content)
    return True, "Success"

def run_task():
    backlog = read_file(BACKLOG_FILE)
    match = re.search(r"- \[ \] \*\*(.*?)\*\*: (.*)", backlog)
    if not match: return
    
    title, action = match.group(1), match.group(2)
    log(f"📋 TARGET: {title}")
    
    # Determine which file Jules thinks he is editing
    target_file = "index.html"
    if "css" in action.lower(): target_file = "css/styles.css"
    if "js" in action.lower(): target_file = "js/components.js"

    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Attempt {attempt+1}/{MAX_QA_RETRIES}")
        content = read_file(target_file)
        prompt = f"TASK: {action}\nFILE: {target_file}\nRULES: Use SEARCH/REPLACE blocks.\nCODE:\n{content}"
        
        resp = ask_gemini(prompt)
        if resp and apply_patch(target_file, resp)[0]:
            log("✅ Success. Pushing...")
            write_file(BACKLOG_FILE, backlog.replace(f"- [ ] **{title}**", f"- [x] **{title}**"))
            repo = git.Repo(REPO_PATH)
            repo.git.add(all=True)
            repo.index.commit(f"feat: {title}")
            repo.remotes.origin.push()
            return

if __name__ == "__main__":
    run_task()
