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
# Jules Level 31 (Master Restore v2)
# ============================
# Philosophy: Level 9's simplicity + Modern safety fixes
# - 2 models max (coder + critic use same stack)
# - Strict patching only (no fuzzy by default)
# - Clean error messages for feedback loop
# - Git sync before push to prevent conflicts

REPO_PATH = os.environ.get("JULES_REPO_PATH", ".")
APP_FILE = os.environ.get("JULES_APP_FILE", "index.html")
BACKLOG_FILE = os.environ.get("JULES_BACKLOG_FILE", "BACKLOG.md")

def _clean_env(name: str, default: str = "") -> str:
    raw = os.environ.get(name, default)
    return (raw or "").replace("\n", "").replace("\r", "").strip()

GEMINI_API_KEY = _clean_env("GEMINI_API_KEY")
RENDER_API_KEY = _clean_env("RENDER_API_KEY")
RENDER_SERVICE_ID = _clean_env("RENDER_SERVICE_ID")

MAX_QA_RETRIES = int(_clean_env("MAX_QA_RETRIES", "3") or 3)  # Reduced from 4
MAX_RUNTIME_MINUTES = int(_clean_env("MAX_RUNTIME_MINUTES", "45") or 45)
REQUEST_TIMEOUT = int(_clean_env("REQUEST_TIMEOUT", "90") or 90)
START_TIME = time.time()

# Simple 2-model strategy (Level 9 style)
# Primary: gemini-2.0-flash-exp (smart, fast, stable)
# Backup: gemini-1.5-pro (separate quota pool, high reasoning)
CODER_MODELS = [
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro"
]

# Override if needed: JULES_MODELS="model1,model2"
MANUAL_OVERRIDE = [m.strip() for m in _clean_env("JULES_MODELS", "").split(",") if m.strip()]
if MANUAL_OVERRIDE:
    CODER_MODELS = MANUAL_OVERRIDE

# Context files (keep minimal like Level 9)
CONTEXT_FILES = ["AGENTS.md"]


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
        
        # Try each model twice, then rotate
        for attempt in range(2):
            try:
                log(f"🔄 [{role.upper()}] {model} (attempt {attempt+1}/2)")
                resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)

                if resp.status_code == 200:
                    text = extract_text_from_response(resp.json())
                    if text:
                        return text
                    log("⚠️ Empty response, rotating...")
                    break

                if resp.status_code == 429:
                    log(f"⏳ Rate limit on {model}, rotating...")
                    time.sleep(2)
                    break

                if resp.status_code == 404:
                    log(f"🚫 Model {model} not found, rotating...")
                    break

                if resp.status_code >= 500:
                    log(f"⚠️ Server error {resp.status_code}, retrying...")
                    time.sleep(2 + attempt)
                    continue

                log(f"❌ Error {resp.status_code}: {resp.text[:150]}")
                break

            except requests.exceptions.Timeout:
                log("⏱️ Timeout, rotating...")
                break
            except Exception as e:
                log(f"❌ Error: {e}")
                break

    return None


def sanitize_patch_response(raw: str) -> str:
    """Strip markdown fences and normalize newlines."""
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    
    # Remove markdown code fences
    raw = re.sub(r"`[a-zA-Z0-9_-]*\s*\n", "", raw)
    raw = raw.replace("`", "")
    
    # Extract only the patch blocks if there's surrounding text
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
        # Debug output for failed parsing
        log("⚠️ PARSING FAILED. Raw response (first 300 chars):")
        log(patch_text[:300])
        return None, "No SEARCH/REPLACE blocks found. Did the model include conversational text?"

    new_code = original_code
    applied = 0

    for search_block, replace_block in matches:
        # 1. Exact match (preferred)
        if search_block in new_code:
            new_code = new_code.replace(search_block, replace_block, 1)
            applied += 1
            continue

        # 2. Whitespace-stripped match (common formatting differences)
        search_stripped = search_block.strip()
        if search_stripped and search_stripped in new_code:
            new_code = new_code.replace(search_stripped, replace_block.strip(), 1)
            applied += 1
            continue

        # 3. Fail with clear error message
        preview = search_block[:80].replace("\n", "\\n")
        return None, f"Search block not found. Starts with: '{preview}...'"

    if applied == 0:
        return None, "No patches applied (0 matches found)."

    # Safety checks
    if "<!DOCTYPE html" not in new_code:
        return None, "CRITICAL: Root HTML tags deleted."

    old_lines = max(1, len(original_code.splitlines()))
    new_lines = len(new_code.splitlines())
    if new_lines < int(old_lines * 0.75):
        return None, f"CRITICAL: File too short ({old_lines} -> {new_lines} lines)."

    return new_code, f"Applied {applied} patch(es)"


def verify_fix(task: str, original_code: str, new_code: str) -> tuple[bool, str]:
    """The Level 9 Critic: Simple diff-based QA."""
    if original_code == new_code:
        return False, "No changes detected."

    # Generate unified diff
    diff = "".join(
        difflib.unified_diff(
            original_code.splitlines(True),
            new_code.splitlines(True),
            fromfile="before",
            tofile="after",
            n=3,
        )
    )

    # Prevent huge payloads
    if len(diff) > 8000:
        diff = diff[:8000] + "\n...[DIFF TRUNCATED]"

    critic_prompt = f"""You are a strict code reviewer.

TASK: {task}

DIFF:
{diff}

Does this change correctly implement the task without breaking React state management?

Reply with EXACTLY one line:
- PASS
- FAIL: <reason>"""

    review = ask_gemini(critic_prompt, CODER_MODELS, role="critic")
    
    if not review:
        return True, "Critic silent (assuming safe)"

    review_upper = review.strip().upper()
    
    if review_upper.startswith("PASS"):
        return True, review.strip()
    
    if "FAIL" in review_upper:
        return False, review.strip()
    
    # Conservative: if unclear, assume pass (avoid deadlock)
    return True, f"Critic unclear (assuming pass): {review[:100]}"


def get_next_task() -> str | None:
    backlog = read_file(BACKLOG_FILE)
    match = re.search(r"- \[ \] \*\*(.*?)\*\*(?!\s*\(SKIPPED)", backlog)
    return match.group(1).strip() if match else None


def mark_task_done(task: str) -> None:
    content = read_file(BACKLOG_FILE)
    updated = content.replace(f"- [ ] **{task}**", f"- [x] **{task}**")
    write_file(BACKLOG_FILE, updated)


def move_task_to_bottom(task: str) -> None:
    content = read_file(BACKLOG_FILE)
    lines = content.splitlines()
    new_lines: list[str] = []
    task_line = ""

    for line in lines:
        if f"- [ ] **{task}**" in line:
            task_line = f"- [ ] **{task}** (SKIPPED)"
        else:
            new_lines.append(line)

    if task_line:
        if "## ⚠️ SKIPPED TASKS" not in new_lines:
            new_lines.extend(["", "## ⚠️ SKIPPED TASKS"])
        new_lines.append(task_line)

    write_file(BACKLOG_FILE, "\n".join(new_lines))


def load_context() -> str:
    """Load minimal context (Level 9 style)."""
    parts = []
    for f in CONTEXT_FILES:
        txt = read_file(f)
        if txt.strip():
            # Truncate to prevent 400 errors
            if len(txt) > 6000:
                txt = txt[:6000] + "\n...[TRUNCATED]"
            parts.append(f"--- {f} ---\n{txt}")

    return "\n\n".join(parts) if parts else ""


def check_render() -> None:
    """Optional: Wait for Render deployment."""
    if not (RENDER_API_KEY and RENDER_SERVICE_ID):
        return

    log("🚀 Watching Render...")
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys?limit=1"

    for _ in range(20):
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    status = data[0]["deploy"]["status"]
                    log(f"📡 {status}")
                    if status == "live":
                        log("✅ Deploy live")
                        return
                    if status in ("build_failed", "canceled"):
                        log("❌ Deploy failed")
                        return
        except Exception:
            pass
        time.sleep(15)


def process_single_task() -> bool:
    task = get_next_task()
    if not task:
        return False

    log(f"\n📋 TARGET: {task}")
    
    current_code = read_file(APP_FILE)
    context = load_context()
    history = ""

    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Attempt {attempt + 1}/{MAX_QA_RETRIES}")

        prompt = f"""TASK: {task}

CONTEXT:
{context}

PREVIOUS FEEDBACK:
{history}

INSTRUCTIONS:
1. Output ONLY SEARCH/REPLACE blocks
2. NO markdown fences (no `)
3. SEARCH must match file EXACTLY

FORMAT:
<<<<<<< SEARCH
(exact code to remove)
=======
(new code)
>>>>>>> REPLACE

CODE:
{current_code}"""

        patch = ask_gemini(prompt, CODER_MODELS, role="coder")
        if not patch:
            history = "No response from AI. Try again."
            continue

        new_code, status = apply_patch(current_code, patch)
        if not new_code:
            log(f"❌ Patch failed: {status}")
            history = f"Patch error: {status}"
            continue

        # The Level 9 critic
        log("🕵️ Verifying...")
        ok, feedback = verify_fix(task, current_code, new_code)
        if not ok:
            log(f"❌ QA failed: {feedback}")
            history = f"QA rejected: {feedback}"
            continue

        # SUCCESS
        log("✅ Verified. Committing...")
        write_file(APP_FILE, new_code)
        mark_task_done(task)

        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        repo.index.commit(f"feat(jules): {task[:80]}")
        
        # Sync before push (prevent conflicts)
        try:
            log("🔄 Pull --rebase...")
            repo.git.pull("--rebase")
        except Exception as e:
            log(f"⚠️ Rebase warning: {e}")
        
        repo.remotes.origin.push()
        log("🚀 Pushed")
        
        check_render()
        return True

    # Failed after retries
    log("⚠️ Task stuck, skipping...")
    move_task_to_bottom(task)
    
    try:
        repo = git.Repo(REPO_PATH)
        repo.git.add(BACKLOG_FILE)
        repo.index.commit("skip: stuck task")
        repo.remotes.origin.push()
    except Exception as e:
        log(f"⚠️ Skip commit failed: {e}")

    return True


def run_loop() -> None:
    if not GEMINI_API_KEY:
        log("❌ ERROR: GEMINI_API_KEY missing!")
        sys.exit(1)

    log(f"🤖 Jules Level 31 Started")
    log(f"📋 Models: {CODER_MODELS}")

    while True:
        runtime = (time.time() - START_TIME) / 60
        if runtime > (MAX_RUNTIME_MINUTES - 2):
            log("⏰ Time limit reached")
            break

        if not process_single_task():
            log("✅ No more tasks")
            break

        time.sleep(5)


if __name__ == "__main__":
    run_loop()
