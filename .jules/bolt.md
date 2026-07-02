## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2025-07-02 - Fast path word iteration
**Learning:** In hot loops checking for stop words (like `is_likely_english`), checking string containment with an array of strings in a loop (`if w_clean in ["and", "the", ...]: ...  is_english_words.append(True)`) followed by `all(is_english_words)` is slow due to O(N) array allocation, O(N) lookup time, and lack of early returning.
**Action:** Replace stop word list matching with early return boolean logic and hoisted `set` lookups for fast O(1) performance.
