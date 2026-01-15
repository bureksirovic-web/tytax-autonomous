# BACKLOG

## 🔨 Deployment Blockers (The Final Sprint)

- [ ] **Implement Profile Data Management (Settings Tab)**
    - *Goal:* Create a specific 'Data Management' section in Settings for backup/restore.
    - *Critical Fix:* **REMOVE** the existing 'Backup Data' button first. Do not just add new ones (prevent duplicate button error).
    - *Action:* Add two clear buttons in a grid:
        1. **'Export Full Backup (JSON)'**: Downloads 	ytax_backup_{date}.json containing { logs, workouts, profile }.
        2. **'Import Backup'**: File input that parses that JSON and restores localStorage.
    - *Safety:* Add window.confirm before restoring data.

- [ ] **Vault Redesign (Visual Cleanup)**
    - *Goal:* Make the log list readable without breaking mobile layout.
    - *Constraint:* **Do NOT use inline styles** for the progress bars (QA Reject). Use Tailwind utility classes (e.g., g-blue-500 h-2 rounded).
    - *Action:*
        1. Locate VaultTab.
        2. Wrap the 'Kinetic Impact' chart in a <details className="group mb-6"> tag so it defaults to closed.
        3. In the log list, simply add a text line: Set {i+1}: {s.weight}kg x {s.reps}. Do not create complex grids yet.

- [ ] **Gym UX: Sticky Stats Header**
    - *Goal:* Show live volume while scrolling.
    - *Constraint:* The previous attempt failed to find the code block.
    - *Strategy:* Target the **Session Timer** component.
    - *Action:* Wrap the existing Timer in a new container:
        <div className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur border-b border-slate-800 p-4 flex justify-between items-center shadow-lg">
    - *Add:* A simple span next to the timer: <span>Vol: {currentVolume}kg</span>.

