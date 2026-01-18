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

MAX_QA_RETRIES = 3 
MAX_RUNTIME_MINUTES = 45
START_TIME = time.time()

def log(message):
    print(message, flush=True)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing!")

# HIERARCHY: Try 3.0 Pro first (Reasoning), fallback to 2.0 Flash (Speed)
MODELS_TO_TRY = [
    "gemini-3-pro-preview",   # Primary: Advanced Reasoning
    "gemini-2.0-flash-exp"    # Fallback: Fast & Reliable
]

def read_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f: return f.read()
    except FileNotFoundError:
        return ""

def write_file(filename, content):
    with open(filename, 'w', encoding='utf-8') as f: f.write(content)

# --- SYSTEM CONTEXT LOADER (RAG) ---
def get_system_context():
    """Reads architectural rules to enforce the Jules persona."""
    context_buffer = ""
    # Critical documentation files
    doc_files = ["AGENTS.md", "ARCHITECTURE.md", "TESTING_PROTOCOL.md"]
    
    for doc in doc_files:
        content = read_file(doc)
        if content:
            context_buffer += f"\n\n=== SYSTEM CONTEXT: {doc} ===\n{content}\n"
            log(f"🧠 Loaded context from {doc}")
    
    if not context_buffer:
        log("⚠️ No system documentation found. Jules is using raw logic.")
    
    return context_buffer

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

def mark_task_failed(task_name, reason):
    log(f"⚠️ Moving failed task to bottom: {task_name}")
    content = read_file("BACKLOG.md")
    task_line = f"- [ ] **{task_name}**"
    if task_line in content:
        content = content.replace(task_line, "").strip()
        footer = f"\n\n- [ ] **{task_name}** (Retry: {reason})"
        write_file("BACKLOG.md", content + footer)

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
                
                # --- ROBUST LOGGING ---
                if resp.status_code == 200:
                    text = extract_text_from_response(resp.json())
                    if text: 
                        log(f"📥 [200 OK] Response received: {len(text)} chars")
                        return text
                elif resp.status_code == 429:
                    log(f"⏳ [429 Rate Limit] Waiting 10s...")
                    time.sleep(10)
                else:
                    log(f"❌ [API Error {resp.status_code}] {resp.text[:200]}...")
            except Exception as e:
                log(f"❌ [Exception]: {e}")
    return None

def apply_patch(original_code, patch_text):
    pattern = r"<<<<<<< SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, patch_text, re.DOTALL)
    if not matches: return None, "No valid SEARCH/REPLACE blocks found."

    new_code = original_code
    success_count = 0
    for search_block, replace_block in matches:
        if search_block in new_code:
            new_code = new_code.replace(search_block, replace_block)
            success_count += 1
            log("✅ Found exact match.")
        elif search_block.strip() in new_code:
            new_code = new_code.replace(search_block.strip(), replace_block.strip())
            success_count += 1
            log("✅ Found whitespace-stripped match.")
            
    if success_count == 0: return None, "No blocks matched."
    return new_code, f"Applied {success_count} patches."

def verify_fix(task, original_code, new_code, context):
    if original_code == new_code: return False, "No changes detected."
    diff = "".join(difflib.unified_diff(original_code.splitlines(True), new_code.splitlines(True), n=3))
    
    # Inject System Context into Critic as well
    prompt = f"{context}\n\nROLE: You are the Critic defined in AGENTS.md.\nTASK: {task}\nDIFF:\n{diff}\n\nDoes this fix the task without breaking React state immutability or the Index.html structure? Respond 'PASS' or 'FAIL: [reason]'"
    response = ask_gemini_robust(prompt, model_hint="critic")
    return ("PASS" in (response or "").upper()), response

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
    
    # 1. Load System Context (RAG)
    system_context = get_system_context()
    current_code = read_file("index.html")
    critique_history = ""
    last_error = "Unknown"

    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Coder Attempt {attempt + 1}/{MAX_QA_RETRIES}...")
        
        # 2. Inject Context into Prompt
        prompt = f"""
{system_context}

---
CURRENT MISSION:
You are acting as the Agent 'Jules'. 
Your goal is to implement the following task in 'index.html' while strictly adhering to the architectural rules above.

TASK: {task}
CRITIQUE HISTORY: {critique_history}

RESPONSE FORMAT:
Strictly use the SEARCH/REPLACE block format defined in ARCHITECTURE.md (if applicable) or standard Git conflict markers:
<<<<<<< SEARCH
(exact code to remove)
=======
(new code to insert)
>>>>>>> REPLACE

CODE CONTEXT:
{current_code}
"""
        response = ask_gemini_robust(prompt)
        if not response: continue
        
        new_code, message = apply_patch(current_code, response)
        if not new_code:
            log(f"❌ Patch failed: {message}")
            last_error = message
            critique_history = f"PREVIOUS FAIL: {message}. Ensure SEARCH block matches exact whitespace."
            continue

        log("🕵️ Verifying Logic...")
        # 3. Pass Context to Critic
        is_valid, feedback = verify_fix(task, current_code, new_code, system_context)
        if is_valid:
            log("✅ QA Passed. Saving...")
            write_file("index.html", new_code)
            
            repo = git.Repo(REPO_PATH)
            repo.git.add(all=True)
            repo.index.commit(f"feat(jules): {task}")
            mark_task_done(task)
            repo.git.add("BACKLOG.md")
            repo.index.commit(f"docs: marked {task} as done")
            
            # --- AGGRESSIVE SYNC ---
            try:
                log("🔄 Pulling latest changes before push...")
                repo.remotes.origin.pull(rebase=True)
                repo.remotes.origin.push()
                log("🚀 Pushed to GitHub.")
            except Exception as e:
                log(f"⚠️ Push failed: {e}")
                return False
            
            wait_for_render_deploy()
            return True
        else:
            log(f"❌ QA Failed: {feedback}")
            last_error = feedback
            critique_history = f"QA REJECTED: {feedback}"
            
    # Fail-Forward
    mark_task_failed(task, last_error)
    repo = git.Repo(REPO_PATH)
    repo.git.add("BACKLOG.md")
    repo.index.commit(f"fix: skip stuck task {task}")
    repo.remotes.origin.push()
    return True

def run_loop():
    log("🤖 Jules Level 11 (HYBRID MASTER) Started...")
    while True:
        if (time.time() - START_TIME) / 60 > (MAX_RUNTIME_MINUTES - 5): break
        if not process_single_task(): 
            log("✅ No more tasks or sync error.")
            break
        time.sleep(10)

if __name__ == "__main__":
    run_loop()
