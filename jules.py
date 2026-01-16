import os
import re
import git
import requests
import json
import time
import sys
import random
import difflib
from datetime import datetime

# --- 1. CONFIGURATION ---
REPO_PATH = "."
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
RENDER_SERVICE_ID = os.environ.get("RENDER_SERVICE_ID")

# --- 2. MULTI-MODEL SWARM ---
# Coder: Fast, Creative (Writes the fix)
CODER_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-2.0-flash-exp"]

# Sentinel: Smart, Strict (The Compiler) - Must be high reasoning
SENTINEL_MODEL = "gemini-1.5-pro-latest"

# Critic: Standard Review (Logic checker) - Restored from v29
CRITIC_MODELS = ["gemini-1.5-flash-latest", "gemini-2.0-flash"]

MAX_QA_RETRIES = 4
REQUEST_TIMEOUT = 60
UNAVAILABLE_MODELS = set() # Ghost Protocol

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

# --- 3. CONTEXT ENGINE (Restored from v29) ---
def truncate_content(content, max_chars=12000):
    if len(content) <= max_chars: return content
    half = max_chars // 2
    return content[:half] + "\n\n... [TRUNCATED] ...\n\n" + content[-half:]

def get_system_context():
    context_buffer = ""
    # We load ALL docs again, not just AGENTS.md
    doc_files = ["AGENTS.md", "ARCHITECTURE.md", "TESTING_PROTOCOL.md"]
    for doc in doc_files:
        content = read_file(doc)
        if content:
            content = truncate_content(content)
            context_buffer += f"\n\n=== SYSTEM CONTEXT: {doc} ===\n{content}\n"
    return context_buffer

# --- 4. INTELLIGENT API CALLER ---
def call_gemini(model_list, prompt, temp=0.1, role="coder"):
    if isinstance(model_list, str): model_list = [model_list]
    
    for model in model_list:
        if model in UNAVAILABLE_MODELS: continue

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 8192, "temperature": temp}
        }
        
        try:
            log(f"🔄 [{role.upper()}] Asking {model}...")
            resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)
            
            if resp.status_code == 200:
                try:
                    return resp.json()['candidates'][0]['content']['parts'][0]['text']
                except: return None
            
            elif resp.status_code == 404:
                log(f"🚫 Ghost Protocol: {model} not found.")
                UNAVAILABLE_MODELS.add(model)
            
            elif resp.status_code == 429:
                log(f"⏳ Rate Limit on {model}. Sleeping 5s...")
                time.sleep(5)
                
        except Exception as e:
            log(f"❌ API Error: {e}")
            
    return None

# --- 5. THE SENTINEL (SAFETY RAIL) ---
def sentinel_check(code, task):
    log("🛡️ Sentinel is scanning code for ReferenceErrors...")
    
    prompt = f"""
    ROLE: You are a STRICT Javascript Compiler.
    TASK: Scan this React code for CRITICAL RUNTIME ERRORS.
    
    CHECKLIST:
    1. Are all variables used in JSX (like 'toast', 'showModal') defined?
    2. Are Hooks (useState) inside the component?
    3. Are there Syntax Errors (unclosed brackets)?
    
    CODE:
    {code[:20000]}... [truncated]
    
    OUTPUT:
    - If Safe: "PASS"
    - If Unsafe: "FAIL: [Reason]"
    """
    
    response = call_gemini([SENTINEL_MODEL], prompt, temp=0.0, role="sentinel")
    if response and "PASS" in response:
        return True, "Safe"
    return False, response or "No response"

# --- 6. SURGICAL PATCHING (Hybrid: Regex + Fuzzy) ---
def apply_patch(original, patch):
    # 1. Clean Markdown (From Level 19)
    clean_patch = re.sub(r'^`[a-zA-Z]*\s*$', '', patch, flags=re.MULTILINE).strip()
    
    pattern = r"<<<<<<< SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, clean_patch, re.DOTALL)
    if not matches: return None, "No blocks found."
    
    new_code = original
    applied_count = 0
    
    for search_block, replace_block in matches:
        # Strategy A: Exact Match
        if search_block in new_code:
            new_code = new_code.replace(search_block, replace_block)
            applied_count += 1
        # Strategy B: Whitespace Strip
        elif search_block.strip() in new_code:
            new_code = new_code.replace(search_block.strip(), replace_block.strip())
            applied_count += 1
        # Strategy C: Fuzzy Match (Restored from Level 15)
        else:
            log("⚠️ Exact match failed. Attempting Fuzzy Match...")
            matcher = difflib.SequenceMatcher(None, new_code, search_block)
            match = matcher.find_longest_match(0, len(new_code), 0, len(search_block))
            if match.size > 0:
                found_block = new_code[match.a : match.a + match.size]
                ratio = difflib.SequenceMatcher(None, found_block, search_block).ratio()
                if ratio >= 0.85: # Threshold
                    log(f"✅ Fuzzy Match Applied (Score: {ratio:.2f})")
                    new_code = new_code[:match.a] + replace_block + new_code[match.a + match.size:]
                    applied_count += 1
                else:
                    return None, f"Block match failed (Fuzzy score {ratio:.2f} too low)."

    if "<!DOCTYPE html>" not in new_code: return None, "CRITICAL: Root tag deleted."
    return new_code, f"Applied {applied_count} patches"

# --- 7. DEPLOYMENT & TASK MANAGEMENT ---
def check_render():
    if not RENDER_API_KEY: 
        log("⚠️ No Render Key. Skipping Check.")
        return
    
    log("🚀 Watching Render Deployment...")
    url = f"[https://api.render.com/v1/services/](https://api.render.com/v1/services/){RENDER_SERVICE_ID}/deploys?limit=1"
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    
    for _ in range(20): # 5 mins max
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                status = resp.json()[0]['deploy']['status']
                log(f"📡 Status: {status}")
                if status == "live": 
                    log("✅ Deployment Live.")
                    return
                if status in ["build_failed", "canceled"]:
                    log("❌ Deployment FAILED on Render.")
                    return
        except: pass
        time.sleep(15)

def move_task_to_bottom(task_name, reason="Stuck"):
    content = read_file("BACKLOG.md")
    lines = content.splitlines()
    new_lines = []
    task_line = ""
    
    for line in lines:
        if f"- [ ] **{task_name}**" in line:
            task_line = f"- [ ] **{task_name}** (SKIPPED: {reason})"
        else:
            new_lines.append(line)
            
    if task_line:
        new_lines.append("") 
        new_lines.append("## ⚠️ SKIPPED TASKS")
        new_lines.append(task_line)
        
    write_file("BACKLOG.md", "\n".join(new_lines))

# --- MAIN LOOP ---
def process_task():
    backlog = read_file("BACKLOG.md")
    match = re.search(r'- \[ \] \*\*(.*?)\*\*(?!\s*\(SKIPPED)', backlog)
    if not match: return False
    task = match.group(1).strip()
    
    log(f"\n📋 TARGET: {task}")
    code = read_file("index.html")
    history = ""
    system_context = get_system_context()
    
    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Attempt {attempt+1}/{MAX_QA_RETRIES}...")
        
        # 1. CODER (With full context)
        prompt = f"""
TASK: {task}
{system_context}
PREVIOUS_ERRORS: {history}
CODE: {code}

INSTRUCTIONS:
1. Return ONLY the SEARCH/REPLACE blocks.
2. DO NOT wrap in Markdown (no `).

FORMAT:
<<<<<<< SEARCH
(exact code to remove)
=======
(new code to insert)
>>>>>>> REPLACE
"""
        patch = call_gemini(CODER_MODELS, prompt, role="coder")
        if not patch: continue
        
        # 2. PATCH
        new_code, status = apply_patch(code, patch)
        if not new_code:
            log(f"❌ Patch Failed: {status}")
            history = status
            continue
            
        # 3. SENTINEL
        is_safe, msg = sentinel_check(new_code, task)
        if not is_safe:
            log(f"🚫 SENTINEL BLOCKED: {msg}")
            history = f"Sentinel Compiler Error: {msg}"
            continue
            
        # 4. CRITIC (Restored from Level 15)
        log("🕵️ Critic Reviewing...")
        critic_prompt = f"TASK: {task}\nReview this code change. Reply PASS or FAIL.\n\nPATCH:\n{patch}"
        review = call_gemini(CRITIC_MODELS, critic_prompt, role="critic")
        if not review or "FAIL" in review:
            log(f"❌ Critic Rejected: {review}")
            history = review
            continue

        # 5. DEPLOY
        log("✅ ALL CHECKS PASSED. Committing...")
        write_file("index.html", new_code)
        
        new_backlog = read_file("BACKLOG.md").replace(f"- [ ] **{task}**", f"- [x] **{task}**")
        write_file("BACKLOG.md", new_backlog)
        
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        repo.index.commit(f"feat(jules): {task}")
        repo.remotes.origin.push()
        
        check_render()
        return True

    log("⚠️ Task stuck. Moving to bottom.")
    move_task_to_bottom(task)
    
    repo = git.Repo(REPO_PATH)
    repo.git.add("BACKLOG.md")
    repo.index.commit("skip: stuck task")
    repo.remotes.origin.push()
    return True

if __name__ == "__main__":
    while process_task():
        time.sleep(5)
