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
# Goals:
# - Bring back Level 9 reliability: strict patching + Critic PASS/FAIL QA.
# - Keep modern safety: API key sanitization + skip stuck tasks.
# - Keep auto-discovery but with correct prioritization (Gemini 3 first).

REPO_PATH = os.environ.get("JULES_REPO_PATH", ".")
APP_FILE = os.environ.get("JULES_APP_FILE", "index.html")
BACKLOG_FILE = os.environ.get("JULES_BACKLOG_FILE", "BACKLOG.md")

def _clean_env(name: str, default: str = "") -> str:
    raw = os.environ.get(name, default)
    return (raw or "").replace("\n", "").replace("\r", "").strip()

GEMINI_API_KEY = _clean_env("GEMINI_API_KEY")
RENDER_API_KEY = _clean_env("RENDER_API_KEY")
RENDER_SERVICE_ID = _clean_env("RENDER_SERVICE_ID") or "srv-d5jlon15pdvs739hp3jg"  # fallback to known id
SITE_URL = _clean_env("SITE_URL") or "https://tytax-elite.onrender.com"

MAX_QA_RETRIES = int(_clean_env("MAX_QA_RETRIES", "4") or 4)
MAX_RUNTIME_MINUTES = int(_clean_env("MAX_RUNTIME_MINUTES", "45") or 45)
REQUEST_TIMEOUT = int(_clean_env("REQUEST_TIMEOUT", "90") or 90)
START_TIME = time.time()

# If you ever want fuzzy patching, set env JULES_FUZZY=1
ENABLE_FUZZY_PATCH = (_clean_env("JULES_FUZZY", "0") == "1")

# Minimal context keeps prompts small (Level 9 style)
DEFAULT_CONTEXT_FILES = ["AGENTS.md", "ARCHITECTURE.md"]
CONTEXT_FILES = [
    f.strip() for f in (_clean_env("JULES_CONTEXT_FILES", ",".join(DEFAULT_CONTEXT_FILES))).split(",") if f.strip()
]

# Manual override (comma-separated). Example:
# JULES_MODELS="gemini-3-pro-preview,gemini-2.0-flash-exp,gemini-1.5-pro"
MANUAL_MODELS = [m.strip() for m in _clean_env("JULES_MODELS", "").split(",") if m.strip()]
# Optional separate critic stack (comma-separated). If empty, critic uses same stack as coder.
MANUAL_CRITIC_MODELS = [m.strip() for m in _clean_env("JULES_CRITIC_MODELS", "").split(",") if m.strip()]


# Hard fallback (matches your last known good stack + common canon names)
STATIC_FALLBACK_MODELS = [
    "gemini-3-pro-preview",
    "gemini-3-flash-preview",
    "gemini-3.0-pro-preview",
    "gemini-3.0-flash-preview",
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
]

# Auto-discovery ranking: smartest -> fastest -> fallbacks
PRIORITY_PATTERNS = [
    r"^gemini-3\\.",
    r"^gemini-3-",  # gemini-3-pro-preview, gemini-3-flash-preview
    r"^gemini-2\\.5\\.",
    r"^gemini-2\\.5-",
    r"^gemini-2\\.0\\.",
    r"^gemini-2\\.0-",
    r"^gemini-1\\.5-pro$",
    r"^gemini-1\\.5-pro-",
    r"^gemini-1\\.5-flash$",
    r"^gemini-1\\.5-flash-",
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
    """Queries the Gemini Models API and returns a ranked list."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        log("🔍 Auto-discovering available models...")
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            log(f"❌ Discovery failed: {resp.status_code} - {resp.text[:200]}...")
            return []

        data = resp.json()
        valid = []
        for m in data.get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                name = (m.get("name") or "").replace("models/", "")
                if name:
                    valid.append(name)

        # Rank using patterns
        ranked: list[str] = []
        for pat in PRIORITY_PATTERNS:
            rx = re.compile(pat)
            ranked.extend([m for m in valid if rx.search(m)])

        # Add remaining gemini* models as last resort
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
        log(f"🧩 Using JULES_MODELS override: {MANUAL_MODELS}")
        return _dedupe(MANUAL_MODELS + STATIC_FALLBACK_MODELS)

    discovered = discover_models()
    if discovered:
        # Keep discovery first, but always append fallbacks (deduped)
        return _dedupe(discovered + STATIC_FALLBACK_MODELS)

    log("⚠️ Discovery returned no models; using static fallback stack.")
    return _dedupe(STATIC_FALLBACK_MODELS)

def pick_critic_models(coder_models: list[str]) -> list[str]:
    if MANUAL_CRITIC_MODELS:
        log(f"🧪 Using JULES_CRITIC_MODELS override: {MANUAL_CRITIC_MODELS}")
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

    # Try each model with small retries; rotate quickly on 404/429
    for model in model_list:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        for attempt in range(3):
            try:
                log(f"🔄 [{role.upper()}] {model} (Attempt {attempt+1}/3)")
                resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)

                if resp.status_code == 200:
                    text = extract_text_from_response(resp.json())
                    if text:
                        log(f"📥 [200 OK] Response received: {len(text)} chars")
                        return text
                    log("⚠️ [200 OK] Empty text payload; rotating...")
                    break

                if resp.status_code == 429:
                    # small backoff then rotate
                    log("⏳ [429 Rate Limit] Waiting 5s then rotating...")
                    time.sleep(5)
                    break

                if resp.status_code in (401, 403):
                    log(f"🛑 Auth error {resp.status_code}. Check GEMINI_API_KEY.")
                    return None

                if resp.status_code in (404,):
                    log(f"🚫 Model not found (404): {model}. Rotating...")
                    break

                # transient server errors
                if resp.status_code in (500, 502, 503, 504):
                    wait = 2 + attempt * 2
                    log(f"⚠️ Server error {resp.status_code}. Waiting {wait}s...")
                    time.sleep(wait)
                    continue

                # other errors: log and rotate
                log(f"❌ API Error {resp.status_code}: {resp.text[:200]}...")
                break

            except requests.exceptions.Timeout:
                log("⏱️ Request timed out; rotating...")
                break
            except Exception as e:
                log(f"❌ Network/Runtime error: {e}")
                break

    return None


def _strip_code_fences(text: str) -> str:
    # Remove triple-backtick fences while keeping the contents
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
        return None, "No valid SEARCH/REPLACE blocks found. (Did the model include extra text or wrong markers?)"

    new_code = original_code
    applied = 0

    for search_block, replace_block in matches:
        # Exact match first
        idx = new_code.find(search_block)
        if idx != -1:
            new_code = new_code.replace(search_block, replace_block, 1)
            applied += 1
            log("✅ Found exact match for block.")
            continue

        # Whitespace-stripped match
        s = search_block.strip()
        if s and s in new_code:
            new_code = new_code.replace(s, replace_block.strip(), 1)
            applied += 1
            log("✅ Found whitespace-stripped match.")
            continue

        # Optional fuzzy match (off by default)
        if ENABLE_FUZZY_PATCH and len(search_block) >= 80:
            log("⚠️ Exact match failed; attempting fuzzy match...")
            matcher = difflib.SequenceMatcher(None, new_code, search_block)
            match = matcher.find_longest_match(0, len(new_code), 0, len(search_block))
            if match.size > 0:
                found = new_code[match.a : match.a + match.size]
                ratio = difflib.SequenceMatcher(None, found, search_block).ratio()
                if ratio >= 0.92:
                    new_code = new_code[:match.a] + replace_block + new_code[match.a + match.size :]
                    applied += 1
                    log(f"✅ Fuzzy match applied (score {ratio:.2f}).")
                    continue
            return None, "Search block mismatch (fuzzy failed)."

        return None, f"Search block mismatch. Starts with: {search_block[:80].replace(chr(10), ' ')}..."

    if applied == 0:
        return None, "No patches applied (0 matches)."

    # Basic safety: doctype should never vanish
    if "<!DOCTYPE html" not in new_code:
        return None, "CRITICAL: <!DOCTYPE html> missing after patch (likely wrong match)."

    # Safety: avoid accidental massive deletion
    old_lines = max(1, len(original_code.splitlines()))
    new_lines = len(new_code.splitlines())
    if new_lines < int(old_lines * 0.70):
        return None, f"CRITICAL: File shrank too much ({old_lines} -> {new_lines} lines)."

    return new_code, f"Applied {applied} patch(es)."


def verify_fix(task: str, original_code: str, new_code: str, model_list: list[str]) -> tuple[bool, str]:
    if original_code == new_code:
        return False, "No changes detected."

    diff = "".join(
        difflib.unified_diff(
            original_code.splitlines(True),
            new_code.splitlines(True),
            fromfile="before",
            tofile="after",
            n=3,
        )
    )

    # Prevent very large payloads
    if len(diff) > 12000:
        diff = diff[:12000] + "\n...DIFF TRUNCATED..."

    critic_prompt = (
        "You are a strict QA reviewer for a production React single-file app (index.html).\n"
        f"TASK: {task}\n\n"
        "Review the diff below.\n"
        "Reply with EXACTLY one line:\n"
        "- PASS\n"
        "- FAIL: <short reason>\n\n"
        f"DIFF:\n{diff}"
    )

    review = ask_gemini(critic_prompt, model_list, role="critic")
    if not review:
        return True, "Critic silent (treating as PASS)."

    up = review.strip().upper()
    if up.startswith("PASS"):
        return True, review.strip()
    if "FAIL" in up:
        return False, review.strip()

    # If critic rambles, be conservative unless it clearly says PASS
    if "PASS" in up:
        return True, review.strip()
    return False, f"Critic unclear: {review.strip()[:200]}"


def get_next_task() -> str | None:
    backlog = read_file(BACKLOG_FILE)
    # Ignore already skipped tasks
    match = re.search(r"- \[ \] \*\*(.*?)\*\*(?!\s*\(SKIPPED)", backlog)
    return match.group(1).strip() if match else None


def mark_task_done(task: str) -> None:
    content = read_file(BACKLOG_FILE)
    updated = content.replace(f"- [ ] **{task}**", f"- [x] **{task}**")
    write_file(BACKLOG_FILE, updated)


def move_task_to_bottom(task: str, reason: str) -> None:
    content = read_file(BACKLOG_FILE)
    lines = content.splitlines()
    new_lines: list[str] = []
    task_line = ""

    for line in lines:
        if f"- [ ] **{task}**" in line:
            task_line = f"- [ ] **{task}** (SKIPPED: {reason})"
        else:
            new_lines.append(line)

    if not task_line:
        return

    heading = "## ⚠️ SKIPPED TASKS"
    if heading in new_lines:
        new_lines.append(task_line)
    else:
        new_lines.append("")
        new_lines.append(heading)
        new_lines.append(task_line)

    write_file(BACKLOG_FILE, "\n".join(new_lines))


def load_context() -> str:
    parts = []
    for f in CONTEXT_FILES:
        txt = read_file(f)
        if txt.strip():
            parts.append(f"\n--- {f} ---\n{txt}\n")

    ctx = "\n".join(parts).strip()

    # Trim context to avoid 400 errors
    max_len = 8000
    if len(ctx) > max_len:
        ctx = ctx[:max_len] + "\n...CONTEXT TRUNCATED..."

    return ctx


def wait_for_render_deploy() -> bool:
    if not (RENDER_API_KEY and RENDER_SERVICE_ID):
        return True

    log("🚀 Monitoring Render deployment...")
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys?limit=1"

    for _ in range(20):
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    status = data[0]["deploy"]["status"]
                    log(f"📡 Render Status: {status}")
                    if status == "live":
                        return True
                    if status in ("build_failed", "canceled"):
                        return False
        except Exception:
            pass
        time.sleep(15)

    return True


def git_sync_and_push(repo: git.Repo) -> bool:
    try:
        # Avoid race conditions: rebase onto remote before pushing
        log("🔄 Pull --rebase (pre-push sync)...")
        try:
            repo.git.pull("--rebase")
        except Exception as e:
            log(f"⚠️ Pull --rebase failed (continuing): {e}")

        repo.remotes.origin.push()
        log("🚀 Pushed to GitHub.")
        return True
    except Exception as e:
        log(f"❌ Push failed: {e}")
        return False


def process_single_task(model_list: list[str]) -> bool:
    task = get_next_task()
    if not task:
        return False

    log(f"\n📋 TARGET: {task}")
    current_code = read_file(APP_FILE)
    context = load_context()
    history = ""

    for attempt in range(MAX_QA_RETRIES):
        log(f"💡 Coder Attempt {attempt + 1}/{MAX_QA_RETRIES}...")

        prompt = (
            "You are an expert React developer editing a SINGLE-FILE app (index.html).\n"
            f"TASK: {task}\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"PREVIOUS_FEEDBACK:\n{history}\n\n"
            "IMPORTANT OUTPUT RULES:\n"
            "1) Output ONLY one or more SEARCH/REPLACE blocks.\n"
            "2) Do NOT wrap in Markdown. No ` fences.\n"
            "3) SEARCH blocks must match the file EXACTLY (including whitespace).\n\n"
            "FORMAT:\n"
            "<<<<<<< SEARCH\n"
            "(exact code to remove)\n"
            "=======\n"
            "(new code to insert)\n"
            ">>>>>>> REPLACE\n\n"
            f"CODE:\n{current_code}"
        )

        patch = ask_gemini(prompt, model_list, role="coder")
        if not patch:
            history = "Coder produced no response. Try a smaller, more surgical patch."
            continue

        new_code, status = apply_patch(current_code, patch)
        if not new_code:
            log(f"❌ Patch failed: {status}")
            history = f"Patch failed: {status}. Ensure SEARCH blocks match exactly and do not include Markdown."
            continue

        critic_models = pick_critic_models(model_list)

        log("🕵️ Critic verifying logic...")
        ok, feedback = verify_fix(task, current_code, new_code, critic_models)
        if not ok:
            log(f"❌ QA failed: {feedback}")
            history = f"QA REJECTED: {feedback}. Fix the issue and re-emit correct SEARCH/REPLACE blocks."
            continue

        # SUCCESS
        log("✅ QA PASSED. Committing...")
        write_file(APP_FILE, new_code)
        mark_task_done(task)

        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)

        safe_task = re.sub(r"\s+", " ", task).strip()
        msg = f"feat(jules): {safe_task}"
        if len(msg) > 120:
            msg = msg[:117] + "..."

        repo.index.commit(msg)

        if not git_sync_and_push(repo):
            return True  # keep loop alive; next run may succeed

        if wait_for_render_deploy():
            log("🎉 Deploy looks OK.")
        else:
            log("🚨 Deploy failed on Render (build_failed/canceled).")

        return True

    # Failed after retries
    log("⚠️ Task stuck. Moving to bottom.")
    move_task_to_bottom(task, reason="Max retries")

    try:
        repo = git.Repo(REPO_PATH)
        repo.git.add(BACKLOG_FILE)
        repo.index.commit("skip: stuck task")
        git_sync_and_push(repo)
    except Exception as e:
        log(f"⚠️ Could not commit skip marker: {e}")

    return True


def run_loop() -> None:
    if not GEMINI_API_KEY:
        log("❌ ERROR: GEMINI_API_KEY missing!")
        sys.exit(1)

    model_list = pick_models()
    if not model_list:
        log("🛑 No models available.")
        sys.exit(1)

    log("🤖 Jules Level 31 (MASTER RESTORE v2) Started...")

    while True:
        # Respect GitHub Actions time limits
        runtime_min = (time.time() - START_TIME) / 60
        if runtime_min > (MAX_RUNTIME_MINUTES - 2):
            log("⏰ Approaching runtime limit. Exiting.")
            break

        progressed = process_single_task(model_list)
        if not progressed:
            log("✅ No more tasks.")
            break

        time.sleep(5)


if __name__ == "__main__":
    run_loop()
