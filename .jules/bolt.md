## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.
## $(date +%Y-%m-%d) - Optimization of regex and list lookups in devlys_to_unicode.py
**Learning:** In heavily used loops and functions (like `is_likely_english` processing per-word per-run in documents), inline `re.compile` calls trigger Python's regex cache lookups which incur measurable overhead. Similarly, building boolean lists to pass to `all()` creates unnecessary object allocations vs a simple early-return loop.
**Action:** Always hoist `re.compile` calls out of loops/hot-paths to module or class level variables. Convert lists to sets for fast `O(1)` `in` checks. Replace list accumulations like `is_english_words.append(True); all(is_english_words)` with simple loop structures that exit early.
