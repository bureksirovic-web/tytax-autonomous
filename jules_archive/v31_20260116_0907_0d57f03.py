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

# --- 1. CONFIGURATION ---
REPO_PATH = "."
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
RENDER_SERVICE_ID = os.environ.get("RENDER_SERVICE_ID")

# --- 2. MULTI-MODEL SWARM CONFIG ---
# Coder: Fast, Creative (Writes the fix)
CODER_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-2.0-flash-exp"]

# Sentinel: Smart, Strict (Checks for crashes)
SENTINEL_MODEL = "gemini-1.5-pro-latest"

# Critic: Standard Review (Checks logic)
CRITIC_MODELS = ["gemini-1.5-flash-latest", "gemini-2.0-flash"]

MAX_QA_RETRIES = 4
REQUEST_TIMEOUT = 60
UNAVAILABLE_MODELS = set() # Ghost Protocol

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

# --- 3. INTELLIGENT API CALLER ---
def call_gemini(model_list, prompt, temp=0.1, role="coder"):
    # Ensure input is a list
    if isinstance(model_list, str): model_list = [model_list]
    
    for model in model_list:
        if model in UNAVAILABLE_MODELS: continue

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
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
                log(f"🚫 Ghost Protocol: {model} not found. Blacklisting.")
                UNAVAILABLE_MODELS.add(model)
            
            elif resp.status_code == 429:
                log(f"⏳ Rate Limit on {model}. Sleeping 5s...")
                time.sleep(5)
                
        except Exception as e:
            log(f"❌ API Error: {e}")
            
    return None

# --- 4. THE SENTINEL (SAFETY RAIL) ---
def sentinel_check(code, task):
    log("🛡️ Sentinel is scanning code for ReferenceErrors...")
    
    prompt = f"""
    ROLE: You are a Javascript Compiler.
    TASK: Scan this React code for CRITICAL CRASHES.
    
    LOOK FOR:
    1. Variables used in JSX (like 'toast', 'showModal') that are NOT defined in the component.
    2. Syntax Errors (unclosed brackets).
    
    CODE:
    {code[:15000]}... [truncated]
    
    OUTPUT:
    - If Safe: "PASS"
    - If Unsafe: "FAIL: [Reason]"
    """
    
    # We force the smartest model (1.5 Pro) for this check
    response = call_gemini([SENTINEL_MODEL], prompt, temp=0.0, role="sentinel")
    
    if response and "PASS" in response:
        return True, "Safe"
    return False, response or "No response"

# --- 5. SURGICAL PATCHING ---
def apply_patch(original, patch):
    pattern = r"<<<<<<< SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, patch, re.DOTALL)
    if not matches: return None, "No blocks found."
    
    new_code = original
    for search, replace in matches:
        if search in new_code:
            new_code = new_code.replace(search, replace)
        elif search.strip() in new_code:
            new_code = new_code.replace(search.strip(), replace.strip())
        else:
            # Fuzzy fallback could go here, but keeping it strict for safety first
            return None, "Search block match failed."
            
    if "<!DOCTYPE html>" not in new_code: return None, "CRITICAL: Root tag deleted."
    return new_code, "Applied"

# --- 6. RENDER WATCHDOG ---
def check_render():
    if not RENDER_API_KEY: 
        log("⚠️ No Render Key. Skipping Check.")
        return
    
    log("🚀 Watching Render Deployment...")
    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys?limit=1"
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    
    for _ in range(20): # 5 mins max
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                status = resp.json()[0]['deploy']['status']
                log(f"📡 Status: {status}")
                if status == "live": 
                    log("✅ Deployment Live.")
                    return
                if status in ["build_failed", "canceled"]:
                    log("❌ Deployment FAILED on Render.")
                    return
        except: pass
        time.sleep(15)

# --- MAIN LOOP ---
def process_task():
    backlog = read_file("BACKLOG.md")
    match = re.search(r'- \[ \] \*\*(.*?)\*\*', backlog)
    if not match: return False
    task = match.group(1)
    
    log(f"\n📋 TARGET: {task}")
    code = read_file("index.html")
    history = ""
    
    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Attempt {attempt+1}/{MAX_QA_RETRIES}...")
        
        # 1. CODER
        prompt = f"TASK: {task}\nCONTEXT: {read_file('AGENTS.md')}\nPREVIOUS_ERRORS: {history}\nCODE: {code}\nReturn SEARCH/REPLACE blocks."
        patch = call_gemini(CODER_MODELS, prompt, role="coder")
        if not patch: continue
        
        # 2. PATCH
        new_code, status = apply_patch(code, patch)
        if not new_code:
            log(f"❌ Patch Failed: {status}")
            history = status
            continue
            
        # 3. SENTINEL
        is_safe, msg = sentinel_check(new_code, task)
        if not is_safe:
            log(f"🚫 SENTINEL BLOCKED: {msg}")
            history = f"Sentinel Compiler Error: {msg}"
            continue
            
        # 4. CRITIC
        critic_prompt = f"TASK: {task}\nReview this code change. Reply PASS or FAIL.\n\n{patch}"
        review = call_gemini(CRITIC_MODELS, critic_prompt, role="critic")
        if not review or "FAIL" in review:
            log(f"❌ Critic Rejected: {review}")
            history = review
            continue
            
        # 5. DEPLOY
        log("✅ ALL CHECKS PASSED. Committing...")
        write_file("index.html", new_code)
        
        new_backlog = backlog.replace(f"- [ ] **{task}**", f"- [x] **{task}**")
        write_file("BACKLOG.md", new_backlog)
        
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        repo.index.commit(f"feat(jules): {task}")
        repo.remotes.origin.push()
        
        check_render()
        return True

    # Fail Logic
    log("⚠️ Task stuck. Skipping.")
    new_backlog = backlog.replace(f"- [ ] **{task}**", f"- [ ] **{task}** (SKIPPED)")
    write_file("BACKLOG.md", new_backlog)
    repo = git.Repo(REPO_PATH)
    repo.git.add("BACKLOG.md")
    repo.index.commit("skip: stuck task")
    repo.remotes.origin.push()
    return True

if __name__ == "__main__":
    while process_task():
        time.sleep(5)
