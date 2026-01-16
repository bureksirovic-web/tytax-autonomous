# BACKLOG

## 🧪 LEVEL 1: SIMPLE (Warm Up)
- [ ] **Task: Update App Version Label**
    - *Goal:* Change the visible version number in the app footer or settings menu.
    - *Action:* Find the text "v1.0" (or similar) and change it to "v2.0 (Night Shift)".

## 🧪 LEVEL 2: NORMAL (Logic & State)
- [ ] **Feature: Auto-Collapse Completed Exercises**
    - *Goal:* Save screen space by shrinking done exercises.
    - *Action:*
        1. Add isCollapsed state to the ExerciseCard.
        2. When isDone becomes true, automatically set isCollapsed = true.
        3. When collapsed, show a minimal header (e.g., "Bench Press ✅").

## 🧪 LEVEL 3: COMPLEX (CSS & Layout)
- [ ] **Fix: Kinetic Impact Graph Positioning**
    - *Goal:* The muscle graph is blocking the 'Finish Workout' button.
    - *Action:*
        1. Locate the <KineticImpact /> container.
        2. Force it to be position: fixed at the bottom-right (or suitable non-obtrusive spot).
        3. Ensure z-index is lower than the Finish Modal (so the modal pops over it).
