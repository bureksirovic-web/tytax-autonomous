# Tytax Elite Companion - Bug Fixes & Tuning

## 🔴 High Priority (Immediate Fixes)

- [x] **Fix Auto-Focus Logic (Reps -> KG)**
    - *Context:* Currently, when finishing a set, the cursor jumps to the *Reps* field of the next set.
    - *Task:* Update the `onClick` handler for the "Check" button. Change the `setTimeout` target ID logic to target `input-kg-${exIdx}-${sIdx+1}` (the KG field) instead of the Reps field.

- [x] **Debug Live Kinetic Impact Chart**
    - *Context:* The "Live Kinetic Impact" chart in the active session is not updating or showing data correctly.
    - *Task:* Review the `currentWorkout` state dependencies. Ensure `calculateImpactDistribution` is called with `currentWorkout.exercises` and `countSets=true`. Force a re-render of the chart when `sets` change.

- [ ] **Implement Exercise Swapping (Active Session)**
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

