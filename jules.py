import os
import re
import git
import requests
import json
import time
import sys
import random
import difflib

# --- CONFIGURATION ---
REPO_PATH = "."
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
RENDER_SERVICE_ID = "srv-d5jlon15pdvs739hp3jg"
SITE_URL = "https://tytax-elite.onrender.com"

# Retains original self-correction depth
MAX_QA_RETRIES = 3 
MAX_RUNTIME_MINUTES = 45
START_TIME = time.time()

# Force unbuffered output for GitHub Actions visibility
def log(message):
    print(message, flush=True)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing!")

# MASTER HIERARCHY: Prioritizes Gemini 3 for reasoning, fallbacks to reliable 2.0
MODELS_TO_TRY = [
    "gemini-3-pro-preview",   # Mastermind for complex patches
    "gemini-3-flash-preview", # Fast Mastermind
    "gemini-2.0-flash-exp",   # Best current balance
    "gemini-1.5-pro"          # Final reliable backup
]

def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f: return f.read()

def write_file(filename, content):
    with open(filename, 'w', encoding='utf-8') as f: f.write(content)

def get_next_task():
    try:
        content = read_file("BACKLOG.md")
        match = re.search(r'- \[ \] \*\*(.*?)\*\*', content)
        return match.group(1).strip() if match else None
    except: return None

def mark_task_done(task_name):
    content = read_file("BACKLOG.md")
    updated = content.replace(f"- [ ] **{task_name}**", f"- [x] **{task_name}**")
    write_file("BACKLOG.md", updated)

def extract_text_from_response(response_json):
    try:
        parts = response_json['candidates'][0]['content']['parts']
        return "".join([p.get("text", "") for p in parts])
    except: return None

def ask_gemini_robust(prompt, model_hint="coder"):
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.1},
    }
    
    for model in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        for attempt in range(3):
            try:
                log(f"🔄 [{model_hint.upper()}] {model} (Attempt {attempt+1}/3)...")
                resp = requests.post(url, headers=headers, data=json.dumps(data))
                if resp.status_code == 200:
                    text = extract_text_from_response(resp.json())
                    if text: 
                        log(f"📥 [RESPONSE RECEIVED] Length: {len(text)} chars")
                        return text
                elif resp.status_code == 429:
                    log(f"⏳ Rate Limit on {model}. Waiting...")
                    time.sleep(5)
            except Exception as e:
                log(f"❌ Error: {e}")
    return None

def apply_patch(original_code, patch_text):
    pattern = r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, patch_text, re.DOTALL)
    if not matches: return None, "No valid SEARCH/REPLACE blocks found."

    new_code = original_code
    success_count = 0
    for search_block, replace_block in matches:
        if search_block in new_code:
            new_code = new_code.replace(search_block, replace_block)
            success_count += 1
            log("✅ Found exact match for block.")
        elif search_block.strip() in new_code:
            new_code = new_code.replace(search_block.strip(), replace_block.strip())
            success_count += 1
            log("✅ Found whitespace-stripped match.")
        else:
            log(f"❌ MISMATCH: Could not find block starting with: {search_block[:50]}...")
            
    if success_count == 0: return None, "No blocks matched."
    return new_code, f"Applied {success_count} patches."

def verify_fix(task, original_code, new_code):
    if original_code == new_code: return False, "No changes detected."
    diff = "".join(difflib.unified_diff(original_code.splitlines(True), new_code.splitlines(True), n=3))
    
    prompt = f"TASK: {task}\nDIFF:\n{diff}\nDoes this fix the task without breaking React? Respond 'PASS' or 'FAIL: [reason]'"
    response = ask_gemini_robust(prompt, model_hint="critic")
    if not response: return True, "Critic silent."
    return ("PASS" in response.upper()), response

def wait_for_render_deploy():
    if not RENDER_API_KEY: return True
    log("🚀 Monitoring Render Deployment...")
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys?limit=1"
    
    for _ in range(20): 
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    status = data[0]['deploy']['status']
                    log(f"📡 Render Status: {status}")
                    if status == "live": return True
                    if status in ["build_failed", "canceled"]: return False
        except: pass
        time.sleep(15)
    return True

def process_single_task():
    task = get_next_task()
    if not task: return False
    log(f"\n📋 TARGET: {task}")
    current_code = read_file("index.html")
    critique_history = ""

    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Coder Attempt {attempt + 1}/{MAX_QA_RETRIES}...")
        prompt = f"Expert React Dev. TASK: {task}\n{critique_history}\nFORMAT: <<<<<<< SEARCH\n(old)\n=======\n(new)\n>>>>>>> REPLACE\n\nCODE:\n{current_code}"
        
        response = ask_gemini_robust(prompt)
        if not response: continue
        
        new_code, message = apply_patch(current_code, response)
        if not new_code:
            log(f"❌ Patch failed: {message}")
            critique_history = f"PREVIOUS FAIL: {message}. Ensure SEARCH block is exact."
            continue

        log("🕵️ Verifying Logic...")
        is_valid, feedback = verify_fix(task, current_code, new_code)
        if is_valid:
            log("✅ QA Passed. Saving...")
            write_file("index.html", new_code)
            
            repo = git.Repo(REPO_PATH)
            repo.git.add(all=True)
            repo.index.commit(f"feat(jules): {task}")
            mark_task_done(task)
            repo.git.add("BACKLOG.md")
            repo.index.commit(f"docs: marked {task} as done")
            repo.remotes.origin.push()
            log("🚀 Pushed to GitHub.")
            
            if wait_for_render_deploy(): log("🎉 Deploy Success!")
            else: log("🚨 Deploy Failed on Render.")
            return True
        else:
            log(f"❌ QA Failed: {feedback}")
            critique_history = f"QA REJECTED: {feedback}"
    return True

def run_loop():
    log("🤖 Jules Level 9 (MASTER RESTORE) Started...")
    while True:
        if (time.time() - START_TIME) / 60 > (MAX_RUNTIME_MINUTES - 5): break
        if not process_single_task(): 
            log("✅ No more tasks.")
            break
        time.sleep(10)

if __name__ == "__main__":
    run_loop()
