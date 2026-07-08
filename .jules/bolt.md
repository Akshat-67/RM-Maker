## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.
## 2025-07-08 - String heuristic early exits
**Learning:** The `is_likely_english` function originally accumulated a boolean array across a tokenized string and checked `all(is_english_words)` at the end, leading to unnecessary iteration overhead for strings that fail heuristics on the very first word. Hoisting the regexes and converting list checks to early-returns resulted in a measurable speed up on both typical matches and failures.
**Action:** For string classification loops, prioritize early exit returns (`return False` or `return True` as soon as determined) rather than accumulating boolean arrays and evaluating them en masse at the end. Hoist repetitive operations like list lookups into static `set`s.
