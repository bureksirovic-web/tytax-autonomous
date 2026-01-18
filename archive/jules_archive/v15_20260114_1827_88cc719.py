import os
import re
import git
import requests
import json
import time
import sys

# --- CONFIGURATION ---
REPO_PATH = "."
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
RENDER_SERVICE_ID = "srv-d5jlon15pdvs739hp3jg"

MAX_RUNTIME_MINUTES = 45
START_TIME = time.time()

def log(message):
    print(message, flush=True)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing!")

# 🎯 THE HIERARCHY
# 1. Try the Best (Gemini 3).
# 2. If jammed, try the Fast Genius (Gemini 2.0).
# 3. No Gemini 1.5.
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
    content = read_file("BACKLOG.md")
    match = re.search(r'- \[ \] \*\*(.*?)\*\*', content)
    return match.group(1).strip() if match else None

def mark_task_done(task_name):
    content = read_file("BACKLOG.md")
    updated = content.replace(f"- [ ] **{task_name}**", f"- [x] **{task_name}**")
    write_file("BACKLOG.md", updated)

def ask_gemini_smart_fallback(prompt):
    headers = {'Content-Type': 'application/json'}
    # Surgical Max Tokens
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192} 
    }
    
    for model in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        
        # Give each model 3 chances (approx 30s of effort)
        # If it's truly jammed, move to the next smart one.
        for attempt in range(3):
            try:
                log(f"🔄 Connecting to {model} (Attempt {attempt+1}/3)...")
                resp = requests.post(url, headers=headers, data=json.dumps(data))
                
                if resp.status_code == 200:
                    log(f"✅ Success! {model} answered.")
                    return resp.json()['candidates'][0]['content']['parts'][0]['text']
                
                elif resp.status_code == 429:
                    log(f"⚠️ {model} Busy. Waiting 5s...")
                    time.sleep(5)
                elif resp.status_code == 404:
                    log(f"❌ {model} Not Found. Skipping.")
                    break
                else:
                    log(f"⚠️ Status {resp.status_code}. Retrying...")
                    time.sleep(2)
            except Exception as e:
                log(f"❌ Network Error: {e}")
                time.sleep(2)
        
        log(f"⏭️ {model} timed out. Falling back to next best model...")
                
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
        else:
            clean_search = search_block.strip()
            if clean_search in new_code:
                new_code = new_code.replace(clean_search, replace_block.strip())
                success_count += 1
            else:
                return None, f"Could not find code block:\n{search_block[:50]}..."
                
    return new_code, f"Applied {success_count} patches."

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
                latest_deploy = data[0]['deploy']
                status = latest_deploy['status']
                log(f"📡 Status: {status}")
                if status == "live": return True
                if status in ["build_failed", "canceled"]: return False
        except: pass
        time.sleep(15)
    return True

def process_single_task():
    task = get_next_task()
    if not task: return False

    log(f"\n📋 SURGICAL TASK: {task}")
    current_code = read_file("index.html")
    
    prompt = f"""
    CONTEXT: You are an expert engineer.
    TASK: {task}
    TARGET FILE: index.html
    
    INSTRUCTIONS:
    1. Find the exact code to fix.
    2. Output a SEARCH/REPLACE block.
    
    FORMAT:
    <<<<<<< SEARCH
    (Exact existing code)
    =======
    (New code)
    >>>>>>> REPLACE
    
    CURRENT CODE:
    {current_code}
    """
    
    log(f"💡 Asking Smart Models (3.0 -> 2.0)...")
    response = ask_gemini_smart_fallback(prompt)
    if not response: 
        log("❌ Failed to get response from any High-IQ model.")
        return True

    log("💉 Applying Patch...")
    new_code, message = apply_patch(current_code, response)
    
    if not new_code:
        log(f"❌ Patch Failed: {message}")
        return True

    if len(new_code) < len(current_code) * 0.9:
        log("❌ Safety: File shrank too much.")
        return True

    log("💾 Saving Patched index.html...")
    write_file("index.html", new_code)
    
    repo = git.Repo(REPO_PATH)
    repo.git.add(all=True)
    repo.index.commit(f"feat(jules): {task}")
    mark_task_done(task)
    repo.git.add("BACKLOG.md")
    repo.index.commit(f"docs: marked {task} as done")
    repo.remotes.origin.push()

    if wait_for_render_deploy():
        log("🎉 Deploy Success!")
    else:
        log("🚨 Deploy Failed! Reverting...")
        repo.git.revert("HEAD", no_edit=True)
        repo.remotes.origin.push()
        
    return True

def run_loop():
    log("🤖 Jules (SMART FALLBACK) Started...")
    while True:
        if (time.time() - START_TIME) / 60 > (MAX_RUNTIME_MINUTES - 5): break
        if not process_single_task(): break
        time.sleep(5)

if __name__ == "__main__":
    run_loop()
