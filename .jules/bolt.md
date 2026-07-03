## 2024-05-18 - Fast Character Iteration
**Learning:** Checking for Devanagari or non-ASCII characters is significantly faster in Python when using a compiled regular expression (`re.compile(r'[^\x00-\x7F]')` or `re.compile(r'[\u0900-\u097F]')`) instead of a generator expression with `any(ord(c) > 127 for c in s)`.
**Action:** Replace `any(...)` character iteration loops with precompiled regular expressions in hot text-processing paths.

## 2024-05-18 - The Surprising Replacement Micro-Optimization
**Learning:** For replacing hundreds of string pairs (like the DevLys mapping list), chaining `.replace()` inside a simple python `for` loop is considerably faster (~4x) than using a precompiled `re.sub` with a lambda function mapping `match.group(0)` to a dictionary. The function call overhead per match inside the lambda outweighs the string `.replace()` traversal, even with lots of regex backtracking.
**Action:** Stick to sequential `str.replace` loops for large mapping arrays instead of trying to be clever with `re.sub` and lambdas.
