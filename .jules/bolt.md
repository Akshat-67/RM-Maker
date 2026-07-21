## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.
## 2025-06-25 - python-docx O(N^2) XML Parsing Overhead
**Learning:** In `python-docx`, accessing `paragraph.runs` dynamically parses the underlying XML tree and creates a new list of `Run` wrapper objects every single time it is accessed. In loops iterating over `len(paragraph.runs)`, this leads to severe O(N^2) list constructions and O(N^3) object creations.
**Action:** When iterating over runs and manipulating the paragraph, cache `paragraph.runs` into a local variable (e.g., `runs = paragraph.runs`) and manually maintain the local list using `del runs[i]` when removing elements to achieve O(N) complexity.
