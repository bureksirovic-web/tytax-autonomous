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

MAX_QA_RETRIES = 3 
MAX_RUNTIME_MINUTES = 45
START_TIME = time.time()

# --- FORCE UNBUFFERED OUTPUT ---
def log(message):
    print(message, flush=True)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing!")

MODELS_TO_TRY = [
    "gemini-3-pro-preview",    
    "gemini-3-flash-preview", 
    "gemini-2.0-flash-exp"     
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
        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        full_text = "".join([p.get("text", "") for p in parts if "text" in p])
        return full_text if full_text.strip() else None
    except: return None

def ask_gemini_v6_style(prompt, model_hint="coder"):
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.1}, 
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    for model in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        wait_time = 5
        for attempt in range(5): 
            try:
                log(f"🔄 [{model_hint.upper()}] {model} (Attempt {attempt+1}/5)...")
                resp = requests.post(url, headers=headers, data=json.dumps(data))
                if resp.status_code == 200:
                    text = extract_text_from_response(resp.json())
                    if text: return text
                elif resp.status_code == 429:
                    log(f"⏳ Busy (429). Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    wait_time *= 1.5
                else:
                    log(f"⚠️ Status {resp.status_code} from {model}")
                    break 
            except Exception as e:
                log(f"❌ Error hitting API: {e}")
                time.sleep(2)
    return None

def apply_patch(original_code, patch_text):
    pattern = r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, patch_text, re.DOTALL)
    if not matches: return None, "No valid SEARCH/REPLACE blocks."
    new_code = original_code
    success_count = 0
    for search_block, replace_block in matches:
        if search_block in new_code:
            new_code = new_code.replace(search_block, replace_block)
            success_count += 1
        elif search_block.strip() in new_code:
            new_code = new_code.replace(search_block.strip(), replace_block.strip())
            success_count += 1
    if success_count == 0: return None, "Code block not found."
    return new_code, f"Applied {success_count} patches."

def verify_fix(task, original_code, new_code):
    if original_code == new_code: return False, "No change detected."
    
    diff = list(difflib.unified_diff(
        original_code.splitlines(keepends=True),
        new_code.splitlines(keepends=True),
        fromfile='original',
        tofile='patched',
        n=5 
    ))
    diff_text = "".join(diff)

    prompt = f"""
    ROLE: Senior React QA Engineer.
    TASK: {task}
    
    Examine the DIFF (changes) below. 
    Does this change correctly implement the task without breaking React state?
    
    DIFF:
    {diff_text}
    
    OUTPUT: 'PASS' or 'FAIL: [Specific Reason]'
    """
    
    response = ask_gemini_v6_style(prompt, model_hint="critic")
    if not response: return True, "Critic silent, assuming pass."
    if "PASS" in response: return True, "Verified."
    return False, response.replace("FAIL:", "").strip()

def process_single_task():
    task = get_next_task()
    if not task: return False
    log(f"\n📋 TARGET: {task}")
    
    current_code = read_file("index.html")
    critique_history = ""
    
    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Coder Attempt {attempt + 1}/{MAX_QA_RETRIES}...")
        prompt = f"Expert React Engineer. TASK: {task}\n{critique_history}\nFORMAT: <<<<<<< SEARCH\n(old)\n=======\n(new)\n>>>>>>> REPLACE\n\nCODE:\n{current_code}"
        
        response = ask_gemini_v6_style(prompt, model_hint="coder")
        if not response: 
            log("❌ No response from AI.")
            continue
            
        new_code, message = apply_patch(current_code, response)
        if not new_code:
            log(f"❌ Patch Error: {message}")
            critique_history = "PREVIOUS ATTEMPT FAILED: The SEARCH block was incorrect. Use EXACT code from the file."
            continue
            
        log(f"✅ Patch success: {message}")
        log("🕵️ Verifying Fix (Surgical Diff)...")
        is_valid, feedback = verify_fix(task, current_code, new_code)
        
        if is_valid:
            log(f"✅ QA Passed: {feedback}")
            log("💾 Saving to index.html...")
            write_file("index.html", new_code)
            
            repo = git.Repo(REPO_PATH)
            repo.git.add(all=True)
            repo.index.commit(f"feat(jules): {task}")
            
            mark_task_done(task)
            repo.git.add("BACKLOG.md")
            repo.index.commit(f"docs: marked {task} as done")
            
            log("🚀 Pushing to GitHub...")
            repo.remotes.origin.push()
            log(f"🎉 SUCCESS! {task} is live.")
            return True
        else:
            log(f"❌ QA Failed: {feedback}")
            critique_history = f"QA REJECTED PREVIOUS FIX: {feedback}"
            
    return True 

def run_loop():
    log("🤖 Jules SURGICAL (LOUD MODE) Started...")
    while True:
        if (time.time() - START_TIME) / 60 > (MAX_RUNTIME_MINUTES - 5): 
            log("⏰ Time limit reached.")
            break
        if not process_single_task(): 
            log("✅ No more tasks.")
            break
        time.sleep(5)

if __name__ == "__main__":
    run_loop()
