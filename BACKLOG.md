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

- [ ] **Vault Redesign: Collapsible Impact & Detailed Logs**
    - *Previous Fail:* "No changes detected" (AI couldn't find the rendering loop).
    - *Target:* Find const VaultTab = .... Look for the KINETIC IMPACT header.
    - *Action 1:* Wrap the bar chart logic in a standard <details> HTML tag: <details><summary className='...'>📊 Kinetic Impact Analysis (Click to Expand)</summary> ...chart... </details>.
    - *Action 2:* In the exercise list below, replace the simple weight display with a map of the sets: ex.sets.map((s, i) => <div key={i}>Set {i+1}: {s.weight}kg x {s.reps}</div>).

- [ ] **Gym UX: Sticky Stats & Auto-Collapse**
    - *Previous Fail:* "No valid SEARCH/REPLACE blocks."
    - *Strategy:* Do not try to patch small lines. Replace the entire GymTab header section if needed.
    - *Requirement 1 (Sticky Header):* Add sticky top-0 z-50 bg-slate-900 to the header container containing the timer. Add live volume stats there.
    - *Requirement 2 (Collapse):* inside the currentWorkout.exercises.map, check const isComplete = ex.sets.every(s => s.isCompleted). If true, render a <div className='h-12 flex...'> summary row instead of the full card.

- [ ] **Debrief Screen: Stats & Tags**
    - *Context:* New feature.
    - *Action:* Inside FinishTab:
        1. Calculate Total Volume and Duration. Show them in a Grid.
        2. Add clickable 'Quick Tags' (Strong, Tired, Pain) that append text to the notes area.
        3. Change RPE selector to use numbers 1-10.

## 🟡 Maintenance & Fixes

- [ ] **Fix 'Swap Exercise' Logic (Refinement)**
    - *Previous Fail:* "swappingIdx declared twice."
    - *Instruction:* Ensure you remove the old declaration before adding the new safety-checked version. Wrap the whole handler in try/catch.
