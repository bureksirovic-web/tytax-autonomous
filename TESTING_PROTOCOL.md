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
    * Navigation bar moves to the bottom (\fixed bottom-0\).
    * The "Workout Logger" cards stack vertically (1 column).
    * Input fields do not cause the page to zoom (Font size must be >= 16px).

### 4. Data Integrity Check
* **Action:** Open Browser DevTools -> Application -> Local Storage.
* **Verify:** \tytax_logs\ should be a valid JSON array, not \[object Object]\.

## 🚨 Emergency Recovery
If the app crashes after your changes:
1.  Check the Console for "Minified React Error".
2.  If you modified state logic, verify you used \structuredClone\ and did not mutate \currentWorkout\ directly.
3.  Run the "Emergency Purge" button in Settings (if accessible) or manually clear \localStorage\ to rule out data corruption.

## 🚀 Production Deployment Gates
Beyond local behavior, verification extends to the live Render environment.

### 1. The 'Black Screen' Check
* **Context:** A syntax error in \index.html\ often compiles fine but crashes the runtime.
* **Protocol:** After deployment, if the \Render Status\ is \live\ but the URL renders a black/white screen, this is a **Critical Severity** failure.
* **Response:** Immediate \git revert HEAD\ is required.

### 2. The '19-Second' Heuristic
* **Warning:** Complex tasks (e.g., 'Implement Set Deletion') cannot be completed in < 20 seconds.
* **Protocol:** If a run finishes instantly, assume the patch was rejected or skipped due to a Regex mismatch.

### 3. Fail-Forward Strategy
* If a task fails QA 3 times (\MAX_QA_RETRIES\), it is not deleted.
* It is moved to the **bottom** of \BACKLOG.md\ with a note \(Retry: QA Failed)\.
* The system then proceeds to the next independent task to prevent a deadlock.
