# TESTING_PROTOCOL.md
Since this is a Single-File App (\index.html\), traditional Unit Tests (Jest) are not currently configured. You must perform **Behavioral Verification**.

## 🛑 Pre-Commit Checklist
Before marking a task as "Done," verify the following:

### 1. The "White Screen" Test
* **Action:** Open \index.html\ in a browser.
* **Pass:** The Dashboard loads with the "TYTAX ELITE" logo and navigation tabs.
* **Fail:** A white screen indicates a React syntax error (check Console).

### 2. The "Ghost Mode" Logic Check
* **Action:** Start a workout. Log a set (e.g., Bench Press: 100kg x 10). Finish session.
* **Action:** Start the *same* session again.
* **Verify:** The input fields for Bench Press should show \100\ as a placeholder (Ghost Value).
* **Verify:** Typing \101\ should turn the text **Green** (Progressive Overload Trigger).

### 3. The Responsive Check
* **Action:** Resize browser window to mobile width (375px).
* **Verify:**
    * Navigation bar moves to the bottom (\ixed bottom-0\).
    * The "Workout Logger" cards stack vertically (1 column).
    * Input fields do not cause the page to zoom (Font size must be >= 16px).

### 4. Data Integrity Check
* **Action:** Open Browser DevTools -> Application -> Local Storage.
* **Verify:** \	ytax_logs\ should be a valid JSON array, not \[object Object]\.

## 🚨 Emergency Recovery
If the app crashes after your changes:
1.  Check the Console for "Minified React Error".
2.  If you modified state logic, verify you used \structuredClone\ and did not mutate \currentWorkout\ directly.
3.  Run the "Emergency Purge" button in Settings (if accessible) or manually clear \localStorage\ to rule out data corruption.
