# Fragile Systems & Risk Zones (fragile_systems.md)

This catalog details areas of the codebase that are sensitive, highly dependent on external states, or prone to regressions during refactors.

---

## 1. Document Processors and Run-Splitting Logic
*   **Location**: [processor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/processor.py) and [processor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/processor.py).
*   **Risks**: 
    - The mixed-font splitting algorithms and replacement logic in python-docx look for DevLys fonts using regex pattern matching.
    - If a user formats a template using mixed runs or changes font styles in the same sentence, python-docx may split the XML text elements.
    - Altering the run split matching code can corrupt formatting or miss replacements.

---

## 2. e-Panjiyan DOM Selectors, Timings & Extension Payloads
*   **Location**: [content.js](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/extensions/epanjiyan_autofill/content.js), [content.js](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/extensions/epanjiyan_sd_autofill/content.js), and e-Panjiyan backend routes/services.
*   **Risks**:
    - The government registration website can change its DOM IDs, CSS selectors, or page paths, which will immediately break extension selectors.
    - Slow page loads and dynamic Ajax dropdowns (Select2) can cause race conditions if the script executes before elements are ready.
    - SweetAlert confirmations and OTP authentication fields require fine-tuned wait times.
    - **Extension Payload Shape & Schema**: The Chrome extensions depend strictly on the payload schema returned by the backend at `/api/case/<case_id>/epanjiyan_data`. Modifying the JSON key structure or payload shape will immediately break autofilling on the portal.
    - **Gender Inference Precedence**: Gender classification must check specific indicators (Hindi terms like `"पुत्री"`, `"पत्नी"` and titles like `"SMT"`, `"MRS"`) in a precise order.
    - **SRO/Tehsil Fallback Priority**: SRO mapping resolution must follow the exact priority chain: matched public DLC SRO -> reversed title chain registrations -> property details tehsil/district.
    - **Hindi Relationship Parsing**: Hindi relation string resolution must be preserved to map correctly to English fields (`FATHER`, `HUSBAND`, etc.).

---

## 3. UI State Management (`case.html`)
*   **Location**: [case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html).
*   **Risks**:
    - Contains extensive client-side JavaScript that manages state variables (witness forms, buyer arrays, file roles, and mapping data).
    - Unassigned Aadhaar cards drag-and-drop mechanisms depend on local HTML5 dragging attributes.
    - Changes to list element indices (`bs[0]`, `ss[1]`) can trigger index errors if the JS does not sync correctly with the backend dictionary during serialization.

---

## 4. Session Persistence and File Locks (`app.py`)
*   **Location**: [app.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/app.py) (`load_case_session` and `save_case_session`).
*   **Risks**:
    - Relies on reading and writing JSON files (`session.json`) inside the `cases/` directory.
    - Parallel or overlapping edits to the same case can lead to race conditions where one save request overwrites another.
    - The SQLite case index (`cases.db`) must remain synchronized with the directory file structure.

---

## 5. AI Prompt Sensitivity
*   **Location**: `extractor.py` prompt templates.
*   **Risks**:
    - Modifying prompts or schema guidelines can alter the output shape returned by Gemini.
    - Small shifts in prompts may cause the model to miss fields, alter the JSON key structure, or output un-parsable strings, leading to schema validation failures.

---

## 6. Registered Mortgage (RM) unassigned_aadhars & Relation Behavior
*   **Location**: [schema.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/schema.py) (`prune_rm_data`) and [case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html).
*   **Risks**:
    - Aadhaar scans are funneled exclusively into `unassigned_aadhars` list on the backend and verified via the `case.html` client interface.
    - The relation parameters `r` (relation type, e.g. `S/o`, `W/o`) and `rn` (relative name) must remain fully populated on `unassigned_aadhars`, borrowers (`bs`), and witnesses (`ws`), and preserved in `prune_rm_data` to ensure template compatibility.
    - Changing how these fields are handled in the UI or schema pruning will break the drag-and-drop assignment or the custom Jinja `basename` filter in `case.html` templates.
