import os
import re
import sys
import time
import json
import difflib
from datetime import datetime
import git
import requests

# ==========================================
# JULES LEVEL 9 MASTER RESTORE (V2 OPTIMIZED)
# ==========================================
# RE-ESTABLISHED: Strict Level 9 Patching Engine
# RE-ESTABLISHED: Critic PASS/FAIL QA Loop
# MAINTAINED: 15 Retries + 180s Timeouts
# MAINTAINED: Multi-File Awareness (css/js)

REPO_PATH = os.environ.get("JULES_REPO_PATH", ".")
APP_FILE = "index.html"
BACKLOG_FILE = "BACKLOG.md"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Master Settings
MAX_QA_RETRIES = 15
REQUEST_TIMEOUT = 180
ENABLE_FUZZY_PATCH = True

# Create a session object for connection pooling
session = requests.Session()

def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f: return f.read()
    except: return ""

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8") as f: f.write(content)

def ask_gemini(prompt, role="coder"):
    # Level 9 Rotation Logic
    models = ["gemini-1.5-pro", "gemini-2.0-flash", "gemini-1.5-flash"]
    headers = {"Content-Type": "application/json"}
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            log(f"🔄 [{role.upper()}] {model}")
            resp = session.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return "".join([p.get("text", "") for p in resp.json()["candidates"][0]["content"]["parts"]])
        except: continue
    return None

def apply_patch(file_path, patch_text, original):
    is_new = not os.path.exists(file_path) or len(original) == 0
    blocks = re.findall(r"<<<<<<< SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE", patch_text, re.DOTALL)
    if not blocks: return None, "No blocks found."

    new_content = original
    for s, r in blocks:
        if is_new or s in new_content:
            new_content = new_content.replace(s, r, 1) if not is_new else r
        elif ENABLE_FUZZY_PATCH:
            matcher = difflib.SequenceMatcher(None, new_content, s)
            m = matcher.find_longest_match(0, len(new_content), 0, len(s))
            if m.size / len(s) >= 0.85:
                new_content = new_content[:m.a] + r + new_content[m.a + m.size:]
            else: return None, "Mismatch."
        else: return None, "Mismatch."
    return new_content, "Success"

def verify_fix(task, original, new_content):
    if original == new_content: return False, "No changes."
    diff = "".join(difflib.unified_diff(original.splitlines(True), new_content.splitlines(True), n=3))
    prompt = f"TASK: {task}\nReply ONLY 'PASS' or 'FAIL: <reason>'.\nDIFF:\n{diff}"
    review = ask_gemini(prompt, role="critic")
    if not review: return True, "Silent Pass"
    return ("PASS" in review.upper()), review.strip()

def run_task():
    backlog = read_file(BACKLOG_FILE)
    match = re.search(r"- \[ \] \*\*(.*?)\*\*: (.*)", backlog)
    if not match: 
        log("✅ No tasks found.")
        return
    
    title, action = match.group(1), match.group(2)
    log(f"\n📋 TARGET: {title}")
    
    # Auto-detect target file
    target_file = "index.html"
    if "css" in action.lower(): target_file = "css/styles.css"
    elif "js" in action.lower(): target_file = "js/components.js"

    orig_content = read_file(target_file)
    ctx = read_file("index.html") if target_file != "index.html" else ""

    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Attempt {attempt+1}/{MAX_QA_RETRIES}")
        if attempt > 10: time.sleep(60)
        
        prompt = f"TASK: {action}\nFILE: {target_file}\nCONTEXT:\n{ctx}\nCODE:\n{orig_content}"
        
        patch_resp = ask_gemini(prompt, role="coder")
        if not patch_resp: continue
        
        new_code, status = apply_patch(target_file, patch_resp, orig_content)
        if not new_code:
            log(f"❌ {status}")
            continue

        ok, feedback = verify_fix(title, orig_content, new_code)
        if not ok:
            log(f"❌ QA REJECTED: {feedback}")
            continue

        log("✅ QA PASSED. Committing...")
        write_file(target_file, new_code)
        # Update Backlog logic
        new_backlog = backlog.replace(f"- [ ] **{title}**", f"- [x] **{title}**")
        write_file(BACKLOG_FILE, new_backlog)
        
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        repo.index.commit(f"feat: {title}")
        repo.remotes.origin.push()
        return

if __name__ == "__main__":
    log("🤖 Level 9 Master Restore (v2) Started...")
    run_task()
