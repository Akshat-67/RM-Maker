## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2024-10-24 - Optimization: Hoisting regex and list conversions
**Learning:** Checking for elements in a list inside a loop (like English stop words or punctuation stripping) using un-compiled regexes or dynamically initialized lists on every method call is significantly slower.
**Action:** Always hoist `re.compile` calls and static lists (especially converting them to `set` for O(1) lookup or `tuple` for immutable iteration) to the module or class level to eliminate memory allocation and compilation overhead in hot paths.
