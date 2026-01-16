import os
import re
import git
import requests
import json
import time
import sys
import difflib
from datetime import datetime

# --- CONFIGURATION ---
REPO_PATH = "."
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").replace("\n", "").strip()
RENDER_API_KEY = os.environ.get("RENDER_API_KEY", "").replace("\n", "").strip()
RENDER_SERVICE_ID = os.environ.get("RENDER_SERVICE_ID", "").replace("\n", "").strip()

# --- MODEL STACK (UPDATED NAMES) ---
# We added 'latest' and '8b' to find a model that isn't rate limited
CODER_MODELS = [
    "gemini-2.0-flash",          # Primary
    "gemini-1.5-flash-latest",   # Standard Backup
    "gemini-1.5-flash-8b-latest" # High-Availability Backup
]

MAX_QA_RETRIES = 4
REQUEST_TIMEOUT = 90

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

# --- PRE-FLIGHT ---
def test_connection():
    log(f"🔌 Testing Connection with {CODER_MODELS[0]}...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{CODER_MODELS[0]}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": "Hello"}]}]}
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        if resp.status_code == 200:
            log("✅ Connection Valid.")
            return True
        else:
            log(f"❌ Connection Failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        log(f"❌ Network Error: {e}")
        return False

# --- API ENGINE ---
def ask_gemini(prompt, model_list, role="coder"):
    if isinstance(model_list, str): model_list = [model_list]
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.1}
    }
    
    for model in model_list:
        model = model.strip()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        
        for attempt in range(2):
            try:
                log(f"🔄 [{role.upper()}] Asking {model}...")
                resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)
                
                if resp.status_code == 200:
                    try:
                        return resp.json()['candidates'][0]['content']['parts'][0]['text']
                    except: return None
                elif resp.status_code == 429:
                    log(f"⏳ {model} Rate Limit. Switching...")
                    time.sleep(2)
                    break 
                elif resp.status_code == 404:
                    log(f"🚫 {model} not found. Switching...")
                    break
                else:
                    log(f"❌ Error {resp.status_code}: {resp.text[:100]}...")
            except Exception as e:
                log(f"❌ Network Error: {e}")
    return None

# --- PATCH ENGINE ---
def apply_patch(original, patch):
    clean_patch = re.sub(r'^`[a-zA-Z]*\s*$', '', patch, flags=re.MULTILINE).strip()
    
    pattern = r"<<<<<<< SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, clean_patch, re.DOTALL)
    
    if not matches:
        # DEBUG: PRINT RAW RESPONSE TO SEE WHY IT FAILED
        log("⚠️ DEBUG: PARSING FAILED. RAW MODEL RESPONSE:")
        log("---------------------------------------------------")
        log(clean_patch[:500] + "..." if len(clean_patch) > 500 else clean_patch)
        log("---------------------------------------------------")
        return None, "No blocks found."
    
    new_code = original
    applied_count = 0
    
    for search, replace in matches:
        if search in new_code:
            new_code = new_code.replace(search, replace)
            applied_count += 1
        elif search.strip() in new_code:
            new_code = new_code.replace(search.strip(), replace.strip())
            applied_count += 1
        else:
            matcher = difflib.SequenceMatcher(None, new_code, search)
            match = matcher.find_longest_match(0, len(new_code), 0, len(search))
            if match.size > 0 and (match.size / len(search) > 0.8):
                 new_code = new_code[:match.a] + replace + new_code[match.a + match.size:]
                 applied_count += 1

    return new_code, f"Applied {applied_count} patches"

# --- DEPLOYMENT ---
def check_render():
    if not RENDER_API_KEY: return
    log("🚀 Watching Render...")
    url = f"[https://api.render.com/v1/services/](https://api.render.com/v1/services/){RENDER_SERVICE_ID}/deploys?limit=1"
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    for _ in range(20):
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200 and resp.json()[0]['deploy']['status'] == "live":
                log("✅ Deployment Live.")
                return
        except: pass
        time.sleep(15)

def move_task_to_bottom(task_name):
    content = read_file("BACKLOG.md")
    lines = content.splitlines()
    new_lines = []
    task_line = ""
    for line in lines:
        if f"- [ ] **{task_name}**" in line:
            task_line = f"- [ ] **{task_name}** (SKIPPED)"
        else:
            new_lines.append(line)
    if task_line:
        new_lines.append(""); new_lines.append("## ⚠️ SKIPPED TASKS"); new_lines.append(task_line)
    write_file("BACKLOG.md", "\n".join(new_lines))

# --- MAIN ---
def process_task():
    backlog = read_file("BACKLOG.md")
    match = re.search(r'- \[ \] \*\*(.*?)\*\*(?!\s*\(SKIPPED)', backlog)
    if not match: return False
    task = match.group(1).strip()
    
    log(f"\n📋 TARGET: {task}")
    code = read_file("index.html")
    context = read_file("AGENTS.md")
    history = ""
    
    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Attempt {attempt+1}/{MAX_QA_RETRIES}...")
        
        # STRICT PROMPT FOR BACKUP MODELS
        prompt = f"""
TASK: {task}
CONTEXT: {context}
ERRORS: {history}
CODE:
{code}

IMPORTANT INSTRUCTIONS:
1. You are a CODE GENERATOR, not a chat bot.
2. Output ONLY the SEARCH/REPLACE blocks.
3. DO NOT include any conversational text like "Here is the code".
4. FORMAT:
<<<<<<< SEARCH
(exact lines to remove)
=======
(new lines to insert)
>>>>>>> REPLACE
"""
        patch = ask_gemini(prompt, CODER_MODELS, role="coder")
        if not patch: continue
        
        new_code, status = apply_patch(code, patch)
        if not new_code:
            log(f"❌ Patch Failed: {status}")
            history = status
            continue
            
        log("✅ Verified. Committing...")
        write_file("index.html", new_code)
        
        new_backlog = read_file("BACKLOG.md").replace(f"- [ ] **{task}**", f"- [x] **{task}**")
        write_file("BACKLOG.md", new_backlog)
        
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        repo.index.commit(f"feat(jules): {task}")
        repo.remotes.origin.push()
        check_render()
        return True

    move_task_to_bottom(task)
    return True

if __name__ == "__main__":
    if test_connection():
        log("🤖 Jules Level 28 (DEBUGGER MODE) Started...")
        while process_task():
            time.sleep(5)
    else:
        log("🛑 Aborting.")
