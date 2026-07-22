## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2025-06-21 - Optimization of Language Heuristics
**Learning:** O(N) list accumulation and `all()`/`any()` generators in hot-path string/word processing loops (like `is_likely_english`) cause unnecessary memory allocations and slow down execution. Early return strategies combined with hoisted compiled regex matching are significantly faster for these specific validation checks.
**Action:** When validating word lists in a hot path, prefer early returns (`return False`) on invalid matches rather than accumulating booleans in a list and evaluating them at the end. Hoist repetitive `re.compile()` calls and `["list"]` containment checks (by converting them to `set` or `tuple`) to the class level to eliminate repeated O(N) lookup/compilation costs.
