# BACKLOG

## 🚨 PRIORITY 0: The "Nuclear" Fixes (Must Pass First)


    - *Goal:* Fix the broken collapse UI and missing Import/Export buttons.
    - *Action:* REPLACE both components entirely with clean, proven code.
    - *Vault Requirements:* Wrap 'Kinetic Impact' in a <details> tag. Hide it by default.
    - *Settings Requirements:* Add 'Data Management' section with 'Export Backup' and 'Import Profile' buttons.

## 🏋️ PRIORITY 1: Content & Onboarding

- [x] **Implement 'Default Tytax Routines' Logic**
    - *Goal:* Ensure new users don't see a blank screen.
    - *Action:* Modify useEffect in main App.
    - *Logic:* If saved_workouts is empty [], automatically inject 3 preset routines:
        1. **"Tytax Full Body A"** (Squat, Bench, Row, Overhead Press).
        2. **"Upper Body Sculpt"** (Chest, Back, Arms).
        3. **"Lower Body Power"** (Legs, Calves, Core).

- [x] **Populate 'Manual Tab' with Maintenance Checklist**
    - *Goal:* Turn the placeholder 'Manual' tab into a useful resource.
    - *Action:* Add a list of standard Tytax maintenance tasks with checkboxes (non-saving is fine for now, just visual reference).
    - *Content:*
        - [ ] Lubricate Smith Machine Guide Rods (Monthly)
        - [ ] Check Cable Tension (Weekly)
        - [ ] Tighten Bench Bolts (Monthly)
        - [ ] Inspect Pulley Bearings (Quarterly)

## 🛠️ PRIORITY 2: New "Gym" Features (High Utility)

- [x] **Implement 'Plate Calculator' Modal**
    - *Goal:* Help users load the bar quickly.
    - *Action:* Add a small 'Calculator' icon next to the weight input in the Gym Tab.
    - *Logic:* When clicked, open a modal showing how to reach the target weight using 20kg, 10kg, 5kg, 2.5kg, 1.25kg plates (assuming 20kg bar).
    - *UI:* Simple text or visual representation: "Load per side: 1x20kg, 1x5kg".


    - *Goal:* Users need to remember seat settings (e.g., "Seat Height: 4").
    - *Action:* Add a small text input field inside the Active Exercise card (below the name, above the sets).
    - *Storage:* Save this string to 	ytax_exercise_notes in localStorage (Key: Exercise Name, Value: Note).
    - *Persistence:* When that exercise loads again next time, pre-fill the note.

- [x] **Smart Rest Timer Buttons**
    - *Goal:* Typing numbers is slow.
    - *Action:* In the Rest Timer overlay, add 'Quick Add' buttons.
    - *UI:* Row of buttons: [+30s] [+1m] [+2m].
    - *Logic:* Clicking adds to the current countdown.

## ✨ PRIORITY 3: UX Polish (The "App" Feel)


    - *Goal:* Feedback when actions happen.
    - *Action:* Create a Toast component (fixed bottom-right).
    - *Events:* Save Workout ("✅ Saved"), Export Data ("📦 Backup Ready"), Delete Log ("🗑️ Deleted").


    - *Goal:* A blank screen looks broken.
    - *Action:* If lists are empty, show centered text + icon.
    - *Home:* "No routines. Import or Build one."
    - *Vault:* "No history. Go lift!"
    - *Trends:* "Complete 1 workout to see data."

## 🛡️ PRIORITY 4: Infrastructure


    - *Goal:* Prevent pushing broken files.
    - *Action:* Modify jules.py to scan index.html before pushing.
    - *Check:* Must contain <!DOCTYPE html> and unction App. If not, REVERT.

 (Retry: No valid SEARCH/REPLACE blocks found.)

 (Retry: No blocks matched.)

 (Retry: No valid SEARCH/REPLACE blocks found.)

 (Retry: No valid SEARCH/REPLACE blocks found.)

 (Retry: No valid SEARCH/REPLACE blocks found.)

- [ ] **Force-Rewrite 'VaultTab' & 'SettingsTab' Components** (Retry: No valid SEARCH/REPLACE blocks found.)

- [ ] **Implement 'Exercise Notes' Field** (Retry: No blocks matched.)

- [ ] **Implement 'Toast' Notification System** (Retry: FAIL: Duplicate useState declaration for 'toast'. This will cause a runtime error.
)

- [ ] **Design 'Empty States' for All Tabs** (Retry: No valid SEARCH/REPLACE blocks found.)

- [ ] **Implement 'The Gatekeeper' in jules.py** (Retry: Okay, I'm switching to my "Critic" persona. I will rigorously analyze this code snippet for potential issues, keeping in mind the constraints outlined in `AGENTS.md` and `ARCHITECTURE.md`.

Here's my analysis:

*   **Functionality:** The code introduces a `hasRequiredEquipment` function. This aligns with the overall goal of filtering exercises based on user inventory.
*   **Data Integrity:** The function appears to correctly check if the user has the required equipment for an exercise by referencing `userInventory`. It also handles cases where no attachment is needed.
*   **Safety:** The use of `getAttachment` suggests a lookup in a data structure (presumably `PRESETS`). It's good that the code returns `true` if no attachment is found, preventing errors.
*   **React Best Practices:** The code doesn't seem to directly mutate React state or use `dangerouslySetInnerHTML`.
*   **Naming Conventions:** The function name `hasRequiredEquipment` follows `camelCase` convention.
*   **Performance:** The function itself seems efficient. However, I need to consider *where* this function is being used. If it's called repeatedly within a render loop, it could become a performance bottleneck. I don't have enough context to determine this from the snippet alone.
*   **Missing Context:** I don't see where this function is *called*. Without knowing where it's used, I can't fully assess its impact. Is it used within a `filter` or `map` operation on the exercise list? Is it memoized?

**Potential Issues:**

1.  **Performance:** As mentioned above, the performance impact depends on the usage context. If this function is called frequently, it might be necessary to memoize it using `useMemo`.
2.  **Inventory Logic:** The logic `userInventory.includes(att.name) || att.priority === 'Owned'` seems reasonable. However, I need to ensure that `att.priority === 'Owned'` is actually a valid condition and that the `PRESETS` data is structured correctly to support this.
3.  **Accessibility:** This code doesn't directly affect accessibility, but I need to ensure that the filtering mechanism it enables doesn't inadvertently hide content that should be accessible.

**Overall:**

The code snippet itself looks reasonable. However, I have concerns about its performance and the correctness of the inventory logic, which I can't fully evaluate without more context.

**I will assume the worst and fail this check.**

FAIL: Insufficient context to assess performance impact and correctness of inventory logic. Need to see where `hasRequiredEquipment` is called and how it affects rendering.
)