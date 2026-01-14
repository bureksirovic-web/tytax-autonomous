import os
import re
import git
import requests
import json
import time
import sys
import random

# --- CONFIGURATION ---
REPO_PATH = "."
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
RENDER_SERVICE_ID = "srv-d5jlon15pdvs739hp3jg"

# Max retries for "Self-Correction" (The Critic Loop)
MAX_QA_RETRIES = 3 
MAX_RUNTIME_MINUTES = 45
START_TIME = time.time()

def log(message):
    print(message, flush=True)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing!")

# 🎯 MODEL HIERARCHY (RESTORED GEMINI 3)
# We need Gemini 3's reasoning to get the PATCH format right.
MODELS_TO_TRY = [
    "gemini-3-pro-preview",    # 1. The Mastermind (Best at coding)
    "gemini-3-flash-preview",  # 2. The Fast Mastermind
    "gemini-2.0-flash-exp",    # 3. The Fallback
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
    except FileNotFoundError: return None

def mark_task_done(task_name):
    content = read_file("BACKLOG.md")
    updated = content.replace(f"- [ ] **{task_name}**", f"- [x] **{task_name}**")
    write_file("BACKLOG.md", updated)

def extract_text_from_response(response_json):
    try:
        if not response_json: return None
        candidates = response_json.get("candidates", [])
        if not candidates: return None
        parts = candidates[0].get("content", {}).get("parts", [])
        full_text = "".join([p.get("text", "") for p in parts if "text" in p])
        return full_text if full_text.strip() else None
    except: return None

def ask_gemini_robust(prompt, model_hint="coder"):
    url_base = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.2}, 
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    for model in MODELS_TO_TRY:
        url = url_base.format(model=model) + f"?key={GEMINI_API_KEY}"
        # Only try once per model to avoid wasting time on broken models
        try:
            log(f"🔄 [{model_hint.upper()}] Connecting to {model}...")
            resp = requests.post(url, headers=headers, data=json.dumps(data))
            
            if resp.status_code == 200:
                text = extract_text_from_response(resp.json())
                if text: return text
                else: log(f"⚠️ {model} returned empty content.")
            elif resp.status_code == 429:
                log(f"⏳ {model} Rate Limited. Switching...")
                time.sleep(2)
            else:
                log(f"❌ {model} Error {resp.status_code}.")
        except Exception as e:
            log(f"❌ Network Error: {e}")
            time.sleep(1)
            
    return None

def apply_patch(original_code, patch_text):
    pattern = r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, patch_text, re.DOTALL)
    
    if not matches:
        return None, "No valid SEARCH/REPLACE blocks found."

    new_code = original_code
    success_count = 0
    
    for search_block, replace_block in matches:
        if search_block in new_code:
            new_code = new_code.replace(search_block, replace_block)
            success_count += 1
            continue
        
        # Loose match
        if search_block.strip() in new_code:
            new_code = new_code.replace(search_block.strip(), replace_block.strip())
            success_count += 1
            continue
    
    if success_count == 0:
        return None, "Could not find any code blocks to replace."
        
    return new_code, f"Applied {success_count} patches."

def verify_fix(task, original_code, new_code):
    if original_code == new_code:
        return False, "The code did not change at all."

    prompt = f"""
    ROLE: You are a Senior Code Reviewer.
    TASK: {task}
    
    I have applied a patch to the file. 
    Analyze the NEW CODE below.
    
    CHECKLIST:
    1. Did the specific logic requested in the TASK actually change?
    2. Are there any obvious React errors?
    
    NEW CODE SNAPSHOT (relevant parts):
    {new_code[:10000]} 
    ... (truncated) ...
    {new_code[-5000:]}
    
    OUTPUT FORMAT:
    If the fix looks correct:
    PASS
    
    If the fix is broken:
    FAIL: [Reason]
    """
    
    response = ask_gemini_robust(prompt, model_hint="critic")
    if not response: return True, "Critic failed to respond."
    
    if "PASS" in response: return True, "Verified."
    else: return False, response.replace("FAIL:", "").strip()

def wait_for_render_deploy():
    if not RENDER_API_KEY: return True
    log("🚀 Monitoring Render Deployment...")
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys?limit=1"
    
    time.sleep(10)
    for _ in range(20):
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if not data: continue 
                status = data[0]['deploy']['status']
                log(f"📡 Status: {status}")
                if status == "live": return True
                if status in ["build_failed", "canceled"]: return False
        except: pass
        time.sleep(15)
    return True

def process_single_task():
    task = get_next_task()
    if not task: return False

    log(f"\n📋 STARTING TASK: {task}")
    current_code = read_file("index.html")
    
    critique_history = ""
    
    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Attempt {attempt + 1}/{MAX_QA_RETRIES}...")
        
        prompt = f"""
        CONTEXT: Expert React Engineer.
        TASK: {task}
        TARGET FILE: index.html
        
        {critique_history}
        
        INSTRUCTIONS:
        1. Find the exact code to fix.
        2. Output a SEARCH/REPLACE block.
        3. Make sure the SEARCH block matches EXACTLY.
        
        FORMAT:
        <<<<<<< SEARCH
        (Exact existing code)
        =======
        (New code)
        >>>>>>> REPLACE
        
        CURRENT CODE:
        {current_code}
        """
        
        response = ask_gemini_robust(prompt, model_hint="coder")
        if not response: continue

        log("💉 Applying Patch...")
        new_code, message = apply_patch(current_code, response)
        
        if not new_code:
            log(f"❌ Patch Failed: {message}")
            critique_history = f"PREVIOUS ATTEMPT FAILED: The SEARCH block didn't match. Be precise."
            continue

        log("🕵️ Running QA Verification...")
        is_valid, feedback = verify_fix(task, current_code, new_code)
        
        if is_valid:
            log(f"✅ QA Passed: {feedback}")
            write_file("index.html", new_code)
            try:
                repo = git.Repo(REPO_PATH)
                repo.git.add(all=True)
                repo.index.commit(f"feat(jules): {task}")
                mark_task_done(task)
                repo.git.add("BACKLOG.md")
                repo.index.commit(f"docs: marked {task} as done")
                repo.remotes.origin.push()
                log("🚀 Pushed to GitHub.")
                if wait_for_render_deploy(): log("🎉 Deploy Success!")
            except Exception as e:
                log(f"❌ Git Error: {e}")
            return True
        else:
            log(f"❌ QA Failed: {feedback}")
            critique_history = f"QA REJECTED: {feedback}"

    log("❌ Task Failed after max retries.")
    return True 

def run_loop():
    log("🤖 Jules Level 8 (GEMINI 3 RETURN) Started...")
    while True:
        if (time.time() - START_TIME) / 60 > (MAX_RUNTIME_MINUTES - 5): break
        if not process_single_task(): break
        time.sleep(5)

if __name__ == "__main__":
    run_loop()
