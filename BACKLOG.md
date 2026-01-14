# AGENT BACKLOG
The agent picks the first unchecked box.

- [x] **Fix Live Kinetic Chart**
   - The "Live Kinetic Load" chart stopped working.
   - Ensure the chart re-renders immediately when the user types weight/reps.
   - Use proper React state (onKeyUp or onChange) to trigger updates.

- [x] **Fix Input Focus UX**
   - Current Behavior: After clicking the checkmark to log a set, the cursor jumps to "Reps".
   - Required Behavior: The cursor MUST jump back to the "Weight" (kg) input field automatically.
   - Reason: This allows users to rapidly log multiple sets without clicking.

- [x] **Implement Global Bar Weight**
   - Add a "Bar Weight" input in the Settings tab.
   - Ensure the Plate Calculator uses this global setting instead of a hardcoded value.
   - Default to 20kg / 45lbs if not set.

- [x] **Implement History Editor**
   - Add an "Edit" button to logs in the Vault/History view.
   - Allow users to modify sets, reps, and weight of past workouts.
   - Ensure changes persist to local storage.

- [x] **Implement Smart Substitutions**
   - Add a "Swap" button to the workout logger.
   - Allow users to swap the current exercise for a similar one (e.g., Bench Press -> Dumbbell Press).
   - This requires a simple lookup logic or list of equivalents.

- [ ] **Add Tech Cues Field**
   - Add a text input field for "Technique Cues" in the exercise logger.
   - This allows users to save notes like "Keep elbows in" for specific exercises.

- [ ] **Refactor to Custom Modals**
   - The app currently uses ugly browser alerts (window.confirm).
   - Replace these with a custom HTML/CSS modal for actions like "Finish Workout" or "Delete Log".
   - It must match the app's dark theme.
