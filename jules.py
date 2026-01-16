import os
import re
import sys
import time
import json
import difflib
from datetime import datetime

import git
import requests

# ============================
# Jules Level 35.1 (STABILITY + PERSISTENCE)
# ============================
# Goals:
# - Fix syntax error in Deep Thinking logic.
# - Maintain 15 retries for extreme persistence.
# - Increase timeout to 180s for large file processing.

REPO_PATH = os.environ.get("JULES_REPO_PATH", ".")
APP_FILE = os.environ.get("JULES_APP_FILE", "index.html")
BACKLOG_FILE = os.environ.get("JULES_BACKLOG_FILE", "BACKLOG.md")

def _clean_env(name: str, default: str = "") -> str:
    raw = os.environ.get(name, default)
    return (raw or "").replace("\n", "").replace("\r", "").strip()

GEMINI_API_KEY = _clean_env("GEMINI_API_KEY")
RENDER_API_KEY = _clean_env("RENDER_API_KEY")
RENDER_SERVICE_ID = _clean_env("RENDER_SERVICE_ID") or "srv-d5jlon15pdvs739hp3jg"
SITE_URL = _clean_env("SITE_URL") or "https://tytax-elite.onrender.com"

MAX_QA_RETRIES = 15
MAX_RUNTIME_MINUTES = 90
REQUEST_TIMEOUT = 180
START_TIME = time.time()

ENABLE_FUZZY_PATCH = True

DEFAULT_CONTEXT_FILES = ["AGENTS.md", "ARCHITECTURE.md"]
CONTEXT_FILES = [f.strip() for f in (_clean_env("JULES_CONTEXT_FILES", ",".join(DEFAULT_CONTEXT_FILES))).split(",") if f.strip()]

PRIORITY_PATTERNS = [
    r"^gemini-2\.0-flash$",
    r"^gemini-1\.5-pro$",
    r"^gemini-1\.5-flash$",
    r"^gemini-3-",
]

def log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)

def read_file(filename: str) -> str:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception: return ""

def write_file(filename: str, content: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def discover_models() -> list[str]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200: return []
        data = resp.json()
        valid = [m.get("name", "").replace("models/", "") for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
        ranked = []
        for pat in PRIORITY_PATTERNS:
            rx = re.compile(pat)
            ranked.extend([m for m in valid if rx.search(m)])
        return list(dict.fromkeys(ranked + valid))
    except Exception: return []

def pick_models() -> list[str]:
    discovered = discover_models()
    fallbacks = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
    return list(dict.fromkeys(discovered + fallbacks))

def ask_gemini(prompt: str, model_list: list[str], role: str) -> str | None:
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.1}}
    for model in model_list:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            log(f"🔄 [{role.upper()}] {model}")
            resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                parts = resp.json()["candidates"][0]["content"]["parts"]
                return "".join([p.get("text", "") for p in parts])
        except Exception: continue
    return None

def apply_patch(original_code: str, patch_text: str) -> tuple[str | None, str]:
    patch_text = re.sub(r"`[a-zA-Z0-9_-]*\s*\n", "", patch_text).replace("`", "").strip()
    pattern = r"<<<<<<< SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, patch_text, re.DOTALL)
    if not matches: return None, "No blocks found."
    new_code = original_code
    for s, r in matches:
        if s in new_code: new_code = new_code.replace(s, r, 1)
        elif ENABLE_FUZZY_PATCH:
            matcher = difflib.SequenceMatcher(None, new_code, s)
            m = matcher.find_longest_match(0, len(new_code), 0, len(s))
            if m.size / len(s) >= 0.9:
                new_code = new_code[:m.a] + r + new_code[m.a + m.size:]
            else: return None, "Mismatch."
        else: return None, "Mismatch."
    return new_code, "Success"

def process_single_task(model_list: list[str]) -> bool:
    backlog = read_file(BACKLOG_FILE)
    match = re.search(r"- \[ \] \*\*(.*?)\*\*", backlog)
    if not match: return False
    task = match.group(1).strip()
    log(f"\n📋 TARGET: {task}")
    current_code = read_file(APP_FILE)
    
    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Coder Attempt {attempt + 1}/{MAX_QA_RETRIES}...")
        
        # Deep Thinking Logic (Multi-line fix)
        if attempt > 10:
            log("⏳ Deep Thinking Mode: Resting 60s...")
            time.sleep(60)
        elif attempt > 5:
            time.sleep(10)

        prompt = f"TASK: {task}\nRULES: Output ONLY SEARCH/REPLACE blocks.\nCODE:\n{current_code}"
        patch = ask_gemini(prompt, model_list, role="coder")
        if not patch: continue
        new_code, status = apply_patch(current_code, patch)
        if not new_code: continue
        
        log("✅ Task Complete. Committing...")
        write_file(APP_FILE, new_code)
        write_file(BACKLOG_FILE, backlog.replace(f"- [ ] **{task}**", f"- [x] **{task}**"))
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        repo.index.commit(f"feat: {task}")
        repo.remotes.origin.push()
        return True
    return False

if __name__ == "__main__":
    log("🤖 Jules Level 35.1 (DEEP THINKER) Started...")
    models = pick_models()
    while process_single_task(models): time.sleep(5)
