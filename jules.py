import os
import re
import git
import requests
import json
import time
import sys
import random
from datetime import datetime

# --- CONFIGURATION ---
REPO_PATH = "."
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
RENDER_SERVICE_ID = os.environ.get("RENDER_SERVICE_ID")

# --- MODELS ---
CODER_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash-latest"]
SENTINEL_MODEL = "gemini-1.5-pro-latest"
MAX_QA_RETRIES = 4
REQUEST_TIMEOUT = 60
UNAVAILABLE_MODELS = set()

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

def call_gemini(model_list, prompt, temp=0.1, role="coder"):
    if isinstance(model_list, str): model_list = [model_list]
    for model in model_list:
        if model in UNAVAILABLE_MODELS: continue
        url = f"[https://generativelanguage.googleapis.com/v1beta/models/](https://generativelanguage.googleapis.com/v1beta/models/){model}:generateContent?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 8192, "temperature": temp}
        }
        try:
            log(f"🔄 [{role.upper()}] Asking {model}...")
            resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                try:
                    return resp.json()['candidates'][0]['content']['parts'][0]['text']
                except: return None
            elif resp.status_code == 404:
                log(f"🚫 Ghost: {model} not found.")
                UNAVAILABLE_MODELS.add(model)
            elif resp.status_code == 429:
                log(f"⏳ Rate Limit on {model}. Sleeping 5s...")
                time.sleep(5)
        except Exception as e:
            log(f"❌ API Error: {e}")
    return None

def sentinel_check(code, task):
    log("🛡️ Sentinel scanning...")
    prompt = f"ROLE: JS Compiler.\nTASK: Check for ReferenceErrors.\nCODE: {code[:15000]}...\nOUTPUT: PASS or FAIL: reason"
    response = call_gemini([SENTINEL_MODEL], prompt, temp=0.0, role="sentinel")
    if response and "PASS" in response: return True, "Safe"
    return False, response or "No response"

def apply_patch(original, patch):
    clean_patch = re.sub(r'^`[a-zA-Z]*\s*$', '', patch, flags=re.MULTILINE).strip()
    if "<<<<<<< SEARCH" not in clean_patch:
        log(f"⚠️ DEBUG - MODEL OUTPUT:\n{clean_patch[:300]}...")
        return None, "No SEARCH blocks found."

    pattern = r"<<<<<<< SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, clean_patch, re.DOTALL)
    
    if not matches: return None, "Regex failed."
    
    new_code = original
    for search, replace in matches:
        if search in new_code:
            new_code = new_code.replace(search, replace)
        elif search.strip() in new_code:
            new_code = new_code.replace(search.strip(), replace.strip())
        else:
            return None, "Search block match failed."
            
    if "<!DOCTYPE html>" not in new_code: return None, "CRITICAL: Root tag deleted."
    return new_code, "Applied"

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

def move_task_to_bottom(task_name, reason="Stuck"):
    content = read_file("BACKLOG.md")
    lines = content.splitlines()
    new_lines = []
    task_line = ""
    
    # 1. Filter out the stuck task
    for line in lines:
        if f"- [ ] **{task_name}**" in line:
            task_line = f"- [ ] **{task_name}** (SKIPPED: {reason})"
        else:
            new_lines.append(line)
    
    # 2. Append to bottom
    if task_line:
        new_lines.append("") 
        new_lines.append("## ⚠️ SKIPPED TASKS")
        new_lines.append(task_line)
        
    write_file("BACKLOG.md", "\n".join(new_lines))

def process_task():
    backlog = read_file("BACKLOG.md")
    # Fix regex to ignore (SKIPPED) tasks
    match = re.search(r'- \[ \] \*\*(.*?)\*\*(?!\s*\(SKIPPED)', backlog)
    if not match: return False
    task = match.group(1).strip()
    
    log(f"\n📋 TARGET: {task}")
    code = read_file("index.html")
    history = ""
    
    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Attempt {attempt+1}/{MAX_QA_RETRIES}...")
        
        prompt = f"""
TASK: {task}
CONTEXT: {read_file('AGENTS.md')}
PREVIOUS_ERRORS: {history}
CODE: {code}

INSTRUCTIONS:
1. Return ONLY the SEARCH/REPLACE blocks.
2. DO NOT wrap in Markdown (no `).

FORMAT:
<<<<<<< SEARCH
(exact code to remove)
=======
(new code to insert)
>>>>>>> REPLACE
"""
        patch = call_gemini(CODER_MODELS, prompt, role="coder")
        if not patch: continue
        
        new_code, status = apply_patch(code, patch)
        if not new_code:
            log(f"❌ Patch Failed: {status}")
            history = status
            continue
            
        is_safe, msg = sentinel_check(new_code, task)
        if not is_safe:
            log(f"🚫 SENTINEL BLOCKED: {msg}")
            history = msg
            continue
            
        log("✅ SUCCESS. Committing...")
        write_file("index.html", new_code)
        
        # Mark Done
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
    while process_task():
        time.sleep(5)
