# BACKLOG

## 🚨 UI RESCUE MISSION (Force Component Rewrites)

- [ ] **Force-Rewrite 'VaultTab' Component (Collapsible Impact)**
    - *Problem:* The previous 'Kinetic Impact' section is not collapsing. It takes up too much space.
    - *Action:* Find const VaultTab. REPLACE the entire return statement.
    - *Requirement 1:* The 'Kinetic Impact' section MUST be wrapped in:
        <details className='bg-slate-900/50 p-4 rounded-lg border border-slate-800 mb-6 group'>
    - *Requirement 2:* The <summary> tag must say '💪 Workout Impact Analysis' and include a chevron icon.
    - *Requirement 3:* The impact bars must be INSIDE the <details> tag (hidden by default).

- [ ] **Force-Rewrite 'SettingsTab' Component (Import/Export)**
    - *Problem:* Previous attempts failed to add Data Management buttons.
    - *Action:* Find const SettingsTab. REPLACE the entire component.
    - *Requirement:* Add a clear section 'DATA MANAGEMENT' with two distinct buttons:
        1. [Export Backup] (Green): Triggers JSON download.
        2. [Import Profile] (Blue): File Input to restore data.

