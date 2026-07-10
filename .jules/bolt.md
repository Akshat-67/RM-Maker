## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.
## 2024-07-10 - Optimizing Heuristic English Classification in DevLys Converter
**Learning:** In the `devlys_to_unicode.py` hot path, `re.compile()` was repeatedly invoked inside a loop for the English detection heuristic, and list accumulation `append()` + `all()` was used instead of short-circuiting. For large documents, this overhead compounding inside paragraph/run loops is significant.
**Action:** When working on text classification or string processing functions that might be called per-run or per-word in a document parsing loop, proactively hoist regex compilation and static string lists (to `set`s) to the class level, and prioritize early returns to avoid O(N) memory allocations.
