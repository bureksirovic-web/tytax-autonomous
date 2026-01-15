# 🗺️ Product Roadmap & Strategic Vision

This document stores long-term ideas, architectural decisions, and feature concepts that are not yet active in the BACKLOG.md.

---

## 👨‍👩‍👧‍👦 Phase 2: The "Family Fleet" Ecosystem
**Goal:** Enable multi-user support without building a complex login system or backend.

### 1. The Deployment Strategy (Parallel Universes)
Instead of one app with logins, we deploy separate instances for each family member on Render.
* **Infrastructure:**
    * 	ytax-dad.onrender.com (Linked to main branch)
    * 	ytax-mom.onrender.com (Linked to main branch)
    * 	ytax-son.onrender.com (Linked to main branch)
* **Benefit:** Shared codebase (features update for everyone), but isolated data (localStorage is domain-specific).

### 2. The "Master Clone" Onboarding (No-Code Setup)
How to set up a family member without typing 50 exercises on their phone:
* **Step 1 (Admin):** You build the perfect "Starter Routine" (e.g., *Dad - Intro A*) on your app.
* **Step 2 (Export):** You click "Export Profile" in Settings (creates 	ytax_profile.json).
* **Step 3 (Import):** Send file to Dad. He clicks "Import Profile" on his link.
* **Result:** His app is instantly populated with your curated routines, but his logs remain empty/private.

### 3. Data Sovereignty (Backup/Restore)
Since data lives in the browser, we need insurance against lost phones.
* **Feature:** JSON Export/Import in Settings.
* **Rule:** Family members should "Backup" once a month to iCloud/Google Drive.

---

## 🏗️ Phase 3: Architectural Evolution

### 1. The "Single-File" vs. "Vite Bundle" Decision
**Current Status:** Single-File (index.html).
**Verdict:** **KEEP CURRENT SETUP.**

* **Why?**
    * **AI Efficiency:** Jules performs best when it can read the entire context in one file. Splitting into 40+ files introduces "Context Blindness" and dependency errors.
    * **Stability:** No 
pm install or build pipelines to break.
* **Trigger for Migration:**
    * File size exceeds 20,000 lines.
    * Jules starts consistently timing out during reads.
    * We hire a human developer to manage a CI/CD pipeline.

---

## 🎨 Future UX Concepts (The "Nice to Haves")

### 1. Advanced Analytics
* **Muscle Balance Radar:** A spider chart showing "Push vs. Pull" or "Quad vs. Hamstring" volume to prevent injury.
* **1RM Estimator:** Using the Brzycki formula to auto-calculate theoretical maxes based on sub-maximal work (e.g., 10 reps @ 80kg = ~106kg Max).

### 2. The "Gamified" Debrief
* **Concept:** Make finishing a workout feel like a video game victory.
* **Features:**
    * "New High Score" badges if volume > last session.
    * "Streak Counter" (Days in a row).
    * One-tap "Mood Tags" (Strong, Tired, Fast) instead of typing logs.

### 3. Smart "Ghost Mode"
* **Concept:** When repeating a session, pre-fill inputs with *last session's* numbers but faded (opacity 50%).
* **Logic:** Typing over them confirms the lift. If you beat the number, text turns Green (Progressive Overload).


---

## 🔧 Phase 4: Tytax Hardware Integration (The "Digital Manual")
**Goal:** The Tytax T1 is complex to set up. The app should guide the family on *how* to configure the machine, not just *what* to lift.

### 1. "Setup Cues" in Exercise Data
* **Problem:** Family member sees "Incline Bench Press" but doesn't know which hole to put the bench pin in.
* **Solution:** Add a setup_code field to the 	ytax_library.json.
* **UI:** Display small badges on the exercise card: [Bench: 45°] [Arms: B-3] [Cable: Low].
* **Implementation:** You (Admin) add these codes once in the JSON library; everyone sees them forever.

### 2. "Station Batching" (Smart Sort)
* **Problem:** Changing the Tytax from "Press" to "Pulley" takes time. Doing it 5 times a workout is annoying.
* **Solution:** A "Smart Sort" button in the active session.
* **Logic:** Group exercises by their station type (e.g., do all *Smith Machine* moves first, then all *Low Pulley* moves).
* **Benefit:** Reduces workout time by 20% by minimizing setup changes.

---

## 🚑 Phase 5: Remote Admin Support (The "Help Me" Tools)
**Goal:** Since you cannot see their screens (data is local), you need tools to debug their issues remotely.

### 1. The "State Snapshot" (Debug Tool)
* **Scenario:** Mom says "The app is broken and won't let me finish the workout."
* **Feature:** A hidden "Copy System State" button in Settings.
* **Action:** It copies the entire currentWorkout object to her clipboard as a JSON string.
* **Workflow:** She pastes it into WhatsApp -> You paste it into your "Manual" tab's "Debug Console" to see exactly what went wrong.

### 2. The "Nuke Button" (Factory Reset)
* **Scenario:** Corrupted data makes the app unusable (White Screen loop).
* **Feature:** A specific URL parameter (e.g., 	ytax-mom.onrender.com/?reset=true) that forces a clean wipe of localStorage before the app even attempts to load React.
* **Benefit:** A failsafe way to revive a "dead" app without needing physical access to the device.

