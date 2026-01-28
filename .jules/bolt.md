## 2024-05-22 - Debouncing Search Inputs
**Learning:** Large datasets in React state (like `mainframe` array with 5000+ items) cause significant main-thread blocking when filtering on every keystroke, even if the filter logic itself is optimized (1.9ms). The React re-render cycle overhead is the bottleneck.
**Action:** Always wrap search/filter inputs for large lists in a debounce hook or component to decouple input UI updates from expensive list re-rendering.

## 2024-05-23 - Caching Expensive Fuzzy Matching
**Learning:** A "smart" video lookup function used fuzzy matching (tokenization + linear scan of 1400+ items) on every render for "unknown" exercises. While exact matches were fast (0.6ms), fuzzy matches took ~100ms per call in a loop. Caching *all* results (including fuzzy matches and misses) reduced subsequent render overhead to ~0.001ms.
**Action:** When implementing "fallback" search logic (like fuzzy matching) in a render-critical path, always memoize or cache the result, especially for negative results (misses).

## 2026-01-28 - Memoizing Derived Data in Lists
**Learning:** The `getImpact` helper was creating new array/object instances on every call. In list filtering (e.g., `mainframe.filter`), this function ran O(N) times on every render/filter pass. By using a `WeakMap` to memoize the result keyed by the stable exercise object, execution time for a full library scan dropped by 95% (180ms -> 8ms).
**Action:** Use `WeakMap` for memoizing expensive derived data functions that take an object as input, especially if used inside `filter`, `sort`, or `map` over large datasets.
