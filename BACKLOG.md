# BACKLOG.md
## 🚀 Priority 1: Core Stability (The "Golden Master" Polish)

- [ ] **Task 001: Fix State Mutation Bug**
    * **Context:** The Live Kinetic Load chart is not updating because \currentWorkout\ is being mutated directly in the \onChange\ handlers.
    * **Requirement:** In \App.js\ (Workout View), replace all direct state modifications (e.g., \up.exercises[i] = ...\) with \const up = structuredClone(currentWorkout)\.

- [ ] **Task 002: Implement React Keys Stability**
    * **Context:** Using array indices as keys (\key={i}\) causes UI bugs when deleting sets.
    * **Requirement:** Inside \startWorkout\, assign a unique \_id\ (using \crypto.randomUUID()\) to every exercise and set. Update JSX loops to use \key={set._id}\.

- [ ] **Task 003: Enable "Delete Set" Feature**
    * **Context:** Users cannot remove accidental sets in the active logger.
    * **Requirement:** Add a small "Trash" icon to each set row in the active logger. Logic: Only allow deletion if \sets.length > 1\.

## 🎨 Priority 2: UI/UX Refinement

- [ ] **Task 004: Add PPL Filters to Builder**
    * **Context:** Users need to filter by movement pattern, not just muscle.
    * **Requirement:** In \BuilderTab\, add 3 filter chips: "PUSH", "PULL", "LEGS". Map these to the relevant \pattern\ and \muscle_group\ fields.

- [ ] **Task 005: Fix iOS Input Zoom**
    * **Context:** Tapping inputs on iPhone zooms the page, breaking layout.
    * **Requirement:** Add a CSS rule forcing \input, select, textarea { font-size: 16px; }\ specifically for mobile breakpoints (\@media (max-width: 768px)\).

## 💾 Priority 3: Long-Term Health

- [ ] **Task 006: Implement History Pagination**
    * **Context:** The "History" tab crashes the browser after 50+ logs due to rendering load.
    * **Requirement:** Implement pagination. Only render the first 10 logs initially. Add a "Load More" button to append the next 10.

- [ ] **Task 007: Update Lagging Muscle Logic**
    * **Context:** The current 7-day lookback is too short for a 6/1 split, causing false alarms.
    * **Requirement:** Update \getLaggingMuscle\ to use a **14-day** lookback window.


- [ ] **Task 002: Fix Live Kinetic Chart (Re-do)**
   - The 'Live Kinetic Load' chart stopped working after the reset.
   - Ensure the chart re-renders immediately when the user types weight/reps.
   - It must update in real-time (onKeyUp or onChange).

- [ ] **Task 003: Fix Input Focus UX**
   - Current Behavior: After clicking the checkmark to log a set, the cursor jumps to 'Reps'.
   - Required Behavior: The cursor MUST jump back to the 'Weight' (kg) input field automatically.
   - Reason: This allows users to rapidly log multiple sets without clicking.

