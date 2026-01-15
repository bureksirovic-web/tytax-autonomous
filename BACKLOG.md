# BACKLOG

## 🔴 Priority Feature Pack (Correction Mode)

- [x] **Trends 2.0: Interactive Charts (Retry)**
    - *Previous Fail:* Agent tried to render 'MuscleSplitChart' without defining it first.
    - *Requirement:*
        1. Inject Chart.js CDN in index.html head.
        2. Define const ProgressGraph = ({ selectedExercise, logs }) => { ... } inside the TrendsTab component (at the top).
        3. Define const MuscleSplitChart = ({ logs }) => { ... } right next to it.
        4. ONLY then render <ProgressGraph /> and <MuscleSplitChart /> in the return statement.
    - *Logic:* Graph 'Top Weight' vs 'Date' for the selected exercise.


    - *Previous Fail:* "No changes detected" (AI couldn't find the rendering loop).
    - *Target:* Find const VaultTab = .... Look for the KINETIC IMPACT header.
    - *Action 1:* Wrap the bar chart logic in a standard <details> HTML tag: <details><summary className='...'>📊 Kinetic Impact Analysis (Click to Expand)</summary> ...chart... </details>.
    - *Action 2:* In the exercise list below, replace the simple weight display with a map of the sets: ex.sets.map((s, i) => <div key={i}>Set {i+1}: {s.weight}kg x {s.reps}</div>).


    - *Previous Fail:* "No valid SEARCH/REPLACE blocks."
    - *Strategy:* Do not try to patch small lines. Replace the entire GymTab header section if needed.
    - *Requirement 1 (Sticky Header):* Add sticky top-0 z-50 bg-slate-900 to the header container containing the timer. Add live volume stats there.
    - *Requirement 2 (Collapse):* inside the currentWorkout.exercises.map, check const isComplete = ex.sets.every(s => s.isCompleted). If true, render a <div className='h-12 flex...'> summary row instead of the full card.

- [x] **Debrief Screen: Stats & Tags**
    - *Context:* New feature.
    - *Action:* Inside FinishTab:
        1. Calculate Total Volume and Duration. Show them in a Grid.
        2. Add clickable 'Quick Tags' (Strong, Tired, Pain) that append text to the notes area.
        3. Change RPE selector to use numbers 1-10.

## 🟡 Maintenance & Fixes

- [x] **Fix 'Swap Exercise' Logic (Refinement)**
    - *Previous Fail:* "swappingIdx declared twice."
    - *Instruction:* Ensure you remove the old declaration before adding the new safety-checked version. Wrap the whole handler in try/catch.

 (Retry: Okay, let's analyze this diff as the Critic.

**Initial Assessment:** The code introduces a collapsible section for "Kinetic Impact" within the exercise logs and modifies the set display to include a set number. It seems to adhere to the single-file component structure and uses Tailwind classes. However, I need to verify a few things:

1.  **Mobile Responsiveness:** Will the new "Kinetic Impact" section and the added column in the set display break the layout on smaller screens (320px)?
2.  **Accessibility:** Is the `<details>` element used correctly for accessibility?
3.  **State Immutability:** Are the `updateSet` function and `setEditedLog` function using `structuredClone` or other immutable patterns? (This is not directly visible in the diff, but I'll assume it's handled correctly for now).
4.  **Data Integrity:** The new set number column doesn't seem to modify any data, so it should be safe.
5.  **Console Errors:** The code looks clean, but I'll need to check for any warnings related to missing keys or incorrect prop usage.

**Reasoning:**

*   The addition of the "Kinetic Impact" section within a `<details>` element is a good way to collapse potentially long lists of impact scores.
*   The addition of a set number column could improve readability.
*   The use of Tailwind classes seems consistent with the project's styling guidelines.

**Potential Issues:**

*   The `getImpact(ex)` function is not defined in the provided diff. I'll assume it exists and returns the expected data structure.
*   The mobile responsiveness of the new layout needs to be carefully checked. The grid with 4 columns might be too wide for small screens.

**Verification Steps:**

1.  **Visual Regression Test:** I would need to load this code in a browser and resize the window to 320px to check for layout breaks.
2.  **Accessibility Test:** I would need to use a screen reader to ensure the `<details>` element is properly announced.
3.  **State Immutability Check:** I would need to examine the `updateSet` function to ensure it's using immutable updates.

**Conclusion:**

Based on the provided diff, I cannot definitively say whether this fix is perfect. I'm concerned about the mobile responsiveness of the new grid layout.

**Final Verdict:**

FAIL: Potential layout issues on mobile (320px width) due to the added column in the set display. Requires visual regression testing.
)

 (Retry: No valid SEARCH/REPLACE blocks found.)
## 🏁 FINAL TASK: Deployment Preparation


    - *Goal:* Enable "Master Clone" setup for family members and data backup.
    - *UI:* Settings Tab -> New Section 'Data Management'.
    - *Action 1 (Export Workouts):* Button that downloads saved_workouts as 	ytax_workouts.json.
    - *Action 2 (Export Full Backup):* Button that downloads ALL data (logs + workouts) as 	ytax_backup.json.
    - *Action 3 (Import):* File Input that reads a JSON file and restores it to localStorage.
    - *Safety:* Show window.confirm before overwriting data.

- [x] **Vault Redesign: Collapsible Impact & Detailed Logs** (Retry: No blocks matched.)

- [ ] **Gym UX: Sticky Stats & Auto-Collapse** (Retry: No valid SEARCH/REPLACE blocks found.)

- [ ] **Implement Profile Import/Export (JSON)** (Retry: FAIL: Logic Gaps. The "Export Profile" button duplicates the backup functionality. The task was to implement *profile* import/export, meaning only user-specific settings (userProfile, userInventory, customProtocols, warmupStrategy) should be exported, not the entire log history. This is a critical distinction for privacy and data management.
)