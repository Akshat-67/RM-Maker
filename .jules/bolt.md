## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.
## 2025-06-19 - Fast English Check Optimization
**Learning:** Using `all()` on a dynamically built list (`is_english_words = []`) for evaluating word-by-word criteria is significantly slower than an early exit (`return False`) loop strategy. Also, `any()` with a list generator over substrings is slower than a direct `for` loop with early exit.
**Action:** When iterating to validate a sequence of rules, immediately return False on the first failure instead of aggregating booleans to evaluate at the end. Hoist list-lookups into sets for O(1) checks.
