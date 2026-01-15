
## 🎨 UI/UX Polish: Mission Debrief (The Reward Screen)

- [ ] **Implement 'Mission Summary' Stats Card**
    - *Problem:* The current debrief screen is empty. It lacks the 'Reward' of seeing what was accomplished.
    - *Action:* Insert a Stats Row above the RPE selector.
    - *Metrics to Show:*
        1. **Total Volume:** Sum of all (weight * reps). Display as "12.5k KG".
        2. **Total Sets:** Count of completed sets.
        3. **Intensity:** Calculate average weight lifted per set.
    - *Design:* 3-column grid, big bold numbers (	ext-3xl), small labels (	ext-slate-400).

- [ ] **Add 'Quick Tags' (One-Tap Context)**
    - *Problem:* Typing notes ("Captain's Log") is hard with shaky hands after a workout.
    - *Action:* Add a row of clickable 'Pills' above the text area.
    - *Tags:* ['🔥 Strong', '🐢 Sluggish', '🤕 Pain', '⚡ Fast', '🎯 Focused'].
    - *Logic:* Clicking a tag appends it to the 'notes' string automatically.

- [ ] **Expand RPE Selector (1-10 Scale)**
    - *Problem:* Current 6-10 scale ignores light days or deloads.
    - *Action:* Change the selector to a full 1-10 range.
    - *Layout:* Two rows of 5 buttons (1-5 on top, 6-10 on bottom) OR a draggable slider component.
    - *Color Logic:* 1-4 (Green/Blue), 5-7 (Yellow), 8-9 (Orange), 10 (Red).


## 🎨 Gym Tab UX Overhaul (Live Kinetic Impact)


    - *Goal:* User wants to see the 'Kinetic Impact' (Volume) update immediately after entering a set, without scrolling.
    - *Action:* Create a sticky top-0 z-50 header bar.
    - *Content:*
        - Left: Session Timer.
        - Right: **Live Kinetic Impact Leaders**.
        - Logic: Reuse the existing calculateVolumeByMuscle(currentWorkout) function.
        - Display: Show Top 3 muscles (e.g., "CHEST: 1240 | TRICEPS: 550").
    - *Visual:* Use a semi-transparent dark background (g-slate-900/90 backdrop-blur) so it floats over the list.


    - *Goal:* User wants finished exercises "out of the way" to focus on the active one.
    - *Strategy:* **Do NOT re-order the list** (moving items confuses muscle memory). Instead, **Minimize** them.
    - *Logic:*
        - Check if exercise.sets.every(s => s.isCompleted).
        - If TRUE: Render a 'Slim Card' (Height: 40px).
        - Slim Content: ✔ {Exercise Name} - {Total Volume}kg.
        - Interaction: Clicking the slim card expands it back to full size (in case of edits).
    - *Result:* As you work, the page 'shrinks' upwards, keeping your current exercise right in the middle of the screen.

- [x] **Visual Feedback: 'Impact Pulse'**
    - *Context:* Make the math feel 'alive'.
    - *Action:* When a set is marked 'Done':
        1. Update the numbers in the Sticky Header.
        2. Briefly flash the text color of the updated muscle group (e.g., Green/Gold for 500ms).

## 🚨 CRITICAL STABILITY FIXES

- [x] **Fix Error Boundary (Disable Auto-Wipe)**
    - *Context:* The red 'System Failure' screen currently wipes all data.
    - *Requirement:* Update the ErrorBoundary component.
    - *Action:* Change the 'Emergency Reset' button to perform window.location.reload() instead of localStorage.clear().
    - *Goal:* A crash should never destroy the user's history.


    - *Context:* Swapping 'Lower Pulley Single-Arm Seated Cable Row' crashes the app.
    - *Root Cause:* The code likely assumes lternatives always has items. If no other exercise matches the criteria, it crashes accessing index 0.
    - *Fix:* In handleSwapExercise:
        1. Wrap everything in a 	ry { ... } catch (err) { ... } block.
        2. Calculate lternatives.
        3. **CRITICAL CHECK:** if (!alternatives || alternatives.length === 0) { alert('No similar exercises found in library.'); return; }
        4. Only proceed if alternatives exist.
    - *Goal:* If the library has no swaps, just tell the user instead of showing the Red Screen.


## 📈 Trends 2.0 (Strategic Implementation)


    - *Strategic Goal:* Visualize Strength (Weight) vs Time.
    - *Constraint:* Do NOT use 
pm install. Use CDN.
    - *Implementation Steps:*
        1. **Injection:** Check if window.Chart exists. If not, append script: https://cdn.jsdelivr.net/npm/chart.js.
        2. **Component:** Create const ProgressGraph = ({ selectedExercise, logs }) => { ... }.
        3. **Lifecycle Management (CRITICAL):**
           - Use useRef for the canvas element.
           - Use useRef for the chartInstance.
           - In useEffect: **Always call chartInstance.current.destroy()** before creating a new chart to prevent "Canvas is already in use" errors.
    - *Data Mapping:*
        - Filter logs for entries containing selectedExercise.
        - X-Axis: log.date.
        - Y-Axis: Math.max(...exercise.sets.map(s => s.weight)).
    - *Styling:* Dark mode compatible (Grid lines 
gba(255,255,255,0.1)).


    - *Strategic Goal:* Show if the user is skipping leg day.
    - *Logic:*
        1. **Aggregate:** Iterate through ALL 	ytax_logs.
        2. **Count:** Create a frequency map: { 'CHEST': 45, 'LEGS': 12, ... }. Use exercise.muscle_group as key.
        3. **Visualize:** Render a Doughnut Chart next to the main graph.
        4. **Colors:** Use a predefined palette (e.g., ['#3b82f6', '#ef4444', '#10b981', '#f59e0b']) matching the Tailwind theme.

- [x] **Fix 1RM Logic (The Brzycki Standard)**
    - *Strategic Goal:* Replace "Force Output" with scientifically accurate "Estimated 1RM".
    - *Formula Constraint:* Use **Brzycki**: EstMax = weight / (1.0278 - (0.0278 * reps)).
    - *Safety Checks:*
        - If 
eps > 20, ignore the set (it's cardio, not strength).
        - If 
eps === 1, EstMax = weight.
    - *UI Update:* - Replace the 3 top cards (Squat/Bench/Deadlift) with dynamic cards.
        - Iterate through logs to find the *highest calculated 1RM* ever recorded for these movements.
        - Display "Est. 1RM" label clearly.

## 🎨 UI/UX Redesign (Vault Tab)


    - *Problem:* The current Vault view is dominated by the 'Kinetic Impact' chart, and the exercise list does not show reps or sets.
    - *Requirement 1 (Collapsible Impact):* - Wrap the entire "Kinetic Impact" bar chart section in a collapsible toggle.
        - Default state: \isOpen = false\.
        - Header: "📊 Kinetic Impact Analysis (Click to Expand)".
    - *Requirement 2 (Detailed Sets):*
        - Instead of just showing the max weight on the right, render the full set history.
        - Loop through \exercise.sets\.
        - Format: Pill or simple text line: "Set 1: 100kg × 10 (RPE 8)".
    - *Requirement 3 (Visual Hierarchy):*
        - Give each exercise a subtle background (\g-white/5\) and rounded corners to separate them.
        - Make the Exercise Name \	ext-white font-bold\.
        - Make the Set Details \	ext-slate-400 text-sm\.

## 🔴 Priority Correction (Attempt 4)

- [x] **Fix Smart Filters: Actually Hide Irrelevant Buttons**
    - *Root Cause:* The previous code calculated 'isUpper' but did NOT apply it to the filter bar. The buttons for 'Quads/Calves' still render on Upper days.
    - *Requirement:* Locate the ilters.map(...) or the loop that renders the top scrolling filter bar.
    - *Logic:* Wrap that map with a hard filter.
    - *Code Snippet:*
      `javascript
      // Define allow-lists
      const UPPER_TAGS = ['CHEST', 'BACK', 'SHOULDERS', 'BICEPS', 'TRICEPS', 'FOREARMS', 'CORE', 'ALL'];
      const LOWER_TAGS = ['QUADS', 'HAMSTRINGS', 'GLUTES', 'CALVES', 'ADDUCTORS', 'CORE', 'ALL'];
      
      // Inside the render return:
      {availableFilters
         .filter(tag => {
             if (!isSmartActive) return true; // Show all if smart mode off
             if (isUpper) return UPPER_TAGS.includes(tag);
             if (isLower) return LOWER_TAGS.includes(tag);
             return true; 
         })
         .map(tag => ( ...render button... ))
      }
      `
    - *Goal:* On 'Upper A', the 'Calves' button must physically disappear from the DOM.

## 🔴 Priority UX Improvement

- [x] **Implement Context-Aware 'Smart Filters' in Builder**
    - *Context:* When building an 'Upper A' session, seeing 'Glutes' or 'Calves' filters is confusing and clutters the UI.
    - *Requirement:* Update the BuilderTab component to read the sessionName prop.
    - *Logic:* 1. Define constants:
           CONST UPPER_MUSCLES = ['Chest', 'Back', 'Shoulders', 'Biceps', 'Triceps', 'Forearms', 'Core']
           CONST LOWER_MUSCLES = ['Quads', 'Hamstrings', 'Glutes', 'Calves', 'Adductors', 'Core']
        2. On mount (useEffect), check if sessionName contains "Upper" (case-insensitive). 
           - If YES: Set the active filter state to ONLY UPPER_MUSCLES.
           - If sessionName contains "Lower": Set active filter state to ONLY LOWER_MUSCLES.
    - *UI:* When these smart filters are active, visually hide the irrelevant filter chips so the user can't accidentally select them unless they click a "Show All" override.
- [x] **UI Polish: 'Active Set' Deletion (Trash Icon)**
    - *Context:* The previous red button design was too aggressive.
    - *Design Requirement:* Use a **Trash Icon** (Lucide/Heroicon style).
    - *Styling:* 	ext-slate-500 hover:text-red-500 transition-colors. No background colors.
    - *Placement:* Inline with the 'RIR' and 'Notes' fields, or at the far right of the set row.
    - *Interaction:* Simple click to remove the set from currentWorkout state.

## 🔴 Priority Corrections (Functionality Fixes)

- [x] **Fix Global Heatmap: Collapsible & Default Closed**
    - *Problem:* The Heatmap is currently always visible and cannot be toggled.
    - *Requirement:*
        1. Create state: const [isHeatmapOpen, setIsHeatmapOpen] = useState(false).
        2. Render only a "Show/Hide Heatmap" button header initially.
        3. Only render the grid/chart div when isHeatmapOpen is true.
    - *Goal:* Clean UI by default; user clicks to see data.


    - *Problem:* The 'Swap' (Refresh icon) button appears for manual workouts but is missing for 'Fixed/Library' programs.
    - *Fix:* In the 'Gym' tab render loop (activeTab === 'workout'), locate the Exercise Card header.
    - *Action:* Remove any conditional checks (like 'if (!isFixed)') preventing the Swap button from rendering. It should be available for ALL active exercises.

- [x] **Fix Builder Filter Logic (Context Aware)**
    - *Problem:* When building an 'Upper Body' session, the filter bar defaults to showing 'Lower Body' tags or renders irrelevant muscles.
    - *Fix:* inside the Builder component:
        1. Detect the session name string (e.g., 'Upper A').
        2. If name contains 'Upper', automatically select/highlight the 'Push' or 'Pull' filters.
        3. If name contains 'Lower', automatically highlight 'Legs'.
        4. Ensure the filter bar allows manual override.


## 🔴 Priority Corrections (Functionality Fixes)

- [x] **Fix Global Heatmap: Collapsible & Default Closed**
    - *Problem:* The Heatmap is currently always visible and cannot be toggled.
    - *Requirement:*
        1. Create state: const [isHeatmapOpen, setIsHeatmapOpen] = useState(false).
        2. Render only a "Show/Hide Heatmap" button header initially.
        3. Only render the grid/chart div when isHeatmapOpen is true.
    - *Goal:* Clean UI by default; user clicks to see data.


    - *Problem:* The 'Swap' (Refresh icon) button appears for manual workouts but is missing for 'Fixed/Library' programs.
    - *Fix:* In the 'Gym' tab render loop (activeTab === 'workout'), locate the Exercise Card header.
    - *Action:* Remove any conditional checks (like 'if (!isFixed)') preventing the Swap button from rendering. It should be available for ALL active exercises.

- [x] **Fix Builder Filter Logic (Context Aware)**
    - *Problem:* When building an 'Upper Body' session, the filter bar defaults to showing 'Lower Body' tags or renders irrelevant muscles.
    - *Fix:* inside the Builder component:
        1. Detect the session name string (e.g., 'Upper A').
        2. If name contains 'Upper', automatically select/highlight the 'Push' or 'Pull' filters.
        3. If name contains 'Lower', automatically highlight 'Legs'.
        4. Ensure the filter bar allows manual override.


## 🔴 Priority Fixes & Recovery

- [x] **Refine Auto-Scroll UX (Target Exercise Header)**
    - *Context:* Currently, clicking an input scrolls that specific *cell* to the top of the viewport. This hides the Exercise Name context.
    - *Requirement:* Modify the focus handler. Instead of scrolling the input, find the closest parent container (e.g., .exercise-card or the div wrapping the exercise).
    - *Action:* Use element.closest(...) and scroll *that* element to the top (lock: 'start').

- [x] **Implement 'Active Set' Deletion (Gym Tab)**
    - *Context:* We need a way to delete a specific set row while the workout is active.
    - *Instruction:* In the ctiveTab === 'workout' render loop:
        1. Add a small 'X' or Trash icon button to the right of the RIR/Notes inputs for each set.
        2. On click, filter out that specific set index from currentWorkout.exercises[exIdx].sets.
        3. Ensure setCurrentWorkout is called with the updated deep copy.
    - *Safety:* Do NOT modify the 'History' tab logic. Only the active session.

- [x] **Clean up Home Page Footer (Retry)**
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

- [x] **Comprehensive Manual Overhaul**
    - *Task:* Rewrite the eatures tab content. Include detailed sections for: Kinetic Impact (95/40 rule), Volume Parity logic, e1RM tracking, RIR (Reps in Reserve) guidance, and how to use the Plate Loader/1RM tools.

## 🔵 Strategic Enhancements (Code Review Finds)

- [x] **Activate History Editor UI**
    - *Context:* The HistoryEditor component exists but is unreachable.
    - *Task:* In the 'Vault' tab, add an 'Edit' button (icon: tool) to each session card. When clicked, it should trigger the HistoryEditor modal for that specific log.

- [x] **Render Builder Filter Chips**
    - *Context:* The 'categories' logic is calculated in BuilderTab but not displayed.
    - *Task:* In the Builder EDITOR view, add a horizontal scrolling container above the search bar. Map the 'categories' array to clickable chips that update the 'filter' state.

## ⚡ Architectural Optimizations (Strategic Push)

- [x] **Implement Strict Immutability for State Updates**
    - *Task:* Refactor all state setters in 'App.js' (especially within 'setCurrentWorkout') to use deep cloning or functional mapping. This fixes the bug where the Kinetic Impact chart fails to detect nested 'set' updates.

- [x] **Smart Exercise Swapping (Context-Filtered)**
    - *Task:* Update the 'Swap' modal logic. Instead of showing the full library, default the list to exercises that match the current exercise's 'pattern' (e.g., Vertical Pull) or 'station' to streamline mid-workout adjustments.

- [x] **Enhanced Rest Timer Audio/Haptic Loop**
    - *Task:* Integrate a 'Last 5 Seconds' audio tick or haptic pulse into the 'timer' useEffect. Use SpeechSynthesis to announce 'Prepare for next set' when the timer hits 0.

- [x] **Adaptive Recovery Logic (Cold Start Detection)**
    - *Task:* In the 'recoveryStatus' useMemo, add logic to detect if the gap between the last two logs is >10 days. If so, automatically trigger 'Deload' mode suggestions to protect the user from overtraining after a break.

 (Retry: FAIL: Syntax Error. The variable `swappingIdx` is declared twice in the `App` component (lines 4376 and 4378 in the diff context). This will cause a "Identifier 'swappingIdx' has already been declared" error and crash the application (White Screen). Remove the duplicate declaration.)

 (Retry: No blocks matched.)

- [x] **Harden 'Swap Exercise' Logic (Handle Zero Alternatives)** (Retry: No valid SEARCH/REPLACE blocks found.)

- [x] **Inject Chart.js & Build 'ProgressGraph' Component** (Retry: FAIL: The task explicitly requires building the 'ProgressGraph' component, but the provided diff only injects the Chart.js library script. The React component implementation is completely missing.)

 (Retry: No valid SEARCH/REPLACE blocks found.)

- [ ] **Redesign Vault Log Cards (Collapsible Chart + Set Details)** (Retry: No changes detected.)

- [ ] **Enable Exercise Swapping for Pre-Loaded Programs** (Retry: No blocks matched.)

- [ ] **Implement Sticky 'Kinetic Impact' Header** (Retry: No valid SEARCH/REPLACE blocks found.)

- [ ] **Auto-Collapse Completed Exercises (Minimize Clutter)** (Retry: No valid SEARCH/REPLACE blocks found.)

- [ ] **Implement 'MuscleSplit' Donut Chart** (Retry: FAIL: MuscleSplitChart component is not defined. The provided diff adds a reference to `<MuscleSplitChart logs={logs} />` without defining or importing this component. This will cause a runtime error.
)
