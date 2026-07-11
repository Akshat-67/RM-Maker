## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.
## 2024-06-25 - Optimize text processing loops with early returns
**Learning:** For hot path text processing and text classification loops (like `is_likely_english`), replacing list accumulation and `all()` with an early exit `return False` significantly improves performance by avoiding unnecessary O(N) object allocations and loop iterations. Pre-compiling `re` patterns and hosting them at the class level instead of inside the method (or inside the loop) also offers measurable speed gains.
**Action:** Always prefer early returns over list accumulation in hot paths. Hoist `re.compile()` calls and static sets to the class level to eliminate redundant memory allocation overhead.
