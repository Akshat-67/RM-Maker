## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.
## 2025-06-20 - python-docx Paragraph Runs Access Overhead
**Learning:** In `python-docx`, accessing `paragraph.runs` reconstructs the run list from the underlying XML elements on every single access. If accessed repeatedly in a loop (e.g., as part of a `while` condition or indexing), it causes `O(N^2)` time complexity when operating on many runs within a paragraph.
**Action:** When iterating through or modifying runs in a paragraph in `python-docx`, cache `runs = paragraph.runs` to a local variable. If the underlying XML is modified during iteration (e.g., deleting an element), manually synchronize the cached list (e.g., `del runs[i]`) since `paragraph.runs` returns a static snapshot.
