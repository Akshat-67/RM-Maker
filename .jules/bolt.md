## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2025-06-21 - Optimization of string parsing checking in hot loops
**Learning:** Using `any(ord(c) > 127 for c in text)` to check for non-ASCII characters is highly inefficient inside Python loops. Compiling a regex like `re.compile(r'[^\x00-\x7F]')` and using `.search()` gives roughly a 10x-15x performance speedup. Additionally, moving static reference lists outside the function scope into module-level properties prevents redundant allocation during high-frequency parsing.
**Action:** When inspecting character types or filtering strings on critical hot paths, hoist pattern arrays to the module level and always prefer compiled regex implementations over Python generator loops (`any()`/`all()`).
