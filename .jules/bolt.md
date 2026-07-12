## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.
## 2025-06-25 - Optimitizing static allocations in regex/lists
**Learning:** Checking for elements in a small `list` vs a `set` has a noticeable performance difference even on small loops (O(N) vs O(1)). Additionally, compiling regex inline via `re.compile` inside a hot-path function introduces significant overhead versus hoisting it to a class or module level variable.
**Action:** Always hoist `re.compile` calls out of functions, and convert static list lookups (e.g. `w in ["and", "the", ...]`) into sets (e.g. `w in {"and", "the", ...}`) when checking membership in performance-sensitive text processing code.
