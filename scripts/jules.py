import os
import re
import sys
import time
import json
import difflib
import requests
import git
from datetime import datetime

# ==============================================================================
# JULES LEVEL 33 (ROBUST ATOMIC)
# ==============================================================================
# - ATOMIC COMMITS: Never leaves the repo in a dirty state.
# - REBASE SAFETY: Always pulls before pushing. Handles conflicts by skipping.
# - STRICT PATCHING: Enforces SEARCH/REPLACE blocks. No conversational filler.
# - SMART DISCOVERY: Finds the best available models automatically.
# ==============================================================================

# --- CONFIGURATION ---
REPO_PATH = os.environ.get("JULES_REPO_PATH", ".")
# Use absolute paths relative to script location for default fallback
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

APP_FILE = os.path.join(ROOT_DIR, "index.html")
BACKLOG_FILE = os.path.join(ROOT_DIR, "docs/BACKLOG.md") # Moved to docs/
AGENTS_FILE = os.path.join(ROOT_DIR, "docs/AGENTS.md")   # Moved to docs/

# Nuclear Sanitization of Keys
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").replace("\n", "").strip()
RENDER_API_KEY = (os.environ.get("RENDER_API_KEY") or "").replace("\n", "").strip()
RENDER_SERVICE_ID = (os.environ.get("RENDER_SERVICE_ID") or "").replace("\n", "").strip()

MAX_RETRIES = 3
REQUEST_TIMEOUT = 120
START_TIME = time.time()
MAX_RUNTIME_MINUTES = 50

# Priority: Smartest/Fastest -> Reliable -> Backups
MODEL_PRIORITY_REGEX = [
    r"^gemini-2\.0-flash",       # Modern standard
    r"^gemini-1\.5-pro",         # High reasoning
    r"^gemini-1\.5-flash",       # High speed
]

# --- LOGGING ---
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

if not GEMINI_API_KEY:
    log("❌ CRITICAL: GEMINI_API_KEY is missing/empty.")
    sys.exit(1)

# --- GIT HELPER ---
class GitManager:
    def __init__(self, repo_path):
        self.repo = git.Repo(repo_path)
        self.git = self.repo.git

    def is_dirty(self):
        return self.repo.is_dirty(untracked_files=True)

    def reset_hard(self):
        log("🧹 Git: Resetting hard to HEAD...")
        self.git.reset("--hard", "HEAD")
        self.git.clean("-fd")

    def pull_rebase(self):
        log("🔄 Git: Pulling with rebase...")
        try:
            self.git.pull("origin", "main", "--rebase")
        except git.GitCommandError as e:
            log(f"⚠️ Rebase failed: {e}")
            log("🛑 Aborting rebase...")
            self.git.rebase("--abort")
            return False
        return True

    def commit_and_push(self, message, files=None):
        if not files:
            files = ["."]

        # 1. Pull first to minimize conflicts
        if not self.pull_rebase():
            return False

        # 2. Add and Commit
        for f in files:
            self.git.add(f)

        # Check if anything is actually staged
        if not self.repo.index.diff("HEAD"):
            log("⚠️ Git: Nothing to commit.")
            return True

        self.repo.index.commit(message)
        log(f"📦 Git: Committed '{message}'")

        # 3. Push
        try:
            self.git.push("origin", "main")
            log("🚀 Git: Push successful.")
            return True
        except Exception as e:
            log(f"❌ Git: Push failed: {e}")
            return False

# --- API CLIENT ---
def discover_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200: return []

        valid = []
        for m in resp.json().get('models', []):
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                valid.append(m['name'].replace('models/', ''))

        ranked = []
        for pattern in MODEL_PRIORITY_REGEX:
            ranked.extend([m for m in valid if re.search(pattern, m)])

        # Dedup keeping order
        seen = set()
        final = []
        for m in ranked:
            if m not in seen:
                final.append(m)
                seen.add(m)

        log(f"🧠 Models Discovered: {final[:3]}...")
        return final
    except: return []

def ask_gemini(prompt, models, role="coder"):
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.1}
    }

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        for _ in range(2): # 2 attempts per model
            try:
                log(f"💬 [{role.upper()}] Asking {model}...")
                resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    try:
                        text = resp.json()['candidates'][0]['content']['parts'][0]['text']
                        return text
                    except: pass
                elif resp.status_code == 429:
                    log(f"⏳ Rate Limited ({model}). Waiting 5s...")
                    time.sleep(5)
                else:
                    log(f"⚠️ Error {resp.status_code} ({model})")
                    break # Next model
            except Exception as e:
                log(f"❌ Net Error: {e}")
                break
    return None

# --- PATCH ENGINE ---
def apply_patch(original, patch_text):
    # Strip markdown code blocks
    clean = re.sub(r'^`{3,}.*$', '', patch_text, flags=re.MULTILINE).strip()

    # Regex to find blocks
    # We look for <<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE
    # We use non-greedy matching .*? with DOTALL
    blocks = re.findall(
        r"<<<<<<< SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE",
        clean,
        re.DOTALL
    )
    
    if not blocks:
        return None, "No valid SEARCH/REPLACE blocks found."

    new_code = original
    matches = 0
    
    for search, replace in blocks:
        # 1. Exact Match
        if search in new_code:
            new_code = new_code.replace(search, replace, 1)
            matches += 1
            continue

        # 2. Trimmed Match
        if search.strip() in new_code:
            new_code = new_code.replace(search.strip(), replace.strip(), 1)
            matches += 1
            continue

        # 3. Fuzzy Match (Fallback)
        # Only if block is substantial to avoid false positives
        if len(search) > 50:
            matcher = difflib.SequenceMatcher(None, new_code, search)
            m = matcher.find_longest_match(0, len(new_code), 0, len(search))
            # If we matched > 80% of the search block
            if m.size / len(search) > 0.80:
                # Replace the matched section
                new_code = new_code[:m.a] + replace + new_code[m.a + m.size:]
                matches += 1
                continue

    if matches == 0:
        return None, "No blocks matched the original code."

    return new_code, f"Applied {matches} patches."

# --- WORKFLOW ---
def process_task(git_mgr, models):
    # 1. Read Backlog
    try:
        with open(BACKLOG_FILE, 'r', encoding='utf-8') as f:
            backlog = f.read()
    except:
        log("❌ Could not read BACKLOG.md")
        return False

    # Find next task (not checked, not skipped)
    # Format: - [ ] **Task Name**: Description
    # We ignore lines with (SKIPPED)
    # Regex captures: Group 1 (Title), Group 2 (Description - Optional)
    match = re.search(r'- \[ \] \*\*(.*?)\*\*(?::\s*(.*))?(?!\s*\(SKIPPED)', backlog)

    if not match:
        log("✅ No pending tasks found.")
        return False

    task_title = match.group(1).strip()
    task_desc = (match.group(2) or "").strip()
    full_task = f"{task_title}: {task_desc}" if task_desc else task_title

    log(f"📋 TARGET: {task_title}")

    # 2. Determine Target File & Read Code
    target_file = APP_FILE
    # Simple heuristic for file targeting (can be expanded)
    if "css" in task_title.lower() or "style" in task_title.lower():
        if "css/" in full_task: target_file = "css/styles.css"
    elif "js" in task_title.lower() or "script" in task_title.lower():
        if "js/" in full_task: target_file = "js/components.js"
        
    # Ensure directory exists if targeting non-root
    if "/" in target_file:
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

    try:
        if os.path.exists(target_file):
            with open(target_file, 'r', encoding='utf-8') as f:
                code = f.read()
        else:
            code = "" # New file creation
            log(f"🆕 Creating new file: {target_file}")
    except:
        log(f"❌ Could not read {target_file}")
        return False
        
    context = ""
    if os.path.exists(AGENTS_FILE):
        with open(AGENTS_FILE, "r") as f: context += f.read()

    # 3. Attempt Loop
    success = False

    for attempt in range(MAX_RETRIES):
        log(f"💡 Attempt {attempt+1}/{MAX_RETRIES}...")
        
        prompt = f"""
ROLE: Senior React Engineer.
TASK: {full_task}
CONTEXT: {context[:5000]}

INSTRUCTIONS:
1. You are modifying '{target_file}'.
2. Output ONLY SEARCH/REPLACE blocks.
3. DO NOT wrap output in Markdown code fences (```).
4. The SEARCH block must match the existing code EXACTLY.

FORMAT:
(exact lines to remove)

CODE:
{code}
"""
        # Call AI
        patch = ask_gemini(prompt, models, role="coder")
        if not patch:
            log("❌ AI returned no response.")
            continue

        # Apply Patch
        new_code, msg = apply_patch(code, patch)
        if not new_code:
            log(f"❌ Patch failed: {msg}")
            continue

        # Verification (Simple Diff Check)
        # Allow empty new code only if file was empty (creation)
        if new_code == code and len(code) > 0:
            log("❌ Patch resulted in no changes.")
            continue

        # Check for catastrophic deletion (skip for small files)
        if len(code) > 1000 and len(new_code) < len(code) * 0.75:
            log("❌ Safety: Code shrank too much.")
            continue

        # SUCCESS PATH
        log(f"✅ Patch applied: {msg}")

        # Write File
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_code)

        # Update Backlog
        new_backlog = backlog.replace(f"- [ ] **{task_title}**", f"- [x] **{task_title}**")
        with open(BACKLOG_FILE, 'w', encoding='utf-8') as f:
            f.write(new_backlog)

        # Commit
        if git_mgr.commit_and_push(f"feat: {task_title} (Jules v33)", files=[target_file, BACKLOG_FILE]):
            success = True

            # Check Render (Optional)
            if RENDER_API_KEY:
                log("🚀 Checking Render...")
                # (Simplified check - just fire and forget usually, but we'll wait 5s)
                time.sleep(5)

            break
        else:
            log("❌ Commit/Push failed. Reverting...")
            git_mgr.reset_hard() # Undo changes to try again or fail cleanly
            break

    # 4. Failure Handling
    if not success:
        log(f"⚠️ Task '{task_title}' failed after {MAX_RETRIES} attempts.")
        # Revert any local file changes first
        git_mgr.reset_hard()

        # Mark as Skipped in Backlog
        # We need to re-read backlog in case it changed (unlikely with reset, but safe)
        with open(BACKLOG_FILE, 'r') as f: current_bl = f.read()

        # Add (SKIPPED) tag
        skipped_line = f"- [ ] **{task_title}** (SKIPPED: Stuck)"
        new_bl = current_bl.replace(f"- [ ] **{task_title}**", skipped_line)

        # Move to bottom
        lines = new_bl.splitlines()
        final_lines = [line for line in lines if skipped_line not in line]
        if "## ⚠️ SKIPPED TASKS" not in final_lines:
            final_lines.extend(["", "## ⚠️ SKIPPED TASKS"])
        final_lines.append(skipped_line)

        with open(BACKLOG_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(final_lines))

        git_mgr.commit_and_push(f"skip: {task_title} (Stuck)")

    return True # Always return True to continue loop (unless no tasks found)

def main():
    log("🤖 Jules Level 33 (Atomic) Starting...")

    # 1. Setup Git
    git_mgr = GitManager(REPO_PATH)

    # 2. Ensure Clean State
    if git_mgr.is_dirty():
        log("⚠️ Repo is dirty. Resetting hard...")
        git_mgr.reset_hard()

    # 3. Discover Models
    models = discover_models()
    if not models:
        log("⚠️ Auto-discovery failed. Using fallback.")
        models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        
    # 4. Main Loop
    while True:
        # Check runtime
        if (time.time() - START_TIME) / 60 > MAX_RUNTIME_MINUTES:
            log("⏰ Time limit reached.")
            break

        # Run Task
        has_more = process_task(git_mgr, models)
        if not has_more:
            break

        time.sleep(2)

if __name__ == "__main__":
    main()
