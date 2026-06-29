# Instructions for Future AI Agents
 
> [!IMPORTANT]
> The guidelines below must be followed by all AI coding assistants or agents working on this codebase.
 
## 1. Do Not Modify KYC and Relation Extraction Without Consent
The KYC/Aadhaar/PAN extraction, normalization, and relation parsing pipeline has been fully optimized, refactored, and verified via a robust test suite. It successfully extracts names, ages, addresses, handles gender-aware salutations, cleans deceased prefixes, parses relations (splitting into relative type `r` and relative name `rn`), and converts digits across both Sale Deed (SD) and Registered Mortgage (RM) modes.
 
* **Constraint**: **DO NOT** modify, refactor, or alter the extraction prompt, merging logic, relation splitting, or normalization helper functions in the following files without explicit, written consent from the user:
  * [modules/sd/extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/extractor.py)
  * [modules/rm/extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/extractor.py)
  * [modules/rm/schema.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/schema.py) (specifically relation preservation in `prune_rm_data`)
  * [utils/helpers.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/utils/helpers.py)
 
## 2. Preserve Universal Digit Conversion
* **Constraint**: Devanagari numerals (`०-९`) must always be converted to standard English digits (`0-9`) globally. This conversion is applied at three robust levels (session loading, session saving, and AI extraction). Any new endpoints or data handlers must maintain this universal English digit format.
 
## 3. Font and Typographic Standards
* **Constraint**: The verification UI must present Hindi text in a clean Unicode Devanagari font (such as `Segoe UI` or `Mangal`). Legacy non-Unicode fonts (such as `DevLys 010` or `Kruti Dev`) must **never** be used to style text inputs or textareas in the browser, as they cause characters and punctuations (commas, dots, dashes) to render incorrectly. Legacy encoding conversion is strictly a backend compilation step for Word document generation.
 
## 4. Protect Automatic Transliteration and Clean Typography UI
* **Constraint**: **DO NOT** modify, disable, or alter the real-time English-to-Hindi transliteration workflow (Enter, Tab, and blur events on English fields automatically calling `/transliterate` and populating Hindi fields with local `Sanscript` fallback) or the clean Unicode Devanagari styling. These features are highly optimized and verified, and must remain intact to preserve the premium user experience.
 
## 5. Protect Registered Mortgage (RM) Relation and UI Workflows
* **Constraint**: **DO NOT** touch or modify the RM relation parsing or assignment workflows. In RM mode, Aadhaar card extractions are funneled exclusively into `unassigned_aadhars`. The fields `r` (relation type, e.g., `S/o`, `W/o`) and `rn` (relative name) must remain fully populated on `unassigned_aadhars`, borrowers (`bs`), and witnesses (`ws`), and must be preserved during database serialization (`prune_rm_data`). Do not alter the custom Jinja `basename` filter in `app.py` or its usage in `case.html` which resolves file path splitting and backslash syntax warnings.


