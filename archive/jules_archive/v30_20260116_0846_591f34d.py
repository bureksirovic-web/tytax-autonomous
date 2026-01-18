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

# --- CONFIGURATION & ENV ---
REPO_PATH = "."
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
RENDER_SERVICE_ID = os.environ.get("RENDER_SERVICE_ID")
SITE_URL = os.environ.get("SITE_URL", "https://tytax-elite.onrender.com")

# DRY RUN: If set to '1', disables Git Push and Render checks
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

# Timing & Retries
MAX_QA_RETRIES = int(os.environ.get("MAX_QA_RETRIES", 4))
MAX_RUNTIME_MINUTES = int(os.environ.get("MAX_RUNTIME_MINUTES", 60))
REQUEST_TIMEOUT = 60  
COOL_DOWN_SECONDS = 5 # Force a breather between heavy requests

# Model Configuration
def get_model_list(env_var, defaults):
    val = os.environ.get(env_var)
    if val:
        return [m.strip() for m in val.split(",") if m.strip()]
    return defaults

# UPDATED: Fixed 404s by using '-latest' and reordered for stability
CODER_MODELS = get_model_list("JULES_CODER_MODELS", [
    "gemini-2.0-flash",        # 1. Primary
    "gemini-1.5-flash-latest", # 2. Fixed Name (was 404ing)
    "gemini-2.0-flash-exp",    # 3. Fallback
    "gemini-3-pro-preview"     # 4. Emergency Only
])

CRITIC_MODELS = get_model_list("JULES_CRITIC_MODELS", [
    "gemini-1.5-pro-latest",   # 1. Fixed Name
    "gemini-2.0-flash"         # 2. Fast Check
])

# Generation Configs
CODER_CONFIG = {"maxOutputTokens": 8192, "temperature": 0.1}
CRITIC_CONFIG = {"maxOutputTokens": 1024, "temperature": 0.0}

# Global State
START_TIME = time.time()
UNAVAILABLE_MODELS = set() 

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

if not GEMINI_API_KEY:
    log("❌ ERROR: GEMINI_API_KEY missing!")
    sys.exit(1)

# --- UTILS ---

def read_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f: return f.read()
    except FileNotFoundError:
        return ""

def write_file(filename, content):
    with open(filename, 'w', encoding='utf-8') as f: f.write(content)

def truncate_content(content, max_chars=12000):
    if len(content) <= max_chars: return content
    half = max_chars // 2
    return content[:half] + "\n\n... [TRUNCATED SYSTEM CONTEXT] ...\n\n" + content[-half:]

def get_system_context():
    context_buffer = ""
    doc_files = ["AGENTS.md", "ARCHITECTURE.md", "TESTING_PROTOCOL.md"]
    for doc in doc_files:
        content = read_file(doc)
        if content:
            content = truncate_content(content)
            context_buffer += f"\n\n=== SYSTEM CONTEXT: {doc} ===\n{content}\n"
    total_len = len(context_buffer)
    log(f"🧠 Loaded System Context (~{total_len} chars)")
    return context_buffer

# --- GEMINI API ENGINE ---

def extract_text_from_response(response_json):
    try:
        if 'candidates' in response_json and response_json['candidates']:
            parts = response_json['candidates'][0]['content']['parts']
            return "".join([p.get("text", "") for p in parts])
    except (KeyError, IndexError, TypeError) as e:
        log(f"⚠️ Failed to extract text: {e}")
    return None

def call_gemini_api(model, prompt, generation_config):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": generation_config}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        log(f"❌ Network Error ({model}): {e}")
        return None, 0 

    return response.json(), response.status_code

def ask_gemini_swarm(prompt, role="coder"):
    models = CODER_MODELS if role == "coder" else CRITIC_MODELS
    config = CODER_CONFIG if role == "coder" else CRITIC_CONFIG
    
    for model in models:
        if model in UNAVAILABLE_MODELS: continue 

        max_retries = 2
        for attempt in range(max_retries + 1):
            log(f"🔄 [{role.upper()}] {model} (Attempt {attempt+1})...")
            
            response_json, status_code = call_gemini_api(model, prompt, config)

            if status_code == 200:
                text = extract_text_from_response(response_json)
                if text:
                    time.sleep(1) # Tiny pause after success
                    return text
                else:
                    log(f"⚠️ Empty response from {model}")
                    break 
            
            elif status_code == 429:
                log(f"⏳ 429 Rate Limit on {model}")
                sleep_time = 5 * (2 ** attempt) # Aggressive backoff (5s, 10s, 20s)
                if attempt < max_retries:
                    log(f"   Sleeping {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                else:
                    log(f"   Skipping {model} due to persistent 429.")
            
            elif status_code == 404:
                log(f"🚫 Model Not Found: {model}. Marking unavailable.")
                UNAVAILABLE_MODELS.add(model)
                break 
            
            elif status_code >= 500:
                log(f"💥 Server Error {status_code}")
                time.sleep(5)
            else:
                log(f"❌ API Error {status_code}: {response_json}")
                break 

    log(f"❌ All models failed for role: {role}")
    return None

# --- PATCH ENGINE ---

def robust_fuzzy_replace(original, search_block, replace_block):
    if search_block in original:
        log("✅ Patch Method: Exact Match")
        return original.replace(search_block, replace_block), True

    if search_block.strip() in original:
        log("✅ Patch Method: Whitespace Strip Match")
        return original.replace(search_block.strip(), replace_block), True

    # Fuzzy Match
    matcher = difflib.SequenceMatcher(None, original, search_block)
    match = matcher.find_longest_match(0, len(original), 0, len(search_block))
    
    if match.size > 0:
        found_block = original[match.a : match.a + match.size]
        ratio = difflib.SequenceMatcher(None, found_block, search_block).ratio()
        
        if ratio >= 0.88:
            log(f"✅ Patch Method: Fuzzy Match (Score {ratio:.4f})")
            new_code = original[:match.a] + replace_block + original[match.a + match.size:]
            return new_code, True
        else:
            log(f"❌ Fuzzy match score too low ({ratio:.4f})")
    
    return original, False

def apply_patches(original_code, response_text):
    pattern = r"<<<<<<< SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, response_text, re.DOTALL)
    
    if not matches: return None, "No valid SEARCH/REPLACE blocks found."

    current_code = original_code
    applied_count = 0
    
    for search_block, replace_block in matches:
        new_code, success = robust_fuzzy_replace(current_code, search_block, replace_block)
        if success:
            current_code = new_code
            applied_count += 1
        else:
            return None, f"Failed to match block:\n{search_block[:50]}..."

    if current_code == original_code: return None, "Code unchanged."
    if "<!DOCTYPE html>" not in current_code: return None, "CRITICAL: Root tags removed."

    return current_code, f"Applied {applied_count} patches."

# --- GIT & DEPLOY ---

def get_next_task():
    content = read_file("BACKLOG.md")
    if not content: return None
    match = re.search(r'- \[ \] \*\*(.*?)\*\*', content)
    return match.group(1).strip() if match else None

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

def git_operations(task_name):
    if DRY_RUN: return True
    try:
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        if not repo.index.diff("HEAD"):
            log("⚠️ No git changes to commit.")
            return True
        repo.index.commit(f"feat(jules): {task_name}")
        log("🔄 Pulling & Pushing to GitHub...")
        repo.remotes.origin.pull(rebase=True)
        repo.remotes.origin.push()
        return True
    except Exception as e:
        log(f"❌ Git Error: {e}")
        return False

def check_render_deploy():
    if DRY_RUN or not RENDER_API_KEY: 
        log("⚠️ No Render Key: Skipping Check")
        return True
    
    log("🚀 Monitoring Render Deployment...")
    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys?limit=1"
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}

    for _ in range(20): 
        try:
            resp = requests.get(url, headers=headers, timeout=10)
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

# --- MAIN ---

def process_single_task():
    task = get_next_task()
    if not task:
        log("✅ No tasks found.")
        return False
    
    log(f"\n📋 TARGET: {task}")
    system_context = get_system_context()
    original_code = read_file("index.html")
    critique_history = ""
    
    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Attempt {attempt + 1}/{MAX_QA_RETRIES}...")

        prompt = f"""
{system_context}
---
TASK: {task}
CRITIQUE HISTORY: {critique_history}
INSTRUCTIONS: Return SEARCH/REPLACE blocks.
FORMAT:
<<<<<<< SEARCH
(code)
=======
(code)
>>>>>>> REPLACE
CODE CONTEXT:
{original_code}
"""
        response_text = ask_gemini_swarm(prompt, role="coder")
        if not response_text: continue

        new_code, patch_msg = apply_patches(original_code, response_text)
        if not new_code:
            log(f"❌ Patch Failed: {patch_msg}")
            critique_history = f"PATCH ERROR: {patch_msg}"
            continue
        
        log("🕵️ Critic Reviewing...")
        diff = "".join(difflib.unified_diff(original_code.splitlines(True), new_code.splitlines(True), n=3))
        critic_prompt = f"""
{truncate_content(system_context, 4000)}
---
ROLE: Critic. TASK: {task}. DIFF:
{diff}
Reply STRICTLY with "PASS" or "FAIL: reason".
"""
        critic_response = ask_gemini_swarm(critic_prompt, role="critic")
        
        if critic_response and "PASS" in critic_response.upper() and "FAIL" not in critic_response.upper():
            log("✅ QA Passed.")
            write_file("index.html", new_code)
            mark_task_done(task)
            if git_operations(task):
                check_render_deploy() # <--- HERE IS THE CHECK
            return True
        else:
            reason = critic_response if critic_response else "No response"
            log(f"❌ Critic FAILED: {reason}")
            critique_history = f"CRITIC REJECTED: {reason}"
            time.sleep(COOL_DOWN_SECONDS) # Prevent hammer

    mark_task_failed(task, "Max retries exhausted")
    log("⚠️ Task Failed: Skipping Render Check") # <--- Explicit log for you
    return True

def run():
    log("🤖 Jules Level 15 (STABILIZED) Started...")
    while True:
        if (time.time() - START_TIME) / 60 > MAX_RUNTIME_MINUTES: break
        if not process_single_task(): break
        time.sleep(5)

if __name__ == "__main__":
    run()
