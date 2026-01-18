import os
import re
import git
import requests
import json
import time
import html.parser

# --- CONFIGURATION ---
REPO_PATH = "."
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
RENDER_SERVICE_ID = "srv-d5jlon15pdvs739hp3jg" # Found from your screenshot
SITE_URL = "https://tytax-elite.onrender.com"

MAX_RUNTIME_MINUTES = 45
START_TIME = time.time()

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing!")
if not RENDER_API_KEY:
    print("⚠️ WARNING: RENDER_API_KEY is missing. Production checks will be skipped.")

MODELS_TO_TRY = ["gemini-2.0-flash-exp", "gemini-2.5-pro", "gemini-3-flash-preview"]

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

def ask_gemini(prompt):
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    for model in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            resp = requests.post(url, headers=headers, data=json.dumps(data))
            if resp.status_code == 200:
                return resp.json()['candidates'][0]['content']['parts'][0]['text']
        except: pass
    return None

def wait_for_render_deploy():
    """Polls Render API to verify deployment success."""
    if not RENDER_API_KEY: return True
    
    print("🚀 Monitoring Render Deployment...")
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys?limit=1"
    
    # Wait for the NEW deploy to start (it takes a few seconds after git push)
    time.sleep(10) 
    
    for _ in range(20): # Check for ~5 minutes
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200: 
                print(f"⚠️ Render API Error: {resp.status_code}")
                continue
                
            latest_deploy = resp.json()[0]['deploy']
            status = latest_deploy['status']
            commit_id = latest_deploy['commit']['id']
            
            print(f"📡 Deploy Status: {status} (Commit: {commit_id[:7]})")
            
            if status == "live":
                print("✅ Render says: Deployment LIVE.")
                return True
            if status in ["build_failed", "update_failed", "canceled"]:
                print(f"❌ Render says: Deployment FAILED ({status}).")
                return False
                
        except Exception as e:
            print(f"⚠️ Monitoring error: {e}")
            
        time.sleep(15)
        
    print("⏳ Timed out waiting for Render. Assuming success or manual check needed.")
    return True

def check_site_health():
    """Pings the live URL to ensure it's not a white screen."""
    try:
        print(f"💓 Pinging {SITE_URL}...")
        resp = requests.get(SITE_URL, timeout=10)
        if resp.status_code == 200:
            print("✅ Site is responding (HTTP 200).")
            return True
        else:
            print(f"❌ Site is DOWN (HTTP {resp.status_code}).")
            return False
    except Exception as e:
        print(f"❌ Site ping failed: {e}")
        return False

def emergency_revert(task_name):
    print("🚨 INITIATING EMERGENCY ROLLBACK 🚨")
    repo = git.Repo(REPO_PATH)
    # Revert the last commit to undo the damage
    repo.git.revert("HEAD", no_edit=True)
    repo.remotes.origin.push()
    print(f"✅ Rollback pushed. {task_name} has been undone to save the site.")

def process_single_task():
    task = get_next_task()
    if not task: return False

    print(f"\n📋 STARTING TASK: {task}")
    
    # Load Context
    agents_doc = read_file("AGENTS.md")
    arch_doc = read_file("ARCHITECTURE.md")
    current_code = read_file("index.html")
    original_lines = len(current_code.splitlines())

    # Generate
    prompt = f"{agents_doc}\nCONTEXT: {arch_doc}\nCURRENT CODE: {current_code}\nMISSION: Implement '{task}'\nRULES: Return FULL index.html."
    print("💡 Thinking...")
    raw_response = ask_gemini(prompt)
    if not raw_response: return True

    new_code = extract_code_block(raw_response)
    if not new_code or len(new_code.splitlines()) < (original_lines * 0.8):
        print("❌ Safety Check Failed (Code too short or invalid). Aborting.")
        return True

    # Save & Push
    print("💾 Saving and Pushing...")
    write_file("index.html", new_code)
    repo = git.Repo(REPO_PATH)
    repo.git.add(all=True)
    repo.index.commit(f"feat(jules): implemented {task}")
    mark_task_done(task) # Mark done locally, but we might undo this if it fails
    repo.git.add("BACKLOG.md")
    repo.index.commit(f"docs: marked {task} as done")
    repo.remotes.origin.push()

    # --- PRODUCTION VERIFICATION ---
    deploy_success = wait_for_render_deploy()
    
    if deploy_success:
        # Double check: Is the site actually reachable?
        health_success = check_site_health()
        if health_success:
            print(f"🎉 SUCCESS! {task} is live and healthy.")
        else:
            print("⚠️ Deploy passed but Site Health failed.")
            emergency_revert(task)
    else:
        print("❌ Deploy failed.")
        emergency_revert(task)
        
    return True

def run_loop():
    print("🤖 Jules Level 4 (Production Aware) Started...")
    while True:
        if (time.time() - START_TIME) / 60 > (MAX_RUNTIME_MINUTES - 5): break
        if not process_single_task(): break
        time.sleep(10)

if __name__ == "__main__":
    run_loop()
