## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2023-10-27 - Early exits and hoisted regex for large loop operations
**Learning:** For a text classification function executing on every paragraph of a document, string operations (like `w_clean in ["and", "the", ...]`) perform significantly faster when the target collection is initialized once as a module-level `set`. Re-evaluating lists or compiling regexes on the hot path creates massive aggregate latency.
**Action:** Always precompile `re.compile()` calls outside loop scope. Prefer early exit returns in text parsers instead of aggregating values in a list (e.g. `is_english_words.append(True)`) and waiting until the loop finishes to check `all(is_english_words)`.
