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

### 1. \tytax_logs\ (Array)
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

### 2. \tytax_master_exercises\ (Array)
* **Purpose:** The active library of exercises available to the user.
* **Source:** Injected from \tytax_library.json\.
* **Key Fields:** \name\, \station\ (Smith/Pulley), \muscle_group\, \impact\ (Score 0-100).

### 3. \tytax_user_inventory\ (Array)
* **Purpose:** List of equipment the user *actually owns*.
* **Structure:** \["Triceps Rope", "D-Handles", "Lat Bar"]\
* **Logic:** Used by the Builder to hide exercises requiring missing gear.

## 🔄 Data Flow
1.  **Initialization:** On load, \App\ checks \localStorage\. If empty, it loads \PRESETS\ (default data).
2.  **Active Session:**
    * User selects a session -> \currentWorkout\ state is created (Deep Copy).
    * User logs sets -> State is updated via \structuredClone\ (Critical for React reactivity).
    * **CRITICAL:** No data is saved to \tytax_logs\ until the "Terminate Session" button is clicked.
3.  **Analysis:** The "Trends" tab reads \tytax_logs\ (Read-Only) to generate charts.

## ⚙️ DevOps & Automation Architecture (Level 11 Hybrid)
The application is a self-sustaining ecosystem managed by the \jules.py\ orchestrator.

### 1. The Recursive Loop & RAG Brain
* **Trigger:** Push to \BACKLOG.md\ -> GitHub Action.
* **Context Injection (RAG):** Before coding, the orchestrator reads \AGENTS.md\, \ARCHITECTURE.md\, and \TESTING_PROTOCOL.md\. **Changing these files immediately reprograms the agent.**
* **Concurrency:** Only one agent runs at a time.

### 2. The Hybrid Model Hierarchy
* **Primary (The Architect):** \gemini-3-pro-preview\. Used for complex reasoning and adhering to strict prompt instructions.
* **Secondary (The Engineer):** \gemini-2.0-flash-exp\. Used as a high-speed fallback if the primary model times out.

### 3. Agent Interaction Protocol (Patching Standard)
All code modifications MUST use the following Regex-compatible block format. **Diffs and Git Patches are ignored.**

\<<<<<<< SEARCH\
\[Exact code to remove - must match whitespace exactly]\
\=======\
\[New code to insert]\
\>>>>>>> REPLACE\

* **Rule:** The \SEARCH\ block must be unique. If the code exists in multiple places, include more context lines.

### 4. Safety Gates (Sync & Render)
* **Aggressive Sync:** The system runs \git pull --rebase\ immediately before pushing to prevent "Rejected" errors.
* **Render Circuit Breaker:** The loop polls the Render API. If a build fails (\build_failed\), the Agent **halts** to prevent compounding errors on a broken build.
