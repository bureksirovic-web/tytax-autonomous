# BACKLOG

## 🚑 EMERGENCY REPAIR: Fix White Screen Crash


    - *Diagnosis:* The App is crashing because 'ToastContext' is undefined.
    - *Action:* Locate the main unction App().
    - *Fix:* Wrap the ENTIRE return statement (the Router/Routes) inside <ToastProvider> ... </ToastProvider>.
    - *Check:* Ensure const ToastProvider is actually defined in the file.

- [ ] **Fix 'Default Routines' Infinite Loop**
    - *Diagnosis:* The useEffect for injecting routines might be triggering on every render.
    - *Action:* Check the useEffect that checks saved_workouts.length === 0.
    - *Fix:* Ensure the dependency array is empty [] or strictly managed.

- [ ] **Fix Missing ToastProvider** (Retry: Unknown)