## 2024-05-15 - Fast loop short-circuiting & constant hoisting in Python
**Learning:** Python overhead in tight strings loops (e.g., matching English words or replacing sequences) is high when creating intermediate lists or repeatedly compiling `re.compile`. Early exiting (`return False` instead of appending to a list and calling `all()`) drastically reduces GC allocations. Hoisting constants to class attributes reduces redundant memory footprint.
**Action:** When analyzing hot path loop performance, always hoist constants to the class level and replace aggregate functions with early exits to save intermediate object creation.

## 2024-05-15 - Reconstructing collections in python-docx
**Learning:** The `paragraph.runs` property in `python-docx` is a computed property that reconstructs a list from underlying XML nodes dynamically on every read. Accessing `paragraph.runs` inside a `while` loop index condition leads to silent O(N^2) complexity.
**Action:** When mutating `python-docx` elements, always extract the collection into a local variable (e.g., `runs = paragraph.runs`), iterate the local array, and manually delete indices from the array to maintain synchronization when elements are removed from the DOM.
