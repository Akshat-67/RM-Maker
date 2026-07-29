## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2023-10-25 - python-docx Paragraph Runs Iteration Performance
**Learning:** Accessing `paragraph.runs` in the `python-docx` library rebuilds the list of runs from the underlying XML elements on every call. Doing this within a loop leads to severe O(N^2) complexity and redundant object creation overhead.
**Action:** Always cache the `paragraph.runs` result into a local variable before iterating over them. If the loop modifies the XML (like removing runs), manually synchronize the local cached list (e.g. `del runs[i]`) instead of continually querying `paragraph.runs`.
