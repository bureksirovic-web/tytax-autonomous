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

- [x] **Add Tech Cues Field**
   - Add a text input field for "Technique Cues" in the exercise logger.
   - This allows users to save notes like "Keep elbows in" for specific exercises.

- [ ] **Refactor to Custom Modals**
   - The app currently uses ugly browser alerts (window.confirm).
   - Replace these with a custom HTML/CSS modal for actions like "Finish Workout" or "Delete Log".
   - It must match the app's dark theme.

# Tytax Elite Companion - Maintenance Backlog

## 🔴 High Priority (Stability & Data Integrity)

- [ ] **Fix Input Re-render Performance**
    - *Issue:* Typing in KG/Reps inputs triggers a full App re-render on every keystroke.
    - *Fix:* Refactor workout input rows into a sub-component (`ExerciseRow`) using `memo` and local state. Only sync to parent state on `onBlur` or `Enter` key.

- [ ] **Sanitize Date Math in ACWR**
    - *Issue:* `Math.min(...logs.map(l => l.date))` assumes string coercion works perfectly for dates.
    - *Fix:* Convert dates to timestamps explicitly: `Math.min(...logs.map(l => new Date(l.date).getTime()))`.

- [ ] **Standardize Volume Calculation**
    - *Issue:* The "Volume Parity" bar calculates total volume including Warmup sets, but historical comparison logic sometimes filters them out.
    - *Fix:* Create a global `calculateVolume(exercises, includeWarmups=false)` utility. Ensure the Live Parity Bar *excludes* sets marked as `type: 'warmup'` to prevent false "beating the log" positives just by doing more warmup reps.

## 🟡 Medium Priority (UX & Logic)

- [ ] **Persist Program Drafts**
    - *Issue:* Switching tabs while building a program wipes the current `programDraft` state.
    - *Fix:* Save `programDraft` to `localStorage` ('tytax_draft_autosave') on every edit. Clear it only on "Publish" or explicit "Discard".

- [ ] **Fix Scroll Blocking on Spacebar**
    - *Issue:* The event listener for Spacebar (Timer Toggle) calls `e.preventDefault()`. If the user is scrolling rapidly and hits space to pause, the page jumps.
    - *Fix:* Ensure `e.preventDefault()` only fires if `activeTab === 'workout'` AND `!timerActive` logic is actually engaged.

- [ ] **Mobile Keyboard Viewport Shift**
    - *Issue:* On mobile, opening the KG/Reps keyboard might hide the input behind the sticky "Live Dock".
    - *Fix:* Add a Focus listener to inputs that scrolls the element into the center of the viewport (`element.scrollIntoView({block: "center"})`) to ensure visibility above the keyboard.

## 🟢 Low Priority (Cleanup)

- [ ] **Consolidate LocalStorage Effects**
    - *Issue:* There are ~10 separate `useEffect` hooks writing to localStorage.
    - *Fix:* Combine into a single custom hook `usePersistentState` or a reducer to minimize write cycles and improve code readability.

- [ ] **Review Impact Parsing Regex**
    - *Issue:* `parseImpact` regex is slightly fragile.
    - *Fix:* Add unit tests or stricter boundary checks for the semicolon split logic to prevent "Primary Chest 95" from becoming "Chest 95" if a typo exists.
