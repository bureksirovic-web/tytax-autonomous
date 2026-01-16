# BACKLOG

## 🚨 CRITICAL REPAIR: SessionDebrief Data Flow
- [x] **Fix: ReferenceError debriefData is not defined**
    - *Action:* The component needs access to the workout summary data. 
    - *Surgical Instruction:* 1. Either pass 'debriefData' into the component OR ensure the component uses 'workout' if that is what the parent provides.
        2. **CRITIC NOTE:** It is acceptable to change the prop name to 'workout' as long as the component logic (totalExercises/totalSets) is updated to match.
        3. Ensure the parent App component passes the data object correctly.

## ✨ UX POLISH: MISSION DEBRIEF DOPAMINE UPDATE
- [ ] **Feature: Victory State & Visual Rewards**
    - *Goal:* Make completing a session feel like a significant achievement.
    - *Action:* 1. Update the 'Mission Debrief' heading to include a pulse animation or a subtle 'Glitch' effect on entry.
        2. Add 'Victory Badges' based on session data (e.g., if Volume > 0, show a 'Heavy Metal' badge).
        3. Add a progressive counter animation (tween) so the Total Volume and Total Work numbers 'roll up' from 0 when the screen appears.
        4. Improve RPE buttons: when selected, trigger a subtle haptic-like scale animation (1.1x) and add a glowing emerald drop-shadow.
        5) Add a 'Session Grade' (A, S, or ELITE) calculated based on the RPE and volume.
