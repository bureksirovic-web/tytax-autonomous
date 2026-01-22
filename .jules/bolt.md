## 2024-05-22 - Debouncing Search Inputs
**Learning:** Large datasets in React state (like `mainframe` array with 5000+ items) cause significant main-thread blocking when filtering on every keystroke, even if the filter logic itself is optimized (1.9ms). The React re-render cycle overhead is the bottleneck.
**Action:** Always wrap search/filter inputs for large lists in a debounce hook or component to decouple input UI updates from expensive list re-rendering.

## 2024-05-23 - Caching Expensive Fuzzy Matching
**Learning:** A "smart" video lookup function used fuzzy matching (tokenization + linear scan of 1400+ items) on every render for "unknown" exercises. While exact matches were fast (0.6ms), fuzzy matches took ~100ms per call in a loop. Caching *all* results (including fuzzy matches and misses) reduced subsequent render overhead to ~0.001ms.
**Action:** When implementing "fallback" search logic (like fuzzy matching) in a render-critical path, always memoize or cache the result, especially for negative results (misses).

## 2024-05-24 - Memoization of Object-Keyed Helpers
**Learning:** Global helper functions like `getImpact` that transform object properties into new objects/arrays can cause significant garbage collection pressure when called in render loops (e.g. list filtering). Even if logic is fast, allocation is not free.
**Action:** Use `WeakMap` to memoize such helpers keyed by the input object reference to ensure O(1) lookups and zero allocation for repeated calls.
