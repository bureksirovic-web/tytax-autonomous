# BACKLOG

## 🔄 PHASE 1: WORKOUT UX RESTORATION

- [ ] **Feature: Auto-Collapse Completed Exercises** (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED) (SKIPPED)
    - *Goal:* When an exercise is marked 'Done' (or all sets checked), the card should collapse.
    - *Action:*
        1. Add isCollapsed state to the Exercise Card.
        2. Toggle it automatically when isDone becomes true.
        3. Show a minimal 'Summary Header' (e.g., 'Bench Press: 3 Sets ✅') when collapsed.
    - *Sentinel Check:* Ensure isCollapsed state is defined.

- [ ] **Fix: Kinetic Impact Graph Positioning**
    - *Goal:* The Live Muscle Impact graph is overlapping content or sitting in the wrong place.
    - *Action:* 1. locate the <KineticImpact /> component (or SVG).
        2. Adjust CSS to position: sticky or ixed at the bottom of the workout view.
        3. Ensure z-index places it *behind* the 'Finish Workout' modal but *visible* during sets.

## 📊 PHASE 2: DATA & TRENDS

- [ ] **Feature: Restore 'Trends' Tab**
    - *Goal:* Re-enable the Trends view in the main navigation.
    - *Action:*
        1. Ensure 
enderTrends() function exists in App.
        2. Add 'Trends' button to the Nav bar.
        3. Ensure it displays the Volume/Progress charts.

- [ ] **UI Polish: Vault Layout Improvements**
    - *Goal:* The Vault looks 'old'. Bring back the modern spacing and dark cards.
    - *Action:* Increase padding on Vault Cards (p-4 to p-6), darken backgrounds (g-slate-800 to g-slate-900), and add subtle borders (order-slate-700).

