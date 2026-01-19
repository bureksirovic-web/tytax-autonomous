## 2024-05-22 - Debouncing Search Inputs
**Learning:** Large datasets in React state (like `mainframe` array with 5000+ items) cause significant main-thread blocking when filtering on every keystroke, even if the filter logic itself is optimized (1.9ms). The React re-render cycle overhead is the bottleneck.
**Action:** Always wrap search/filter inputs for large lists in a debounce hook or component to decouple input UI updates from expensive list re-rendering.
