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
SITE_URL = "https://tytax-elite.onrender.com"

MAX_RUNTIME_MINUTES = 45
START_TIME = time.time()

# --- FORCE UNBUFFERED OUTPUT ---
def log(message):
    print(message, flush=True)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing!")
if not RENDER_API_KEY:
    log("⚠️ WARNING: RENDER_API_KEY is missing. Production checks will be skipped.")

# 🎯 SNIPER LIST: ONLY High-IQ Experimental Models. 
# We removed the "dumber" stable models.
MODELS_TO_TRY = [
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

def extract_code_block(response_text):
    match = re.search(r'```html(.*?)```', response_text, re.DOTALL)
    if match: return match.group(1).strip()
    return response_text if "<!DOCTYPE html>" in response_text else None

def ask_gemini_stubborn(prompt):
    """
    Siege Mode: Keeps hitting the High-IQ model until it answers.
    No downgrading to dumber models.
    """
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    model = "gemini-2.0-flash-exp"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

    wait_time = 5 # Start with 5 seconds wait
    max_retries = 10 # Try 10 times (approx 5 mins of fighting)

    for attempt in range(max_retries):
        try:
            log(f"🔄 Connecting to {model} (Attempt {attempt+1}/{max_retries})...")
            resp = requests.post(url, headers=headers, data=json.dumps(data))
            
            if resp.status_code == 200:
                log(f"✅ Success! {model} answered.")
                return resp.json()['candidates'][0]['content']['parts'][0]['text']
            
            elif resp.status_code == 429:
                log(f"⚠️ {model} is busy (Rate Limit). Waiting {wait_time}s...")
                time.sleep(wait_time)
                wait_time *= 1.5 # Exponential Backoff: Wait longer next time (5s -> 7.5s -> 11s...)
            elif resp.status_code == 503:
                log(f"⚠️ {model} Overloaded (503). Cooling down for 20s...")
                time.sleep(20)
            else:
                log(f"❌ Critical Error {resp.status_code}: {resp.text}")
                # Don't give up immediately on 500s, retry once or twice
                time.sleep(5)
                
        except Exception as e:
            log(f"❌ Connection Error: {e}")
            time.sleep(5)
            
    log("❌ Failed to get code after maximum retries.")
    return None

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
        except Exception as e:
            log(f"⚠️ Monitor Error: {e}")
        time.sleep(15)
    log("⏳ Monitor timed out (assuming success).")
    return True

def process_single_task():
    task = get_next_task()
    if not task: return False

    log(f"\n📋 STARTING TASK: {task}")
    
    current_code = read_file("index.html")
    agents_doc = read_file("AGENTS.md")
    
    prompt = f"{agents_doc}\nCURRENT CODE LENGTH: {len(current_code)}\nTASK: {task}\nOUTPUT: Full index.html only."
    
    log(f"💡 Asking Gemini 2.0 Flash Exp (Stubborn Mode)...")
    raw_response = ask_gemini_stubborn(prompt)
    if not raw_response: 
        log("❌ No response from AI.")
        return True

    new_code = extract_code_block(raw_response)
    if not new_code or len(new_code.splitlines()) < 2000:
        log("❌ Safety Check Failed: Code too short.")
        return True

    log("💾 Saving to index.html...")
    write_file("index.html", new_code)
    
    repo = git.Repo(REPO_PATH)
    repo.git.add(all=True)
    repo.index.commit(f"feat(jules): implemented {task}")
    mark_task_done(task)
    repo.git.add("BACKLOG.md")
    repo.index.commit(f"docs: marked {task} as done")
    
    log("🚀 Pushing to GitHub...")
    repo.remotes.origin.push()

    if wait_for_render_deploy():
        log("🎉 Deploy Success!")
    else:
        log("🚨 Deploy Failed! Reverting...")
        repo.git.revert("HEAD", no_edit=True)
        repo.remotes.origin.push()
        
    return True

def run_loop():
    log("🤖 Jules (HIGH-IQ ONLY) Started...")
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
