# ARCHITECTURE.md
## 📂 Project Structure (Single-File React)
Currently, the application uses a **Single-File Component** architecture for maximum portability (\index.html\).
*Note: We are in the process of migrating to a standard Vite build (See Backlog), but current tasks must respect the \index.html\ structure.*

\\\	ext
/
├── index.html          # THE CORE. Contains React, Babel, Tailwind via CDN.
├── tytax_library.json  # The "Brain" of the app. 100+ Exercise Database.
├── assets/             # Images/Icons (if external)
├── AGENTS.md           # Your Instructions
├── ARCHITECTURE.md     # This File
└── BACKLOG.md          # Your Task List
\\\

## 💾 Data Schema (Local Storage)
The app persists state in the browser's \localStorage\ using specific keys.

### 1. \	ytax_logs\ (Array)
* **Purpose:** Stores completed workout sessions.
* **Structure:**
    \\\json
    [
      {
        "id": "uuid-v4",
        "date": "2023-10-27",
        "session": "Upper A",
        "duration": 3600, // Seconds
        "volume": 15400,  // Total KG
        "rpe": 8,
        "notes": "Felt strong on bench.",
        "exercises": [ ... ] // Detailed set data
      }
    ]
    \\\

### 2. \	ytax_master_exercises\ (Array)
* **Purpose:** The active library of exercises available to the user.
* **Source:** Injected from \	ytax_library.json\.
* **Key Fields:** \
ame\, \station\ (Smith/Pulley), \muscle_group\, \impact\ (Score 0-100).

### 3. \	ytax_user_inventory\ (Array)
* **Purpose:** List of equipment the user *actually owns*.
* **Structure:** \["Triceps Rope", "D-Handles", "Lat Bar"]\
* **Logic:** Used by the Builder to hide exercises requiring missing gear.

## 🔄 Data Flow
1.  **Initialization:** On load, \App\ checks \localStorage\. If empty, it loads \PRESETS\ (default data).
2.  **Active Session:**
    * User selects a session -> \currentWorkout\ state is created (Deep Copy).
    * User logs sets -> State is updated via \structuredClone\ (Critical for React reactivity).
    * **CRITICAL:** No data is saved to \	ytax_logs\ until the "Terminate Session" button is clicked.
3.  **Analysis:** The "Trends" tab reads \	ytax_logs\ (Read-Only) to generate charts.

## ⚙️ DevOps & Automation Architecture (Jules Level 11)
The application is maintained by an autonomous loop ("Jules") with specific environmental awareness.

### 1. The Recursive Loop
* **Trigger:** Push to BACKLOG.md -> GitHub Action.
* **Execution:** jules.py runs -> Commits Code -> Pushes -> Triggers Self.
* **Concurrency:** Only one agent runs at a time (concurrency: group: jules-agent-loop).

### 2. The Deployment Gate (Render)
* **Live Monitoring:** The system queries the Render API (/services/{id}/deploys).
* **Stop Signal:** If a deploy fails (uild_failed), the agent **halts**. It will not attempt new tasks until the build is green.
* **Latency:** Deployment typically takes 90-120 seconds. The agent sleeps/polls during this window.

### 3. Aggressive Sync Strategy
* To prevent "Push Rejected" errors in the recursive loop, the agent performs a git pull --rebase immediately before pushing.
* **Rule:** All file writes (index.html) must happen *before* the final rebase to minimize conflict windows.

## 🤖 Agent Interaction Protocol
Since the system is autonomous, all code modifications must adhere to strict machine-readable standards to ensure the jules.py orchestrator can parse them.

### 1. The Patching Standard (Search/Replace)
Do **not** output full files. You must use the following block format to modify code. The orchestrator uses Regex to apply these patches.

<<<<<<< SEARCH
[Exact code to remove - must match whitespace exactly]
=======
[New code to insert]
>>>>>>> REPLACE

* **Rule:** The SEARCH block must be unique. If the code exists in multiple places, include more context lines.
* **Rule:** Do not use diff or git patch formats. Use the custom block above.

### 2. DevOps Architecture
The application is maintained by an autonomous loop with specific environmental awareness.

* **Orchestrator:** A Python script (jules.py) that manages the 'Think -> Code -> Deploy' loop.
* **Context Injection (RAG):** The orchestrator reads AGENTS.md and ARCHITECTURE.md before every task. Updates to these files immediately change the agent's behavior.
* **Aggressive Sync:** The system performs a git pull --rebase before every push to prevent conflict loops.
* **Render Gate:** The loop pauses and polls the Render API. If a build fails, the agent halts to prevent compounding errors.
