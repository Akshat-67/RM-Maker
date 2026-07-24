## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2025-06-21 - Python docx O(N^2) XML access bug
**Learning:** When using `python-docx` for document manipulation, accessing `paragraph.runs` inside a loop rebuilds the list of `Run` objects from the underlying XML elements on every call. This causes an $O(N^2)$ time complexity for paragraph modifications if called continuously in a loop condition.
**Action:** When mutating or analyzing `paragraph.runs` in a loop, always cache it to a local list variable before iterating, and manually keep the cache synchronized if runs are merged or deleted.
