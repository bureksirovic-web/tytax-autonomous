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

# INCREASED RETRIES: We have more models, so we can try more times.
MAX_QA_RETRIES = 4 
MAX_RUNTIME_MINUTES = 60
START_TIME = time.time()

def log(message):
    print(message, flush=True)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing!")

# --- THE NEW MULTI-LANE BRAIN ---
# Lane 1: The Architect (Complex Logic)
# Lane 2: The Engineer (Fast Coding)
# Lane 3: The Critic (Review Only)

CODER_MODELS = [
    "gemini-3-pro-preview",    # 1. Primary Genius
    "gemini-3-flash",          # 2. Smart & Fast (New 3.0 Model)
    "gemini-2.5-flash",        # 3. Backup Workhorse
    "gemini-2.0-flash"         # 4. Last Resort
]

CRITIC_MODELS = [
    "gemini-2.5-pro",          # 1. The Expert Reviewer (Unused Quota)
    "gemini-2.0-flash"         # 2. Fast Check
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
    context_buffer = ""
    doc_files = ["AGENTS.md", "ARCHITECTURE.md", "TESTING_PROTOCOL.md"]
    for doc in doc_files:
        content = read_file(doc)
        if content:
            context_buffer += f"\n\n=== SYSTEM CONTEXT: {doc} ===\n{content}\n"
            log(f"🧠 Loaded context from {doc}")
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

def ask_gemini_robust(prompt, role="coder"):
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.1},
    }
    
    # INTELLIGENT ROUTING: Pick the right list based on the job
    models_to_use = CRITIC_MODELS if role == "critic" else CODER_MODELS
    
    for model in models_to_use:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        # Only try each model twice to fail-over quickly
        for attempt in range(2): 
            try:
                log(f"🔄 [{role.upper()}] {model} (Attempt {attempt+1})...")
                resp = requests.post(url, headers=headers, data=json.dumps(data))
                
                if resp.status_code == 200:
                    text = extract_text_from_response(resp.json())
                    if text: 
                        log(f"📥 [200 OK] Response received: {len(text)} chars")
                        return text
                elif resp.status_code == 429:
                    log(f"⏳ [429 Rate Limit] Switching to next model...")
                    time.sleep(2) 
                    break # Break inner loop -> Go to next model in list
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
    
    prompt = f"{context}\n\nROLE: You are the Critic defined in AGENTS.md.\nTASK: {task}\nDIFF:\n{diff}\n\nDoes this fix the task without breaking React state immutability or the Index.html structure? Respond 'PASS' or 'FAIL: [reason]'"
    # ROUTING: Explicitly ask the 'critic' models
    response = ask_gemini_robust(prompt, role="critic")
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
    
    system_context = get_system_context()
    current_code = read_file("index.html")
    critique_history = ""
    last_error = "Unknown"

    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Coder Attempt {attempt + 1}/{MAX_QA_RETRIES}...")
        
        prompt = f"""
{system_context}

---
CURRENT MISSION:
You are acting as the Agent 'Jules'. 
Your goal is to implement the following task in 'index.html' while strictly adhering to the architectural rules above.

TASK: {task}
CRITIQUE HISTORY: {critique_history}

RESPONSE FORMAT:
Strictly use the SEARCH/REPLACE block format defined in ARCHITECTURE.md.
<<<<<<< SEARCH
(exact code to remove)
=======
(new code to insert)
>>>>>>> REPLACE

CODE CONTEXT:
{current_code}
"""
        # ROUTING: Explicitly ask the 'coder' models
        response = ask_gemini_robust(prompt, role="coder")
        if not response: continue
        
        new_code, message = apply_patch(current_code, response)
        if not new_code:
            log(f"❌ Patch failed: {message}")
            last_error = message
            critique_history = f"PREVIOUS FAIL: {message}. Ensure SEARCH block matches exact whitespace."
            continue

        log("🕵️ Verifying Logic...")
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
            
    mark_task_failed(task, last_error)
    repo = git.Repo(REPO_PATH)
    repo.git.add("BACKLOG.md")
    repo.index.commit(f"fix: skip stuck task {task}")
    repo.remotes.origin.push()
    return True

def run_loop():
    log("🤖 Jules Level 12 (MULTI-MODEL SWARM) Started...")
    while True:
        if (time.time() - START_TIME) / 60 > (MAX_RUNTIME_MINUTES - 5): break
        if not process_single_task(): 
            log("✅ No more tasks or sync error.")
            break
        time.sleep(5)

if __name__ == "__main__":
    run_loop()
