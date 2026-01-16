
## 🚨 CRITICAL FIX: SessionDebrief Prop Injection
- [ ] **Fix: Missing debriefData in SessionDebrief**
    - *Issue:* SessionDebrief crashes because it references 'debriefData' which is not in its scope.
    - *Action:* 1. Update the SessionDebrief component definition to include 'debriefData' in the destructuring:
           'const SessionDebrief = ({ duration, volume, debriefData, onComplete }) => {'
        2. Locate where <SessionDebrief /> is called (likely in the main App component) and ensure 'debriefData' is passed as a prop.
        3. Add a safety guard at the top of the component: 
           'if (!debriefData) return null;' 
           This prevents the 'SYSTEM FAILURE' screen if data hasn't loaded yet.
