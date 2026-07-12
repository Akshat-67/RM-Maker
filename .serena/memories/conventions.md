# Conventions & Constraints Memory

These guidelines and code style invariants must be followed without exception to preserve the stability and correctness of LegalDoc Automator (RM-Maker).

## 1. High Impact Files (Extra Care Required)
No files are permanently forbidden. However, modifying high impact files requires extra care:
*   [modules/rm/](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/) (all scripts under RM module)
*   [modules/sd/](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/) (all scripts under SD module)
*   [utils/helpers.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/utils/helpers.py)
*   [app.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/app.py) (specifically session routes)
*   [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)

Before modifying:
*   Inspect dependencies.
*   Preserve schema compatibility.
*   Understand historical reasons.

## 2. Universal English Digit Conversion
- **Constraint**: Convert Devanagari numerals (`०-९`) to standard English digits (`0-9`) globally (applied at session loading, session saving, and AI extraction via `convert_hindi_digits_to_english`).

## 3. Font and Typographic Standards
- **Constraint**: 
  - Unicode internally.
  - Legacy DevLys conversion only at docx rendering boundary.
  - Do not force legacy fonts globally.
- **UI rule**: The verification UI must present Hindi text in clean Unicode Devanagari (Segoe UI or Mangal). Legacy fonts (DevLys 010, Kruti Dev) must **never** be used for browser inputs or textareas.

## 4. Real-time Transliteration
- **Constraint**: The English-to-Hindi transliteration on Enter/Tab/blur fields (calling `/transliterate` or the local `Sanscript` fallback) must remain intact.

## 5. Registered Mortgage (RM) Stability
- **Constraint**: The RM pipeline is production stable. Avoid making changes to RM schema, processors, or extractors unless explicitly requested. Preserve backward compatibility.

## 6. Sale Deed (SD) Canonical Shorthands
- **Constraint**: Preserve the shorthand list names for SD cases in session databases:
  - `ss` = sellers
  - `bs` = buyers
  - `ws` = witnesses
  - `ps` = property

## 7. Editing & Refactoring Guidelines
- **Rule**: This is a production legal document automation system. Understand before editing.
- **Rule**: Historical code may look unusual because it fixes real legal workflow edge cases. Do not simplify without understanding why it exists.
- **Rule**: Use Serena symbol search or file overviews before changing code. Avoid blind rewrites.
- **Rule**: Inspect callers before changing function signatures. Smallest safe changes only.
- **Rule**: Session JSON schemas and template placeholders are contracts. Never drop fields or remove keys without verifying compatibility.
