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
