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

MAX_RUNTIME_MINUTES = 45
START_TIME = time.time()

def log(message):
    print(message, flush=True)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing!")

# 🎯 MODEL HIERARCHY (Priority Order)
# Fallback strategy: Try Best -> Fast -> Legacy
MODELS_TO_TRY = [
    "gemini-3-pro-preview",
    "gemini-3-flash-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-001",       # Legacy (Retires March 2026)
    "gemini-2.0-flash-lite-001"   # Legacy (Retires March 2026)
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
    except FileNotFoundError:
        return None

def mark_task_done(task_name):
    content = read_file("BACKLOG.md")
    updated = content.replace(f"- [ ] **{task_name}**", f"- [x] **{task_name}**")
    write_file("BACKLOG.md", updated)

# 1) ROBUSTNO VAĐENJE TEKSTA
def extract_text_from_response(response_json):
    """
    Safely extracts text from the deep JSON structure.
    Returns None if structure is missing or empty, avoiding KeyErrors.
    """
    try:
        if not response_json: return None
        candidates = response_json.get("candidates", [])
        if not candidates: return None
        
        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        
        # Combine all text parts (ignoring non-text parts if any)
        full_text = "".join([p.get("text", "") for p in parts if "text" in p])
        
        return full_text if full_text.strip() else None
    except Exception as e:
        log(f"⚠️ Extraction Logic Error: {e}")
        return None

# 2, 3, 4) ROBUST REQUEST & FALLBACK LOGIC
def ask_gemini_robust(prompt):
    url_base = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {'Content-Type': 'application/json'}
    
    # Disable Safety Filters to minimize "False Success" (200 OK but blocked content)
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192},
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    for model in MODELS_TO_TRY:
        url = url_base.format(model=model)
        full_url = f"{url}?key={GEMINI_API_KEY}"
        
        # Retry loop for a single model
        max_retries_per_model = 3
        base_delay = 5 # seconds
        
        for attempt in range(max_retries_per_model):
            try:
                log(f"🔄 Connecting to {model} (Attempt {attempt+1}/{max_retries_per_model})...")
                resp = requests.post(full_url, headers=headers, data=json.dumps(data))
                
                # --- CASE: HTTP 200 (Success... or is it?) ---
                if resp.status_code == 200:
                    try:
                        resp_json = resp.json()
                        text = extract_text_from_response(resp_json)
                        
                        if text:
                            log(f"✅ Success! {model} answered.")
                            return text
                        else:
                            # 2) DETEKCIJA LAŽNOG SUCCESSA
                            finish_reason = resp_json.get("candidates", [{}])[0].get("finishReason", "UNKNOWN")
                            log(f"⚠️ Warning: 200 OK but NO CONTENT from {model}. Reason: {finish_reason}")
                            
                            # Dump JSON for debugging
                            with open("last_gemini_debug.json", "w", encoding="utf-8") as f:
                                json.dump(resp_json, f, indent=2)
                            log("💾 Saved debug info to last_gemini_debug.json")
                            
                            # Treat as a failure, trigger retry
                            time.sleep(2) 
                            continue

                    except json.JSONDecodeError:
                        log(f"❌ Parse Error: Invalid JSON from {model}. Raw: {resp.text[:100]}")
                        continue

                # --- CASE: RATE LIMIT (429) ---
                elif resp.status_code == 429:
                    # 4) PAMETNI BACKOFF
                    retry_after = int(resp.headers.get("Retry-After", 0))
                    # Exponential backoff + Jitter
                    sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0, 3)
                    wait_time = max(retry_after, sleep_time)
                    
                    log(f"⏳ {model} Rate Limited (429). Cooling down for {wait_time:.1f}s...")
                    time.sleep(wait_time)
                
                # --- CASE: OVERLOADED (503) ---
                elif resp.status_code == 503:
                    log(f"⚠️ {model} Overloaded (503). Waiting 20s...")
                    time.sleep(20)
                
                # --- CASE: CLIENT ERRORS (400, 404, 403) ---
                elif 400 <= resp.status_code < 500:
                    log(f"❌ Client Error {resp.status_code} from {model}: {resp.text}")
                    break # Don't retry client errors (wrong model name, invalid key), move to next model
                
                # --- CASE: SERVER ERRORS (500, 502, 504) ---
                else:
                    log(f"⚠️ Server Error {resp.status_code} from {model}. Retrying...")
                    time.sleep(5)

            except Exception as e:
                log(f"❌ Network/API Error: {e}")
                time.sleep(5)
        
        log(f"⏭️ {model} exhausted retries. Falling back to next model in list...")

    log("❌ All models failed to generate code.")
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
    
    log(f"💡 Asking Gemini (Smart Fallback Mode)...")
    response = ask_gemini_robust(prompt)
    if not response: 
        log("❌ Failed to get response from any model.")
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
    
    try:
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        repo.index.commit(f"feat(jules): {task}")
        mark_task_done(task)
        repo.git.add("BACKLOG.md")
        repo.index.commit(f"docs: marked {task} as done")
        repo.remotes.origin.push()
        log("🚀 Pushed to GitHub.")
    except Exception as e:
        log(f"❌ Git Error: {e}")
        return True

    if wait_for_render_deploy():
        log("🎉 Deploy Success!")
    else:
        log("🚨 Deploy Failed! Reverting...")
        try:
            repo.git.revert("HEAD", no_edit=True)
            repo.remotes.origin.push()
        except: pass
        
    return True

def run_loop():
    log("🤖 Jules (ROBUST V6) Started...")
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
