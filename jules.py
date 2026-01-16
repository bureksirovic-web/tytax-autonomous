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
# Jules Level 33 (STABILITY TUNE)
# ============================
# Changes from Level 31:
# - PRIORITY CHANGE: Demoted Gemini 3 (Unstable/Slow). Promoted Gemini 2.0 & 1.5 Pro.
# - TIMEOUT: Increased to 120s to prevent 'Request timed out' errors.
# - PROMPT: Added stricter 'No Chatter' instructions to fix patch parsing errors.

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

MAX_QA_RETRIES = 8
MAX_RUNTIME_MINUTES = int(_clean_env("MAX_RUNTIME_MINUTES", "45") or 45)
# INCREASED TIMEOUT FOR SAFETY
REQUEST_TIMEOUT = int(_clean_env("REQUEST_TIMEOUT", "120") or 120)
START_TIME = time.time()

ENABLE_FUZZY_PATCH = True

DEFAULT_CONTEXT_FILES = ["AGENTS.md", "ARCHITECTURE.md"]
CONTEXT_FILES = [
    f.strip() for f in (_clean_env("JULES_CONTEXT_FILES", ",".join(DEFAULT_CONTEXT_FILES))).split(",") if f.strip()
]

MANUAL_MODELS = [m.strip() for m in _clean_env("JULES_MODELS", "").split(",") if m.strip()]
MANUAL_CRITIC_MODELS = [m.strip() for m in _clean_env("JULES_CRITIC_MODELS", "").split(",") if m.strip()]

STATIC_FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-2.0-flash-exp",
    "gemini-3-flash-preview"
]

# === PRIORITY UPDATE: 2.0 & 1.5 FIRST ===
PRIORITY_PATTERNS = [
    r"^gemini-2\.0-flash$",      # Best balance (Smart/Fast)
    r"^gemini-1\.5-pro$",        # Best Logic (Stable)
    r"^gemini-1\.5-pro-",        # Newer 1.5 Pro versions
    r"^gemini-2\.0-flash-",      # Other 2.0 variants
    r"^gemini-1\.5-flash$",      # High speed backup
    r"^gemini-3-",               # Demoted to fallback due to instability
]

def log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)

def read_file(filename: str) -> str:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def write_file(filename: str, content: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def _dedupe(seq):
    out = []
    seen = set()
    for x in seq:
        if x and x not in seen:
            out.append(x)
            seen.add(x)
    return out

def discover_models() -> list[str]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        log("🔍 Auto-discovering available models...")
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            log(f"❌ Discovery failed: {resp.status_code}")
            return []

        data = resp.json()
        valid = []
        for m in data.get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                name = (m.get("name") or "").replace("models/", "")
                if name:
                    valid.append(name)

        ranked: list[str] = []
        for pat in PRIORITY_PATTERNS:
            rx = re.compile(pat)
            ranked.extend([m for m in valid if rx.search(m)])

        ranked.extend([m for m in valid if m.startswith("gemini")])
        ranked = _dedupe(ranked)
        
        log(f"✅ Discovered {len(ranked)} usable models.")
        if ranked:
            log(f"📋 Priority stack: {ranked[:6]}")
        return ranked
    except Exception as e:
        log(f"❌ Discovery error: {e}")
        return []

def pick_models() -> list[str]:
    if MANUAL_MODELS:
        return _dedupe(MANUAL_MODELS + STATIC_FALLBACK_MODELS)
    discovered = discover_models()
    if discovered:
        return _dedupe(discovered + STATIC_FALLBACK_MODELS)
    return _dedupe(STATIC_FALLBACK_MODELS)

def pick_critic_models(coder_models: list[str]) -> list[str]:
    if MANUAL_CRITIC_MODELS:
        return _dedupe(MANUAL_CRITIC_MODELS + STATIC_FALLBACK_MODELS)
    return coder_models

def extract_text_from_response(response_json) -> str | None:
    try:
        parts = response_json["candidates"][0]["content"]["parts"]
        return "".join([p.get("text", "") for p in parts if isinstance(p, dict)])
    except Exception:
        return None

def ask_gemini(prompt: str, model_list: list[str], role: str) -> str | None:
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.1},
    }

    for model in model_list:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        for attempt in range(2): # Reduced retries per model to rotate faster
            try:
                log(f"🔄 [{role.upper()}] {model} (Attempt {attempt+1}/2)")
                resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)

                if resp.status_code == 200:
                    text = extract_text_from_response(resp.json())
                    if text:
                        return text
                    log("⚠️ [200 OK] Empty text payload; rotating...")
                    break

                if resp.status_code == 429:
                    log("⏳ [429 Rate Limit] Switching models...")
                    time.sleep(2)
                    break 

                if resp.status_code in (404,):
                    log(f"🚫 Model not found (404): {model}. Rotating...")
                    break
                
                log(f"❌ API Error {resp.status_code}: {resp.text[:100]}...")
                break

            except requests.exceptions.Timeout:
                log("⏱️ Request timed out; rotating...")
                break
            except Exception as e:
                log(f"❌ Network/Runtime error: {e}")
                break
    return None

def _strip_code_fences(text: str) -> str:
    text = re.sub(r"`[a-zA-Z0-9_-]*\s*\n", "", text)
    text = text.replace("`", "")
    return text

def sanitize_patch_response(raw: str) -> str:
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    raw = _strip_code_fences(raw)
    start = raw.find("<<<<<<< SEARCH")
    end = raw.rfind(">>>>>>> REPLACE")
    if start != -1 and end != -1:
        raw = raw[start : end + len(">>>>>>> REPLACE")]
    return raw.strip()

def apply_patch(original_code: str, patch_text: str) -> tuple[str | None, str]:
    patch_text = sanitize_patch_response(patch_text)
    pattern = r"<<<<<<< SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, patch_text, re.DOTALL)

    if not matches:
        return None, "No valid SEARCH/REPLACE blocks found."

    new_code = original_code
    applied = 0

    for search_block, replace_block in matches:
        idx = new_code.find(search_block)
        if idx != -1:
            new_code = new_code.replace(search_block, replace_block, 1)
            applied += 1
            continue

        s = search_block.strip()
        if s and s in new_code:
            new_code = new_code.replace(s, replace_block.strip(), 1)
            applied += 1
            continue
            
        return None, f"Search block mismatch. Starts with: {search_block[:50]}..."

    return new_code, f"Applied {applied} patch(es)."

def verify_fix(task: str, original_code: str, new_code: str, model_list: list[str]) -> tuple[bool, str]:
    if original_code == new_code:
        return False, "No changes detected."

    diff = "".join(difflib.unified_diff(original_code.splitlines(True), new_code.splitlines(True), n=3))

    critic_prompt = (
        "ROLE: Strict Code Reviewer.\n"
        f"TASK: {task}\n"
        "INSTRUCTIONS: Reply 'PASS' or 'FAIL: <reason>'.\n"
        f"DIFF:\n{diff}"
    )

    review = ask_gemini(critic_prompt, model_list, role="critic")
    if not review: return True, "Critic silent."
    
    if "PASS" in review.upper(): return True, review.strip()
    return False, review.strip()

def get_next_task() -> str | None:
    backlog = read_file(BACKLOG_FILE)
    match = re.search(r"- \[ \] \*\*(.*?)\*\*(?!\s*\(SKIPPED)", backlog)
    return match.group(1).strip() if match else None

def mark_task_done(task: str) -> None:
    content = read_file(BACKLOG_FILE)
    updated = content.replace(f"- [ ] **{task}**", f"- [x] **{task}**")
    write_file(BACKLOG_FILE, updated)

def move_task_to_bottom(task: str, reason: str) -> None:
    content = read_file(BACKLOG_FILE)
    lines = content.splitlines()
    new_lines = []
    task_skipped = False
    
    for line in lines:
        if f"- [ ] **{task}**" in line:
            new_lines.append(f"- [ ] **{task}** (SKIPPED: {reason})")
            task_skipped = True
        else:
            new_lines.append(line)
            
    if task_skipped:
        if "## ⚠️ SKIPPED TASKS" not in content:
            new_lines.append(""); new_lines.append("## ⚠️ SKIPPED TASKS")
        # We modified the line in place, so no need to append again, just save
    
    write_file(BACKLOG_FILE, "\n".join(new_lines))

def load_context() -> str:
    parts = []
    for f in CONTEXT_FILES:
        txt = read_file(f)
        if txt.strip(): parts.append(f"\n--- {f} ---\n{txt}\n")
    return "\n".join(parts).strip()[:8000]

def git_sync_and_push(repo: git.Repo) -> bool:
    try:
        repo.git.pull("--rebase")
        repo.remotes.origin.push()
        log("🚀 Pushed to GitHub.")
        return True
    except Exception:
        return False

def process_single_task(model_list: list[str]) -> bool:
    task = get_next_task()
    if not task: return False
    
    log(f"\n📋 TARGET: {task}")
    current_code = read_file(APP_FILE)
    context = load_context()
    history = ""

    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Coder Attempt {attempt + 1}/{MAX_QA_RETRIES}...")

        prompt = (
            f"TASK: {task}\n"
            f"CONTEXT: {context}\n"
            f"ERRORS: {history}\n"
            "OUTPUT RULES: Output ONLY SEARCH/REPLACE blocks. NO CHATTER. NO MARKDOWN.\n"
            "FORMAT:\n<<<<<<< SEARCH\n(code to remove)\n=======\n(code to insert)\n>>>>>>> REPLACE\n\n"
            f"CODE:\n{current_code}"
        )

        patch = ask_gemini(prompt, model_list, role="coder")
        if not patch: continue

        new_code, status = apply_patch(current_code, patch)
        if not new_code:
            log(f"❌ Patch failed: {status}")
            history = f"Patch failed: {status}"
            continue

        ok, feedback = verify_fix(task, current_code, new_code, pick_critic_models(model_list))
        if not ok:
            log(f"❌ QA failed: {feedback}")
            history = feedback
            continue

        log("✅ QA PASSED. Committing...")
        write_file(APP_FILE, new_code)
        mark_task_done(task)
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        repo.index.commit(f"feat(jules): {task}")
        git_sync_and_push(repo)
        return True

    move_task_to_bottom(task, "Max retries")
    repo = git.Repo(REPO_PATH); repo.git.add(BACKLOG_FILE); repo.index.commit("skip: stuck task"); git_sync_and_push(repo)
    return True

if __name__ == "__main__":
    if not GEMINI_API_KEY: sys.exit(1)
    log("🤖 Jules Level 33 (STABILITY TUNE) Started...")
    models = pick_models()
    while process_single_task(models):
        time.sleep(5)



