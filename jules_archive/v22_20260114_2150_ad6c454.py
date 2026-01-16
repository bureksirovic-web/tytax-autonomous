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
MAX_QA_RETRIES = 3 
MAX_RUNTIME_MINUTES = 45
START_TIME = time.time()

def log(message):
    print(message, flush=True)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing!")

MODELS_TO_TRY = ["gemini-3-pro-preview", "gemini-3-flash-preview", "gemini-2.0-flash-exp"]

def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f: return f.read()

def write_file(filename, content):
    with open(filename, 'w', encoding='utf-8') as f: f.write(content)

def get_next_task():
    try:
        content = read_file("BACKLOG.md")
        match = re.search(r'- \[ \] \*\*(.*?)\*\*', content)
        return match.group(1).strip() if match else None
    except: return None

def ask_gemini_v6_style(prompt, model_hint="coder"):
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.1}}
    
    for model in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        for attempt in range(5): 
            log(f"🔄 [{model_hint.upper()}] {model} (Attempt {attempt+1}/5)...")
            try:
                resp = requests.post(url, headers=headers, data=json.dumps(data))
                if resp.status_code == 200:
                    res_json = resp.json()
                    # LOG THE RAW RESPONSE IMMEDIATELY
                    text = res_json['candidates'][0]['content']['parts'][0]['text']
                    log(f"📥 [RAW RESPONSE RECEIVED] Length: {len(text)} chars")
                    return text
                log(f"⚠️ API Status: {resp.status_code}")
            except Exception as e:
                log(f"❌ API Error: {e}")
            time.sleep(2)
    return None

def apply_patch(original_code, patch_text):
    pattern = r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, patch_text, re.DOTALL)
    if not matches: 
        log("🔍 [DEBUG] No markers found. AI Response starts with: " + patch_text[:100])
        return None, "No valid SEARCH/REPLACE blocks."
    
    new_code = original_code
    for search_block, replace_block in matches:
        if search_block in new_code:
            new_code = new_code.replace(search_block, replace_block)
            log("✅ Found exact match for search block.")
        else:
            log("❌ FAILED TO MATCH SEARCH BLOCK. First 50 chars of search: " + search_block[:50].replace('\n', ' '))
            return None, "Search block mismatch."
    return new_code, "Success"

def process_single_task():
    task = get_next_task()
    if not task: return False
    log(f"\n📋 TARGET: {task}")
    current_code = read_file("index.html")
    
    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Coder Attempt {attempt + 1}/{MAX_QA_RETRIES}...")
        prompt = f"TASK: {task}\nFORMAT: <<<<<<< SEARCH\n(old)\n=======\n(new)\n>>>>>>> REPLACE\n\nCODE:\n{current_code}"
        
        response = ask_gemini_v6_style(prompt)
        if not response: continue
        
        new_code, msg = apply_patch(current_code, response)
        if not new_code:
            log(f"❌ Patch Error: {msg}")
            continue
            
        log("✅ Patch Applied. Saving...")
        write_file("index.html", new_code)
        # Git Push logic omitted for brevity in logs but present in your script
        return True
    return False

log("🤖 Jules SURGICAL (ULTRA LOUD) Started...")
process_single_task()
