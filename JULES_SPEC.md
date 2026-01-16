# Jules Agent Specification (Level 24 - Hybrid Restore)

## 1. The Brain (Restored from Level 9)
- [x] **Primary:** gemini-3-pro-preview (The one that built the Charts).
- [x] **Secondary:** gemini-2.0-flash-exp (The fast backup).
- [x] **Critic:** gemini-3-pro-preview (Uses high intelligence to verify logic).

## 2. The Fixes (Patches for Level 9 Failures)
- [x] **Markdown Stripper:** Removes `html blocks so the parser finds the code.
- [x] **Sanitizer:** Strips whitespace from API keys to prevent connection errors.
- [x] **Task Rotation:** Prevents infinite retry loops on stuck tasks.

## 3. The Logic Loop
- Read Task -> Generate Patch -> Apply (Fuzzy) -> Verify (Diff) -> Push -> Check Render.
