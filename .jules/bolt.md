## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2025-06-25 - Regex and Object Allocation Hoisting in Hot Paths
**Learning:** During text processing hot paths (like DOCX conversion loops), dynamically creating regular expressions with `re.compile()` or inline lists (e.g., `["a", "b", "c"]`) inside functions causes massive redundant object allocation overhead. Moving static lists to sets (enabling O(1) membership lookups) and hoisting `re.compile` calls to the class level significantly improves runtime efficiency. Replacing boolean array accumulation with early exits in loops further prevents O(N) penalties.
**Action:** Always hoist `re.compile` and static reference variables to the class or module level, convert reference arrays to sets, and utilize early exits rather than full-loop list accumulation for performance-critical text processing.
