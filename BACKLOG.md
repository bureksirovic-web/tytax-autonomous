
## 🔴 Priority Fixes & Recovery

- [x] **Refine Auto-Scroll UX (Target Exercise Header)**
    - *Context:* Currently, clicking an input scrolls that specific *cell* to the top of the viewport. This hides the Exercise Name context.
    - *Requirement:* Modify the focus handler. Instead of scrolling the input, find the closest parent container (e.g., .exercise-card or the div wrapping the exercise).
    - *Action:* Use element.closest(...) and scroll *that* element to the top (lock: 'start').

- [ ] **Implement 'Active Set' Deletion (Gym Tab)**
    - *Context:* We need a way to delete a specific set row while the workout is active.
    - *Instruction:* In the ctiveTab === 'workout' render loop:
        1. Add a small 'X' or Trash icon button to the right of the RIR/Notes inputs for each set.
        2. On click, filter out that specific set index from currentWorkout.exercises[exIdx].sets.
        3. Ensure setCurrentWorkout is called with the updated deep copy.
    - *Safety:* Do NOT modify the 'History' tab logic. Only the active session.

- [ ] **Clean up Home Page Footer (Retry)**
    - *Context:* The previous attempt caused a syntax error/blank screen.
    - *Requirement:* Simplify the footer text/links.
    - *QA:* Double-check that all <div> and <a> tags are properly closed to prevent a crash.

## 🔴 Immediate Fixes (Correction)

- [x] **Implement 'Active Set' Deletion (Gym Tab)**
    - *Context:* The previous attempt added deletion to the History tab, but we need it in the Active Session.
    - *Task:* In the 'activeTab === workout' render loop, find the row where sets are mapped ({ex.sets.map...}).
    - *Action:* Add a small 'x' button next to the 'RIR' dropdown.
    - *Logic:* On click, remove that specific index from the 'currentWorkout.exercises[exIdx].sets' array and trigger 'setCurrentWorkout' with the update.# Tytax Elite Companion - Remaining Backlog

## 🔴 High Priority (Functionality & UX)

- [x] **Implement Set Deletion**
    - *Issue:* Users cannot remove an extra or accidental set.
    - *Task:* Add a small "x" or "trash" button next to each set row in the active workout. When clicked, filter out that set from the exercise's `sets` array.

- [x] **Fix Vault Notes Visibility**
    - *Issue:* Past session notes are hidden in the History/Vault.
    - *Task:* In the history tab render logic, ensure log.notes is displayed (e.g., in a styled blockquote or paragraph) within the session card.

- [x] **Auto-Scroll Active Input to Top**
    - *Issue:* Keyboard hides input fields on mobile.
    - *Task:* When a user focuses a KG or Reps input, use window.scrollTo or element.scrollIntoView({ behavior: 'smooth', block: 'start' }) to position the active exercise at the top of the viewport.

## 🟡 Medium Priority (UI & Content)

- [x] **Reposition Rest Timer to Bottom**
    - *Task:* Move the floating 	imerActive UI component from the top/middle of the screen to a fixed position at the bottom (above the navigation dock).

- [x] **Persistent Live Kinetic Impact Visibility**
    - *Task:* Reposition the "Live Kinetic Impact" bars. Instead of being tucked in a card, make them part of a sticky header or a side-dock (on tablet/desktop) so they stay visible while the user scrolls through exercises.

- [x] **Make Global Heatmap Collapsible**
    - *Task:* On the Home tab, wrap the "Global Heatmap" in a disclosure/accordion component. Hide the bars by default; show them only when the user clicks the "Global Heatmap" header.

- [x] **Clean up Home Page Footer**
    - *Task:* Remove the "Elite Manual" section from the bottom of the Home tab to reduce clutter.

- [ ] **Comprehensive Manual Overhaul**
    - *Task:* Rewrite the eatures tab content. Include detailed sections for: Kinetic Impact (95/40 rule), Volume Parity logic, e1RM tracking, RIR (Reps in Reserve) guidance, and how to use the Plate Loader/1RM tools.

## 🔵 Strategic Enhancements (Code Review Finds)

- [ ] **Activate History Editor UI**
    - *Context:* The HistoryEditor component exists but is unreachable.
    - *Task:* In the 'Vault' tab, add an 'Edit' button (icon: tool) to each session card. When clicked, it should trigger the HistoryEditor modal for that specific log.

- [ ] **Render Builder Filter Chips**
    - *Context:* The 'categories' logic is calculated in BuilderTab but not displayed.
    - *Task:* In the Builder EDITOR view, add a horizontal scrolling container above the search bar. Map the 'categories' array to clickable chips that update the 'filter' state.

## ⚡ Architectural Optimizations (Strategic Push)

- [ ] **Implement Strict Immutability for State Updates**
    - *Task:* Refactor all state setters in 'App.js' (especially within 'setCurrentWorkout') to use deep cloning or functional mapping. This fixes the bug where the Kinetic Impact chart fails to detect nested 'set' updates.

- [ ] **Smart Exercise Swapping (Context-Filtered)**
    - *Task:* Update the 'Swap' modal logic. Instead of showing the full library, default the list to exercises that match the current exercise's 'pattern' (e.g., Vertical Pull) or 'station' to streamline mid-workout adjustments.

- [ ] **Enhanced Rest Timer Audio/Haptic Loop**
    - *Task:* Integrate a 'Last 5 Seconds' audio tick or haptic pulse into the 'timer' useEffect. Use SpeechSynthesis to announce 'Prepare for next set' when the timer hits 0.

- [ ] **Adaptive Recovery Logic (Cold Start Detection)**
    - *Task:* In the 'recoveryStatus' useMemo, add logic to detect if the gap between the last two logs is >10 days. If so, automatically trigger 'Deload' mode suggestions to protect the user from overtraining after a break.


