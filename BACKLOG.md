# Tytax Elite Companion - Bug Fixes & Tuning

## 🔴 High Priority (Immediate Fixes)

- [ ] **Fix Auto-Focus Logic (Reps -> KG)**
    - *Context:* Currently, when finishing a set, the cursor jumps to the *Reps* field of the next set.
    - *Task:* Update the `onClick` handler for the "Check" button. Change the `setTimeout` target ID logic to target `input-kg-${exIdx}-${sIdx+1}` (the KG field) instead of the Reps field.

- [ ] **Debug Live Kinetic Impact Chart**
    - *Context:* The "Live Kinetic Impact" chart in the active session is not updating or showing data correctly.
    - *Task:* Review the `currentWorkout` state dependencies. Ensure `calculateImpactDistribution` is called with `currentWorkout.exercises` and `countSets=true`. Force a re-render of the chart when `sets` change.

- [ ] **Implement Exercise Swapping (Active Session)**
    - *Context:* The user cannot swap exercises during a workout.
    - *Task:* Add a "Swap" button (icon: `shuffle`) to the exercise header in the Active Workout view. When clicked, show a modal (reuse `BuilderTab` logic or simple list) to replace the current exercise with another from `masterExercises` that matches the same `muscle_group`.

## 🟡 Medium Priority (UX Polish)

- [ ] **Fix Input Re-render Performance**
    - *Issue:* Typing is laggy.
    - *Fix:* Refactor `input` fields to use `onBlur` for state updates, keeping a local `defaultValue` for smooth typing.

