## 2024-05-22 - Debouncing Search Inputs
**Learning:** Large datasets in React state (like `mainframe` array with 5000+ items) cause significant main-thread blocking when filtering on every keystroke, even if the filter logic itself is optimized (1.9ms). The React re-render cycle overhead is the bottleneck.
**Action:** Always wrap search/filter inputs for large lists in a debounce hook or component to decouple input UI updates from expensive list re-rendering.

## 2024-05-23 - Caching Expensive Fuzzy Matching
**Learning:** A "smart" video lookup function used fuzzy matching (tokenization + linear scan of 1400+ items) on every render for "unknown" exercises. While exact matches were fast (0.6ms), fuzzy matches took ~100ms per call in a loop. Caching *all* results (including fuzzy matches and misses) reduced subsequent render overhead to ~0.001ms.
**Action:** When implementing "fallback" search logic (like fuzzy matching) in a render-critical path, always memoize or cache the result, especially for negative results (misses).

## 2024-05-24 - Memoization of Expensive Data Parsing
**Learning:** The `getImpact` helper function was parsing `exercise.impact` (Array/Object) or `exercise.note` (Regex) on every call. During list filtering (1600+ items), this caused thousands of unnecessary object allocations and regex executions per render/search.
**Action:** Wrapped the parser in a closure with a `WeakMap` cache keyed by the stable `exercise` object. This reduced execution time for bulk processing from ~164ms to ~8ms (20x speedup).
