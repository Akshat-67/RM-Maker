# DevLys & Unicode Handling Memory

This project manages two distinct Hindi text representation paradigms: standard Unicode Devanagari (used in UI/browsers) and legacy DevLys 010 / Kruti Dev 010 (used inside Word templates).

## Why Two Standards?
- **Web UI**: Requires Unicode (e.g. `Segoe UI` or `Mangal`). Legacy fonts cause input and browser punctuation rendering bugs (e.g. commas, dashes, periods).
- **Word Templates**: Standardized on legacy non-Unicode fonts (`DevLys 010`). Text must be compiled into the legacy character set prior to writing to `.docx`.

## Key Conversion Logic
- **Unicode to DevLys**: Implemented in `Unicode_to_KrutiDev(unicode_str)` inside [helpers.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/utils/helpers.py).
  - Handles 'ि' matra reordering (from consonant-then-matra in Unicode to matra-then-consonant in legacy).
  - Translates reph (Z) characters using a cluster-aware swapping algorithm.
  - Converts Devanagari numbers to DevLys equivalents (`å` for 0, `ƒ` for 1, etc.).
- **DevLys to Unicode**: Implemented in [devlys_to_unicode.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/utils/devlys_to_unicode.py).
  - Traverses paragraph and table runs inside Word documents.
  - Replaces DevLys rFonts references with Mangal/Standard Devanagari.
- **Legacy Text Heuristics**: `is_text_devlys(text)` in [processor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/processor.py) detects legacy strings using typical indicators (e.g., "fuoklh" for निवासी, "iq=" for पुत्र, vowel sign patterns).

## JavaScript Clipboard Tool
- Located in [devlys_converter_js](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/DevLys%20Converter/devlys_converter_js).
- Contains `converter.js` which provides real-time clipboard conversion.
- Can be compiled into a standalone Windows binary (`devlys-clipboard-converter.exe`) using `pkg`.
