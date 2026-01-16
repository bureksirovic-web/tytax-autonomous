# BACKLOG

## 🚨 CRITICAL REPAIR: SessionDebrief Data Flow
- [x] **Fix: ReferenceError debriefData is not defined**
    - *Action:* The component needs access to the workout summary data. 
    - *Surgical Instruction:* 1. Either pass 'debriefData' into the component OR ensure the component uses 'workout' if that is what the parent provides.
        2. **CRITIC NOTE:** It is acceptable to change the prop name to 'workout' as long as the component logic (totalExercises/totalSets) is updated to match.
        3. Ensure the parent App component passes the data object correctly.
