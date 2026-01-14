# Tytax Elite Companion - Bug Fixes & Tuning

## 🔴 High Priority (Immediate Fixes)

- [x] **Fix Auto-Focus Logic (Reps -> KG)**
    - *Context:* Currently, when finishing a set, the cursor jumps to the *Reps* field of the next set.
    - *Task:* Update the `onClick` handler for the "Check" button. Change the `setTimeout` target ID logic to target `input-kg-${exIdx}-${sIdx+1}` (the KG field) instead of the Reps field.

- [x] **Debug Live Kinetic Impact Chart**
    - *Context:* The "Live Kinetic Impact" chart in the active session is not updating or showing data correctly.
    - *Task:* Review the `currentWorkout` state dependencies. Ensure `calculateImpactDistribution` is called with `currentWorkout.exercises` and `countSets=true`. Force a re-render of the chart when `sets` change.

- [x] **Implement Exercise Swapping (Active Session)**
    - *Context:* The user cannot swap exercises during a workout.
    - *Task:* Add a "Swap" button (icon: `shuffle`) to the exercise header in the Active Workout view. When clicked, show a modal (reuse `BuilderTab` logic or simple list) to replace the current exercise with another from `masterExercises` that matches the same `muscle_group`.

## 🟡 Medium Priority (UX Polish)

- [ ] **Fix Input Re-render Performance**
    - *Issue:* Typing is laggy.
    - *Fix:* Refactor `input` fields to use `onBlur` for state updates, keeping a local `defaultValue` for smooth typing.


# --- URGENT FIXES (JULES SNIPER LIST) ---

## 🔴 High Priority (Functionality Bugs)

- [x] **Fix Auto-Focus Logic (Reps -> KG)**
    - *Context:* Cursor jumps to "Reps" instead of "KG" after finishing a set.
    - *Task:* Update the `onClick` handler for the "Check" button. Change the `setTimeout` target ID logic to target `input-kg-${exIdx}-${sIdx+1}` instead of `input-reps`.

- [x] **Debug Live Kinetic Impact Chart**
    - *Context:* The chart in the active session is flat/empty.
    - *Task:* In `App` component, ensure `currentVolume` and `projectedImpact` recalculate when `logs` or `currentWorkout` changes. Verify `calculateImpactDistribution` is called with `countSets=true` for the active session.

- [ ] **Implement Exercise Swapping**
    - *Context:* User is locked into the preset exercises.
    - *Task:* Add a "Swap" button (icon: `shuffle`) to the exercise header. When clicked, show a modal list of `masterExercises` matching the current `muscle_group`. On selection, replace the current exercise in `currentWorkout`.

## 🟡 Medium Priority (Stability & Performance)

- [ ] **Fix Input Re-render Performance**
    - *Issue:* Typing is laggy because it re-renders the whole app.
    - *Fix:* Create a sub-component `SetRow` that manages its own input state and only updates the parent `App` state on `onBlur` or `Enter` key.

- [ ] **Sanitize Date Math in ACWR**
    - *Issue:* `Math.min(...logs.map(l => l.date))` fails on some browsers.
    - *Fix:* Convert dates to timestamps: `Math.min(...logs.map(l => new Date(l.date).getTime()))`.

- [ ] **Persist Program Drafts**
    - *Issue:* Switching tabs wipes the Builder draft.
    - *Fix:* Save `programDraft` to `localStorage` on change.

- [ ] **Fix Scroll Blocking on Spacebar**
    - *Issue:* Hitting spacebar to pause music scrolls the page.
    - *Fix:* Only `preventDefault` on spacebar if `timerActive` is true.

- [ ] **Mobile Viewport Shift**
    - *Issue:* Keyboard hides input fields.
    - *Fix:* Add `onFocus={(e) => e.target.scrollIntoView({block: "center"})}` to inputs.


## 🔴 High Priority (React Logic Fixes)

- [ ] **Fix Live Kinetic Impact Chart Reactivity**
    - *Context:* The Live Impact chart updates after Set 1 but freezes for Set 2 & 3, even though load increases.
    - *Root Cause:* The `useMemo` calculating `currentVolume` or `impactDistribution` is likely failing to detect deep changes within the `sets` array because the state update might be mutating the object directly or React's shallow comparison ignores deep nested updates.
    - *Task:* 1. Review the `onChange` handlers for the Set Inputs. Ensure they use strict immutable patterns (e.g., `const newWorkout = JSON.parse(JSON.stringify(currentWorkout))`).
        2. Alternatively, add a `forceUpdate` state or a `version` key to `currentWorkout` that increments on every edit to force `useMemo` to recalculate.
        3. Ensure the chart component receives `sets` data explicitly in its dependency array, not just the parent object.


# --- URGENT UI & LOGIC FIXES ---

## 🔴 High Priority (Functionality & UX)

- [ ] **Fix Spacebar Input in Notes**
    - *Issue:* Cannot press space in the "Captain's Log" during session debrief.
    - *Fix:* The global `keydown` listener for the spacebar (timer toggle) is likely calling `e.preventDefault()` without checking if the active element is a `textarea` or `input`. Add a check: `if (document.activeElement.tagName === 'TEXTAREA') return;`.

- [ ] **Implement Set Deletion**
    - *Issue:* Users cannot remove an extra or accidental set.
    - *Task:* Add a small "x" or "trash" button next to each set row in the active workout. When clicked, filter out that set from the exercise's `sets` array.

- [ ] **Implement Exercise Swapping**
    - *Task:* Add a "Swap" button (icon: `shuffle`) to the exercise header. When clicked, show a modal list of `masterExercises` matching the current `muscle_group`. On selection, replace the current exercise in the active workout state.

- [ ] **Fix Vault Notes Visibility**
    - *Issue:* Past session notes are hidden in the History/Vault.
    - *Task:* In the `history` tab render logic, ensure `log.notes` is displayed (e.g., in a styled blockquote or paragraph) within the session card.

- [ ] **Auto-Scroll Active Input to Top**
    - *Issue:* Keyboard hides input fields on mobile.
    - *Task:* When a user focuses a KG or Reps input, use `window.scrollTo` or `element.scrollIntoView({ behavior: 'smooth', block: 'start' })` to position the active exercise at the top of the viewport.

## 🟡 Medium Priority (UI Layout & Manual)

- [ ] **Reposition Rest Timer to Bottom**
    - *Task:* Move the floating `timerActive` UI component from the top/middle of the screen to a fixed position at the bottom (above the navigation dock).

- [ ] **Persistent Live Kinetic Impact Visibility**
    - *Task:* Reposition the "Live Kinetic Impact" bars. Instead of being tucked in a card, make them part of a sticky header or a side-dock (on tablet/desktop) so they stay visible while the user scrolls through exercises.

- [ ] **Make Global Heatmap Collapsible**
    - *Task:* On the Home tab, wrap the "Global Heatmap" in a disclosure/accordion component. Hide the bars by default; show them only when the user clicks the "Global Heatmap" header.

- [ ] **Clean up Home Page Footer**
    - *Task:* Remove the "Elite Manual" section from the bottom of the Home tab to reduce clutter. The manual is already accessible via the "Manual/Features" tab.

- [ ] **Comprehensive Manual Overhaul**
    - *Task:* Rewrite the `features` tab content. Include detailed sections for: Kinetic Impact (95/40 rule), Volume Parity logic, e1RM tracking, RIR (Reps in Reserve) guidance, and how to use the Plate Loader/1RM tools.
