## 2025-06-19 - Regex Optimization for Devanagari detection
**Learning:** Checking for Devanagari characters in Python using `any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text)` is much slower than using a compiled regex `re.compile(r'[ऀ-ॿ]').search(text)`.
**Action:** When performing character range checks in strings, prefer compiled regex searches over python iteration logic to improve performance, especially on large texts.

## 2025-06-25 - python-docx O(N^2) Performance Bottleneck with Paragraph Runs
**Learning:** Accessing `paragraph.runs` in `python-docx` is not an O(1) attribute lookup; it reconstructs the list of `Run` objects from the underlying XML elements on every call. Using `paragraph.runs` inside a loop condition (e.g. `while i < len(paragraph.runs) - 1:`) results in O(N^2) performance when iterating over large numbers of runs.
**Action:** When iterating over and modifying paragraph runs in `python-docx`, cache `paragraph.runs` to a local variable before the loop. If the underlying XML is modified during the loop (such as `p_element.remove()`), manually synchronize the local cached list (e.g., `del runs[i+1]`) to maintain both O(N) performance and list accuracy.
