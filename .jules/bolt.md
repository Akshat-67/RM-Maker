## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2026-07-02 - Hoisting regex and early returns in hot paths
**Learning:** In text classification loops (e.g., heuristics like `is_likely_english`), dynamic compilation of regex (`re.compile` inside a function), array allocation, and accumulation using `all()` can severely degrade performance. Hoisting regexes, converting list lookups to sets, and returning early can reduce the function overhead by ~40%.
**Action:** When working on heuristic or matching functions called thousands of times, hoist all `re.compile` and static collections to the class level. Use `set` for O(1) membership lookups instead of list. Prefer early-exit control flow instead of accumulating booleans for an `all()` or `any()` evaluation.
