# Tytax Elite Companion - Remaining Backlog

## 🔴 High Priority (Functionality & UX)

- [ ] **Implement Set Deletion**
    - *Issue:* Users cannot remove an extra or accidental set.
    - *Task:* Add a small "x" or "trash" button next to each set row in the active workout. When clicked, filter out that set from the exercise's `sets` array.

- [ ] **Fix Vault Notes Visibility**
    - *Issue:* Past session notes are hidden in the History/Vault.
    - *Task:* In the history tab render logic, ensure log.notes is displayed (e.g., in a styled blockquote or paragraph) within the session card.

- [ ] **Auto-Scroll Active Input to Top**
    - *Issue:* Keyboard hides input fields on mobile.
    - *Task:* When a user focuses a KG or Reps input, use window.scrollTo or element.scrollIntoView({ behavior: 'smooth', block: 'start' }) to position the active exercise at the top of the viewport.

## 🟡 Medium Priority (UI & Content)

- [ ] **Reposition Rest Timer to Bottom**
    - *Task:* Move the floating 	imerActive UI component from the top/middle of the screen to a fixed position at the bottom (above the navigation dock).

- [ ] **Persistent Live Kinetic Impact Visibility**
    - *Task:* Reposition the "Live Kinetic Impact" bars. Instead of being tucked in a card, make them part of a sticky header or a side-dock (on tablet/desktop) so they stay visible while the user scrolls through exercises.

- [ ] **Make Global Heatmap Collapsible**
    - *Task:* On the Home tab, wrap the "Global Heatmap" in a disclosure/accordion component. Hide the bars by default; show them only when the user clicks the "Global Heatmap" header.

- [ ] **Clean up Home Page Footer**
    - *Task:* Remove the "Elite Manual" section from the bottom of the Home tab to reduce clutter.

- [ ] **Comprehensive Manual Overhaul**
    - *Task:* Rewrite the eatures tab content. Include detailed sections for: Kinetic Impact (95/40 rule), Volume Parity logic, e1RM tracking, RIR (Reps in Reserve) guidance, and how to use the Plate Loader/1RM tools.
