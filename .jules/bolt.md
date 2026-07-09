## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2025-07-09 - Early Exits and Hoisting in Text Classification
**Learning:** Using `all(list_comprehension)` or accumulating boolean flags in a list for text classification (e.g. word-by-word checks) causes unnecessary O(N) object allocations which degrades performance in hot paths. Additionally, compiling regexes and allocating `list` / `set` literals inside loop iterations or function calls adds major overhead.
**Action:** When optimizing text processing functions, hoist static `re.compile` patterns, conversion tuples, and lookup sets to the class or module level. Replace list accumulations with `found_valid = False` + `for loop` + `return False` early-exit strategies to completely avoid memory allocations and short-circuit evaluation.
