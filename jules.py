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

# Placeholder - populated by Auto-Discovery
CODER_MODELS = [] 

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

# --- AUTO-DISCOVERY ENGINE ---
def discover_models():
    """Queries the API to find valid models instead of guessing."""
    log("🔍 Auto-Discovering available models...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            log(f"❌ Discovery Failed: {resp.status_code} - {resp.text}")
            return []
            
        data = resp.json()
        valid_models = []
        
        # 1. Filter for 'generateContent' support
        for m in data.get('models', []):
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                # Strip 'models/' prefix if present
                name = m['name'].replace('models/', '')
                valid_models.append(name)
        
        # 2. Priority Ranking (2.0 > 1.5 > Pro > Flash)
        ranked = []
        
        # Priority 1: Gemini 2.0 (Smartest/Fastest)
        ranked.extend([m for m in valid_models if 'gemini-2.0' in m])
        
        # Priority 2: Gemini 1.5 Flash (Reliable)
        ranked.extend([m for m in valid_models if 'gemini-1.5-flash' in m and m not in ranked])
        
        # Priority 3: Gemini 1.5 Pro (High Logic)
        ranked.extend([m for m in valid_models if 'gemini-1.5-pro' in m and m not in ranked])
        
        # Priority 4: Anything else
        ranked.extend([m for m in valid_models if m not in ranked])
        
        log(f"✅ Discovered {len(ranked)} usable models.")
        log(f"📋 Priority Stack: {ranked[:5]}...")
        return ranked

    except Exception as e:
        log(f"❌ Discovery Error: {e}")
        return []

# --- API ENGINE ---
def ask_gemini(prompt, model_list, role="coder"):
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.1}
    }
    
    # Try the discovered models in order
    for model in model_list:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        
        for attempt in range(1): # Single attempt per model to fail fast and rotate
            try:
                log(f"🔄 [{role.upper()}] Asking {model}...")
                resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)
                
                if resp.status_code == 200:
                    try:
                        return resp.json()['candidates'][0]['content']['parts'][0]['text']
                    except: return None
                elif resp.status_code == 429:
                    log(f"⏳ {model} Rate Limit. Rotating...")
                    break # Next model
                elif resp.status_code == 404:
                    log(f"🚫 {model} returned 404 (Unexpected). Rotating...")
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
        log("⚠️ DEBUG: PARSING FAILED. RAW RESPONSE:")
        log(clean_patch[:300] + "...")
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
    global CODER_MODELS
    if not CODER_MODELS:
        CODER_MODELS = discover_models()
        if not CODER_MODELS:
            log("🛑 No models found via Auto-Discovery.")
            return False

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
        
        prompt = f"""
TASK: {task}
CONTEXT: {context}
ERRORS: {history}
CODE:
{code}

IMPORTANT INSTRUCTIONS:
1. You are a CODE GENERATOR.
2. Output ONLY the SEARCH/REPLACE blocks. NO conversational text.
3. FORMAT:
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
    log("🤖 Jules Level 30 (AUTO-DISCOVERY) Started...")
    while process_task():
        time.sleep(5)
