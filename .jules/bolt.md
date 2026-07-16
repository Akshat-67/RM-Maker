## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2025-06-21 - Word lookup optimization in text processing loops
**Learning:** Checking list membership (e.g., `word in ["and", "the", ...]`) inside a loop is O(N). Converting it to a module-level `frozenset` reduces the lookup to O(1) and eliminates the list reconstruction per method call. Further, using `all()` with a boolean list accumulation takes more time and memory than an early exit `for` loop returning `False`.
**Action:** When performing word filtering or matching inside loops, use early return strategies and module-level `set`s or `frozenset`s instead of locally instantiated lists to improve O(N) performance bottlenecks.
