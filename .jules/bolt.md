## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2023-10-25 - Regex and List optimizations in loops
**Learning:** Initializing inline regular expressions with `re.match`/`re.sub` inside loops that are called frequently incurs overhead from re-evaluating and compiling the regexes (despite internal re caching). Similarly, creating literal lists like `['a', 'b', 'c']` inside a function re-allocates that list every time.
**Action:** Always hoist regular expressions using `re.compile()` to class-level properties when used repeatedly or inside loops. For literal sets of strings used for lookup, use python `set()` instances stored at the class level to achieve O(1) lookups and prevent reallocation overhead.
