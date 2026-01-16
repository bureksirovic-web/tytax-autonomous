import os
import re
import git
import requests
import json
import time
import sys
import random
import difflib
from datetime import datetime

# --- CONFIGURATION ---
REPO_PATH = "."
# SANITIZATION: Critical fix for connection errors
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
RENDER_API_KEY = os.environ.get("RENDER_API_KEY", "").strip()
RENDER_SERVICE_ID = os.environ.get("RENDER_SERVICE_ID", "").strip()

# --- MODEL CONFIG (Restored Level 9 Stack) ---
# We use the smartest models because Level 9 proved they can write the complex React code.
CODER_MODELS = ["gemini-3-pro-preview", "gemini-2.0-flash-exp"]
CRITIC_MODEL = "gemini-3-pro-preview" 

MAX_QA_RETRIES = 4
REQUEST_TIMEOUT = 90 # Increased for 3.0 Pro
START_TIME = time.time()
MAX_RUNTIME_MINUTES = 60

def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)

if not GEMINI_API_KEY:
    log("❌ ERROR: GEMINI_API_KEY missing!")
    sys.exit(1)

def read_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f: return f.read()
    except: return ""

def write_file(filename, content):
    with open(filename, 'w', encoding='utf-8') as f: f.write(content)

# --- API ENGINE (Simplified from Level 9) ---
def ask_gemini(prompt, model_list, role="coder"):
    if isinstance(model_list, str): model_list = [model_list]
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.1}
    }
    
    for model in model_list:
        url = f"[https://generativelanguage.googleapis.com/v1beta/models/](https://generativelanguage.googleapis.com/v1beta/models/){model}:generateContent?key={GEMINI_API_KEY}"
        
        for attempt in range(2):
            try:
                log(f"🔄 [{role.upper()}] Asking {model} (Attempt {attempt+1})...")
                resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)
                
                if resp.status_code == 200:
                    try:
                        return resp.json()['candidates'][0]['content']['parts'][0]['text']
                    except: return None
                elif resp.status_code == 429:
                    log(f"⏳ Rate Limit. Sleeping 10s...")
                    time.sleep(10)
                elif resp.status_code == 404:
                    log(f"🚫 {model} not found. Skipping.")
                    break # Next model
                else:
                    log(f"❌ Error {resp.status_code}: {resp.text[:200]}")
                    
            except Exception as e:
                log(f"❌ Network Error: {e}")
    return None

# --- PATCH ENGINE (Level 9 + Markdown Stripper) ---
def apply_patch(original, patch):
    # FIX: Strip markdown code fences which caused Level 9 to fail on 'Set Deletion'
    clean_patch = re.sub(r'^`[a-zA-Z]*\s*$', '', patch, flags=re.MULTILINE).strip()
    
    pattern = r"<<<<<<< SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, clean_patch, re.DOTALL)
    
    if not matches:
        return None, "No blocks found. (Parser failed to find SEARCH/REPLACE pattern)"
    
    new_code = original
    applied_count = 0
    
    for search_block, replace_block in matches:
        # 1. Exact Match
        if search_block in new_code:
            new_code = new_code.replace(search_block, replace_block)
            applied_count += 1
        # 2. Whitespace Strip Match (The "Fuzzy" Logic from Level 9)
        elif search_block.strip() in new_code:
            new_code = new_code.replace(search_block.strip(), replace_block.strip())
            applied_count += 1
        else:
            return None, f"Block match failed. Could not find:\n{search_block[:50]}..."

    return new_code, f"Applied {applied_count} patches"

# --- VERIFICATION (The Level 9 Critic) ---
def verify_fix(task, original, new_code):
    if original == new_code: return False, "No changes detected."
    
    # Send a diff to the critic so it focuses on the changes
    diff = "".join(difflib.unified_diff(original.splitlines(True), new_code.splitlines(True), n=3))
    
    prompt = f"""
    ROLE: Senior Code Reviewer.
    TASK: {task}
    DIFF:
    {diff}
    
    VERIFICATION CHECKLIST:
    1. Does this fix the task?
    2. Are there syntax errors?
    3. Did it accidentally delete unrelated code?
    
    OUTPUT: 'PASS' or 'FAIL: [reason]'
    """
    
    response = ask_gemini(prompt, CRITIC_MODEL, role="critic")
    if not response: return True, "Critic silent, assuming safe."
    
    if "PASS" in response.upper(): return True, "Verified."
    return False, response

# --- DEPLOYMENT ---
def check_render():
    if not RENDER_API_KEY: return
    log("🚀 Watching Render...")
    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys?limit=1"
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    
    for _ in range(20):
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                status = resp.json()[0]['deploy']['status']
                log(f"📡 Status: {status}")
                if status == "live": return
                if status in ["build_failed", "canceled"]: return
        except: pass
        time.sleep(15)

def move_task_to_bottom(task_name):
    content = read_file("BACKLOG.md")
    lines = content.splitlines()
    new_lines = []
    task_line = ""
    for line in lines:
        if f"- [ ] **{task_name}**" in line:
            task_line = f"- [ ] **{task_name}** (SKIPPED)"
        else:
            new_lines.append(line)
    if task_line:
        new_lines.append("")
        new_lines.append("## ⚠️ SKIPPED TASKS")
        new_lines.append(task_line)
    write_file("BACKLOG.md", "\n".join(new_lines))

# --- MAIN ---
def process_task():
    backlog = read_file("BACKLOG.md")
    match = re.search(r'- \[ \] \*\*(.*?)\*\*(?!\s*\(SKIPPED)', backlog)
    if not match: return False
    task = match.group(1).strip()
    
    log(f"\n📋 TARGET: {task}")
    code = read_file("index.html")
    history = ""
    
    # Load minimal context (AGENTS.md only to keep tokens low, like Level 9)
    context = read_file("AGENTS.md")
    
    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Attempt {attempt+1}/{MAX_QA_RETRIES}...")
        
        prompt = f"""
TASK: {task}
CONTEXT: {context}
PREVIOUS ERRORS: {history}

INSTRUCTIONS:
1. Output SEARCH/REPLACE blocks.
2. NO MARKDOWN formatting (Do not use `).
3. Be precise with whitespace in SEARCH blocks.

CODE:
{code}
"""
        # 1. GENERATE
        patch = ask_gemini(prompt, CODER_MODELS, role="coder")
        if not patch: continue
        
        # 2. PATCH
        new_code, status = apply_patch(code, patch)
        if not new_code:
            log(f"❌ Patch Failed: {status}")
            history = f"Your SEARCH block failed to match. {status}"
            continue
            
        # 3. CRITIC
        is_valid, msg = verify_fix(task, code, new_code)
        if not is_valid:
            log(f"❌ Critic Rejected: {msg}")
            history = f"Critic feedback: {msg}"
            continue
            
        # 4. DEPLOY
        log("✅ QA Passed. Committing...")
        write_file("index.html", new_code)
        
        new_backlog = read_file("BACKLOG.md").replace(f"- [ ] **{task}**", f"- [x] **{task}**")
        write_file("BACKLOG.md", new_backlog)
        
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        repo.index.commit(f"feat(jules): {task}")
        repo.remotes.origin.push()
        
        check_render()
        return True

    log("⚠️ Task stuck. Moving to bottom.")
    move_task_to_bottom(task)
    
    repo = git.Repo(REPO_PATH)
    repo.git.add("BACKLOG.md")
    repo.index.commit("skip: stuck task")
    repo.remotes.origin.push()
    return True

if __name__ == "__main__":
    log("🤖 Jules Level 24 (HYBRID RESTORE) Started...")
    while process_task():
        time.sleep(5)
