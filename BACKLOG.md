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

- [ ] **Force-Rewrite 'VaultTab' & 'SettingsTab' Components** (Retry: No valid SEARCH/REPLACE blocks found.)

- [ ] **Implement 'Exercise Notes' Field** (Retry: No blocks matched.)

- [ ] **Implement 'Toast' Notification System** (Retry: No valid SEARCH/REPLACE blocks found.)

- [ ] **Design 'Empty States' for All Tabs** (Retry: No valid SEARCH/REPLACE blocks found.)

- [ ] **Implement 'The Gatekeeper' in jules.py** (Retry: No valid SEARCH/REPLACE blocks found.)