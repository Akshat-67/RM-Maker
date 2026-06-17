# DevLys040 Reverse Conversion Analysis

## 1. Current Implementation
- **Converter:** `static/devlys_to_unicode.js`
- **Logic:** Manually defined mapping based on a generic KrutiDev 010 layout.
- **Status:** **INCORRECT.** The mapping used for several critical characters (p, i, h, q, w) is swapped or misaligned with the actual DevLys040 encoding used in this project.

## 2. Comparison: Project Standard vs. Current Preview
The project's standard encoding is defined in `utils/devlys_converter.py` (`unicode_to_devlys`). 

| Character | DevLys040 (Project) | Current Preview Logic | Result |
| :--- | :---: | :---: | :--- |
| **प (Pa)** | `i` | `h` | **FAIL** |
| **ी (ii-matra)** | `h` | `i` | **FAIL** |
| **ु (u-matra)** | `q` | `w` | **FAIL** |
| **ू (uu-matra)** | `w` | `q` | **FAIL** |
| **फ (Pha)** | `¶` | `q` | **FAIL** |
| **ज (Ja)** | `t` | `t` | ✅ PASS |

## 3. Manual Verification of Real Strings
Using the project's source-of-truth mapping (`utils/devlys_converter.py` reversed):

| Raw String | Expected Hindi | Current Preview | Reason for Mismatch |
| :--- | :--- | :--- | :--- |
| `Hkknok] tkscusj] t;iqj` | `भादवा, जोबनेर, जयपुर` | `भादवा, जोबनेर, जयीफर` | `i` mapped to `ी` instead of `प`, `q` mapped to `फ` instead of `ु`. |
| `okMZ u- 3] Hkkfroj]` | `वार्ड न. ३, भातिवर` | `वार्ड न. ३, भातिवर` | (Partial success due to coincidence) |
| `97&,] izfri uxj] t;iqj` | `९७-, प्रति नगर, जयपुर` | `९७&, प्रपति नगर, जयीफर` | `i` mis-mapping and lack of `&` mapping. |

## 4. Root Cause
1. **Wrong Font Base:** The current preview logic was ported from a generic KrutiDev 010 script which has subtle but critical differences from the **DevLys 040** layout used in the LegalDoc templates.
2. **Double Encoding in Logs:** The debug output showed UTF-8 bytes being treated as Latin-1, making the preview look like gibberish even when the logic was partially correct.
3. **Complex Reordering:** DevLys requires specific rules for the `ि` matra (which appears before the character in ASCII) and the `र्` (Reph) marker.

## 5. Existing Converters
- **Forward (Unicode → DevLys):** `utils/devlys_converter.py` (Functional, used for generation).
- **Reverse (DevLys → Unicode):** **DOES NOT EXIST** in the current project. The JS version I implemented was an approximation that failed for 040.

## 6. Implementation Requirements for Fix
To fix the preview, a true **DevLys040 → Unicode** converter must be built by reversing the arrays in `utils/devlys_converter.py`.
1. **Reverse Mapping:** Map `array_two` keys to `array_one` values.
2. **Matra Reordering:** Move `ि` (f) from before the character to after.
3. **Reph Positioning:** Identify `Z` and move it to the correct phonetic position.
4. **Alphanumeric Preservation:** Maintain the existing English detection heuristic.
