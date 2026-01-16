# BACKLOG

## 🚨 PRIORITY 0: SYSTEM RECOVERY (Fix the Crash)

- [x] **Fix 'ReferenceError: toast is not defined' in App**
    - *CRITICAL:* The app is white-screening because 	oast is used in JSX but not defined.
    - *Action:* Locate the start of unction App().
    - *Insert:* `javascript
      const [toast, setToast] = React.useState(null);
      const showToast = (message, duration = 3000) => {
        setToast({ message, duration });
        setTimeout(() => setToast(null), duration);
      };
      `
    - *Verify:* The error 	oast is not defined must be gone.

## 🛠️ PRIORITY 1: STABILIZE NIGHT SHIFT FEATURES

- [x] **Stabilize 'Default Routines' Injection**
    - *Goal:* Ensure the new "Starter Routines" don't cause an infinite loop.
    - *Action:* Check the useEffect that loads saved_workouts.
    - *Fix:* Ensure it has a dependency array [] (run once) or properly checks if (saved_workouts.length === 0).


    - *Goal:* Ensure the calculator icon opens the modal and doesn't crash.
    - *Action:* Check the setShowCalculator logic in the GymTab.
    - *Fix:* Ensure the state showCalculator is defined in GymTab (e.g., const [showCalculator, setShowCalculator] = React.useState(false);).

- [ ] **Verify 'Exercise Notes' Field**
    - *Goal:* Ensure typing in notes doesn't re-render the whole page aggressively.
    - *Action:* Check the <input> for notes in the active exercise card.
    - *Fix:* Ensure it uses onBlur to save (better performance) or debounced onChange.

- [ ] **Verify 'Plate Calculator' Modal** (Retry: Max retries exhausted or Patch/Critic failed.)