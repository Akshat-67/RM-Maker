## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2025-06-21 - Regex Pre-compilation in Python
**Learning:** Instantiating inline `re.compile` or passing raw regex strings to `re.sub`/`re.match` inside functions (especially those called frequently or in loops) causes unnecessary recompilation overhead in Python.
**Action:** Always pre-compile regular expressions as module-level or class-level constants (e.g. `_my_regex = re.compile(r'...')`) when they are used within hot paths or repeated string processing functions.
