# BACKLOG

## 🧪 RETRY: TIMER LOGIC
- [ ] **Feature: Workout Timer Toggle** (SKIPPED: Max retries)
    - *Action:* Use the new 'jules-timer-hook' ID to find the timer container and add a visibility toggle button.

## 🧪 NEW: UX IMPROVEMENT
- [ ] **Feature: Dynamic Heatmap Legend** (SKIPPED: Max retries)
    - *Action:* Add a small legend (Low, Med, High) to the Global Heatmap section using the existing theme colors.

## ⚠️ SKIPPED TASKS
## 🚨 CRITICAL BUG: DEBRIEF RUNTIME ERROR
- [x] **Fix: ReferenceError debriefData is not defined**
    - *Issue:* App crashes with 'SYSTEM FAILURE' after finishing a set. 
    - *Root Cause:* The 'SessionDebrief' component attempts to access 'debriefData' which is missing or undefined in the current scope.
    - *Action:* 1. Locate 'SessionDebrief' in index.html.
        2. Ensure 'debriefData' has a default empty state or is correctly populated before rendering.
        3. Wrap the data access in a null check (e.g., debriefData?.totalVolume) to prevent future crashes.
