## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2025-06-20 - Cache `paragraph.runs` in python-docx loops
**Learning:** When using `python-docx` for document manipulation, accessing `paragraph.runs` reconstructs the list of `Run` objects from underlying XML elements on every single call. This causes O(N^2) complexity if used inside a `while` loop condition or repeatedly in the loop body.
**Action:** Always assign `paragraph.runs` to a local variable (e.g., `runs = paragraph.runs`) before iterating, and manually manipulate the cached list (e.g., `runs.pop()`) when deleting runs to avoid severe performance degradation on large documents.
