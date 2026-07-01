## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.
## 2023-10-27 - Fast Text Validation Strategy
**Learning:** Checking character validity using python iterations mixed with string replacements or `all()` accumulation inside loops causes significant O(N) allocation overheads. Compiling regex checks to class-level properties and using early return logic (`return False` as soon as a non-matching word is found) inside loops eliminates these overheads.
**Action:** Always hoist `re.compile()` calls and static lookup `set`s outside of loops or to class/module scope. When validating an iterator/list, prefer using early return logic rather than list accumulation when possible.
