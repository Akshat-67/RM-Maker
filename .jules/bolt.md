## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.
## 2024-05-18 - Regex Overhead in Hot Loops
**Learning:** In Python, defining and compiling regular expressions (`re.compile`) inside frequently called functions (like `is_likely_english` processing loops) introduces measurable overhead. Additionally, using Python generator expressions like `any('\u0900' <= char <= '\u097F' for char in text)` for unicode character detection is roughly 4.5x slower than using a compiled regular expression with `.search()`.
**Action:** When validating formatting or checking strings in tight loops, pre-compile regexes at the module or class level. Convert arrays of static strings into `set` objects to enable O(1) membership checks instead of O(n) iteration.
