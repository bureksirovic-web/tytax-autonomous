## 2024-05-22 - Debouncing Search Inputs
**Learning:** Large datasets in React state (like `mainframe` array with 5000+ items) cause significant main-thread blocking when filtering on every keystroke, even if the filter logic itself is optimized (1.9ms). The React re-render cycle overhead is the bottleneck.
**Action:** Always wrap search/filter inputs for large lists in a debounce hook or component to decouple input UI updates from expensive list re-rendering.

## 2024-05-23 - Caching Expensive Fuzzy Matching
**Learning:** A "smart" video lookup function used fuzzy matching (tokenization + linear scan of 1400+ items) on every render for "unknown" exercises. While exact matches were fast (0.6ms), fuzzy matches took ~100ms per call in a loop. Caching *all* results (including fuzzy matches and misses) reduced subsequent render overhead to ~0.001ms.
**Action:** When implementing "fallback" search logic (like fuzzy matching) in a render-critical path, always memoize or cache the result, especially for negative results (misses).

## 2024-05-24 - Memoizing Derived Calculations in Loops
**Learning:** The "Live Impact" feature called `calculateImpactDistribution` (an expensive reduction over all exercises) inside a `map` loop for 10 muscle groups on every render. This resulted in 11+ redundant calculations per second (~0.6ms overhead) during the active workout timer. Moving this calculation to a single `useMemo` reduced the overhead to ~0.03ms (22x speedup).
**Action:** Never perform expensive derived state calculations inside a render loop (like `.map`). Calculate it once at the component level using `useMemo` and reference the result.
