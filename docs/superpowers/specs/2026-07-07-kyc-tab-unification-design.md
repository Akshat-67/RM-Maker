# Specification: Unified KYC Tab & Structured AI Extraction
 
This document defines the spec for consolidating identity documents (Aadhaar Front, Aadhaar Back, PAN Card) belonging to the same person under a single tab in the preview editor.
 
## Goal
1. Clean up horizontal tab and sidebar list clutter by collapsing multiple KYC files into one collapsed tab per person (e.g. `Borrower 1 [KYC]`).
2. Provide a 3-way toggle toolbar (`[Front]`, `[Back]`, `[PAN]`) in the preview pane to switch between the collapsed documents seamlessly.
3. Automate file-to-role matching during the AI extraction phase by having Gemini categorize and list the source files of each extracted identity card.
 
---
 
## Proposed Changes
 
### 1. Extraction Prompts
#### [extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/extractor.py) & [extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/extractor.py)
* Update `unassigned_aadhars` list schema. The `files` field of each item will change from a list of strings to a list of objects containing `file` (filename string) and `type` (enum string: `"aadhar_front" | "aadhar_back" | "pan"`).
* Update prompts to instruct Gemini to look at each processed image/PDF page and classify which file belongs to what category.
 
### 2. Normalization Logic
#### [extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/extractor.py) & [extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/extractor.py)
* In `_normalize_list` inside `modules/rm/extractor.py`, ensure `"files"` array is preserved as a list of dicts/objects rather than parsed into raw strings.
 
### 3. Editor UI & File Tab Renaming
#### [case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)
* **Unassigned Table**: Add `data-files` to each row in the unassigned table, containing the escaped JSON string of files array objects.
* **Assign Selected**: When applying assignments, the files of the row are recorded in `localStorage` under `case_file_roles_<CASE_ID>` along with their type (e.g. `case_file_roles_[file1] = {role: "Borrower 1", type: "aadhar_front"}`).
* **Tab Renaming & Collapse (`updateFileTabLabels`)**:
  * Group files by their matched role from `localStorage`.
  * For each role (e.g. `Borrower 1`), identify all associated files.
  * Determine the representative file (e.g., preference: `aadhar_front` -> `aadhar_back` -> `pan`).
  * Only show the representative file's tab in the horizontal bar and sidebar list, renaming it to `${role} [KYC].${ext}`.
  * Hide all other files in that role's group from the tabs and sidebar.
  * Store all active groupings in `window.CURRENT_ACTIVE_GROUPINGS` so the preview system knows what toggles to show.
* **Document Preview (`previewFile`)**:
  * If the previewed file belongs to a role group (e.g., `Borrower 1`), find all other files in the same group.
  * Render the preview toolbar with buttons representing the available file types:
    * `[Front]` if `aadhar_front` exists.
    * `[Back]` if `aadhar_back` exists.
    * `[PAN]` if `pan` exists.
  * Highlight the button corresponding to the currently active file.
  * Clicking a button loads the respective file into the preview iframe/img.
 
---
 
## Verification Plan
* Validate that `py_compile` succeeds on the backend scripts.
* Simulate AI extraction results in `session.json` to verify that collapsed tabs collapse correctly and display `[Front]`, `[Back]`, `[PAN]` buttons.
