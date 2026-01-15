# 🤖 Tytax Elite Autonomous Agent: System Architecture & Recreation Guide

This document provides a comprehensive blueprint of the autonomous coding ecosystem ("Jules") built for the Tytax Elite Companion project. This system independently implements features, verifies logic, and manages production deployments.

## 1. System Philosophy: The Recursive Loop
The system is designed as a **self-triggering loop**. Unlike standard automation, Jules uses a Personal Access Token (PAT) to perform git operations, which GitHub interprets as an external user action, thereby allowing it to re-trigger the workflow for the next task automatically.

### High-Level Execution Flow:
1. **Backlog Entry:** A user appends a task to `BACKLOG.md` (e.g., `- [ ] **Task Name**`).
2. **Trigger:** A push to the backlog triggers the GitHub Action workflow.
3. **Task Selection:** `jules.py` scans for the first open checkbox `[ ]`.
4. **AI Generation:** The "Coder" AI (Gemini 3 Pro) reviews the current code and writes a patch using `SEARCH/REPLACE` blocks.
5. **QA Review:** A "Critic" AI reviews the generated diff for syntax errors or logic breaks.
6. **Aggressive Sync:** Before saving, Jules executes a `pull --rebase` to merge any manual edits made during the AI's 10-minute thinking window.
7. **Recursive Push:** Jules pushes the completed task. This push triggers a *new* workflow run immediately.
8. **Deployment Gate:** The system waits for Render to confirm the site is stable before clearing the task.

## 2. Production Stability (Render Monitor)
A unique feature of this system is the **Render API Handshake**:
- **Health Verification:** Jules polls the Render API (`/deploys`) using a secure API Key.
- **Status Check:** It specifically monitors for the `live` status signal.
- **Circuit Breaker:** If Render reports a `build_failed`, `canceled`, or any non-200 status, Jules halts the loop and reports the error in the GitHub Action log. This prevents the AI from implementation more code on top of a broken production build.

## 3. Core Component Requirements

### A. Security & Keys (GitHub Secrets)
To recreate this, three secrets must be added to the GitHub repository:
- **`GEMINI_API_KEY`**: Powers the AI's coding and critic logic.
- **`RENDER_API_KEY`**: Enables the deployment monitoring gate.
- **`MY_PAT_TOKEN`**: A Personal Access Token (classic) with `repo` and `workflow` scopes. **Note:** The default `GITHUB_TOKEN` will not work as it is restricted from triggering recursive runs.

### B. Safety Mechanisms
- **Concurrency Lock:** Defined in the YAML to ensure only one Jules instance runs at a time, preventing race conditions.
- **Fail-Forward Logic:** If Jules fails to patch a specific task after 3 attempts, it moves that task to the bottom of the backlog to prevent a "system jam".
- **Deep Cloning:** All React state updates within the code are implemented using immutable patterns to ensure UI reactivity.

## 4. How to Recreate the Engine
1. **Repo Setup:** Host your `index.html`, `requirements.txt`, and `BACKLOG.md` in a private GitHub repo.
2. **Workflow Configuration:** Create `.github/workflows/jules_autonomous.yml` with the concurrency block and PAT checkout.
3. **Orchestrator Setup:** Upload `jules.py` which uses the `gitpython` library for rebase management.
4. **Activation:** Push your first task to the backlog. The system will now run autonomously until all checkboxes are marked `[x]`.

---
*Documentation generated for Tytax Elite Companion System Initialization.*
