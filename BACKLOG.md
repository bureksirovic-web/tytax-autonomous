# BACKLOG

## 🚨 PRIORITY: FIX WHITE SCREEN CRASH


    - *Error:* Uncaught TypeError: Cannot read properties of null (reading 'useState')
    - *Diagnosis:* A useState hook is likely being called OUTSIDE of the unction App() component (in the global scope).
    - *Action:* Scan the top of the file and the Toast logic.
    - *Fix:* Move any const [x, setX] = useState(...) lines INSIDE the App or ToastProvider component.
    - *Verify:* Ensure React.useState is only called inside valid functional components.

- [x] **Inject Missing 'ToastProvider' Wrapper**
    - *Diagnosis:* The console warned useToast must be used within a ToastProvider.
    - *Action:* Find the unction App return statement.
    - *Fix:* Wrap the router:
      <ToastProvider> <div className="min-h-screen..."> ... </div> </ToastProvider>
    - *Constraint:* Ensure ToastProvider is defined before App.

- [x] **Verify Default Routines Logic (Infinite Loop Check)**
    - *Goal:* Ensure the new 'Starter Pack' logic doesn't crash the browser.
    - *Action:* Check the useEffect that loads default workouts.
    - *Fix:* Ensure the dependency array is [] (run once) and not [saved_workouts] (infinite loop).

- [x] **Debug and Fix 'useState' Global Scope Error** (Retry: FAIL: The diff removes the toast functionality entirely instead of fixing it. The task is to fix the global scope error, which means moving the `useState` hook and its related logic *inside* the `App` component where it can be correctly called. This change just deletes the feature.)