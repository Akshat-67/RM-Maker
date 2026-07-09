# Historical Bugs & Lessons Learned (historical_bugs.md)

This document catalogs patterns of recurring bugs, critical regressions, and integration errors observed in the development of LegalDoc Automator.

---

## 1. DevLys & Font Conversion Regressions
*   **Font Overrides Fallbacks**: 
    - *Bug*: Forcing the legacy `DevLys 040` font style globally across entire paragraphs caused modern Unicode Devanagari runs (like narrative chain text) to fail back to `Times New Roman`, rendering Hindi characters unreadable.
    - *Lesson*: 
      - Unicode internally.
      - Legacy DevLys conversion only at docx rendering boundary.
      - Do not force legacy fonts globally.
*   **Mixed Font Regex Splitting**:
    - *Bug*: Regular expressions designed to split legacy DevLys from Unicode runs falsely captured isolated characters, resulting in fragmented text runs.
    - *Lesson*: Keep splitting regexes guarded and refined to prevent parsing single legacy ASCII characters as distinct font runs.

---

## 2. Salutation & Name Normalization Issues
*   **AI Extraction Extraction Splits**:
    - *Bug*: Gemini extraction models occasionally failed to separate prefix salutations (e.g., Mr., Mrs., Shri, Smt., Late) from the name string, leading to doubled names or incorrect styling (e.g., "Mr. Mr. Dinesh").
    - *Lesson*: Use robust regex filters at the extraction boundary to split salutations into their own fields and clean up nested duplicates (e.g., "स्वर्गीय स्वर्गीय श्री").
*   **Duplicate Salutation Cleanups on Session Load**:
    - *Bug*: Duplicate salutations loaded from historical database files caused double-renderings in UI inputs.
    - *Lesson*: Implement sanitizers during session load/save cycles to strip out duplicated English and Hindi salutations (e.g., "श्री श्री").

---

## 3. Address Formatting Inconsistencies
*   **Title Case Enforcement**:
    - *Bug*: Addresses extracted in uppercase or mixed formats rendered in inconsistent cases across documents, leading to poor formatting.
    - *Lesson*: Enforce strict title-casing algorithms on loading, saving, and template rendering for all parties (borrowers, sellers, witnesses, properties).
*   **District Name Duplications**:
    - *Bug*: Extraction models occasionally returned district names twice (e.g. "JAIPUR JAIPUR"), which leaked into template rendering.
    - *Lesson*: Check for duplicates and strip repeating tokens during parsing.

---

## 4. KYC File Pairing & Merge Errors
*   **NoneType Merge Crashes**:
    - *Bug*: Merging front/back KYC extraction arrays crashed the server with `AttributeError: 'NoneType' has no attribute 'replace'` when optional keys were absent.
    - *Lesson*: Enforce safe dictionary default accessors and null-checking filters inside merging loops (`_merge_kyc_results`).
*   **Aadhaar Front/Back Pairing Regressions**:
    - *Bug*: Simple string-matching checks for Aadhaar images failed to pair files when users uploaded files with names like `Aadhar_Front_Dinesh.jpg` and `Aadhar_Back_Dinesh_1.jpg`.
    - *Lesson*: Use phonetic/vowel-stripped filename matching and substring-regex filters to group and pair files cleanly.

---

## 5. Session State & Persistence Losses
*   **Witness/Signatory state loss**:
    - *Bug*: Modifying case details in the verification UI occasionally discarded witness ages or Aadhaar identifiers during saving because of schema mapping omissions in the UI JS controller.
    - *Lesson*: Keep the form serialization code synchronized with the case schemas.

---

## 6. e-Panjiyan Automation Race Conditions
*   **Party Rows Counting & loops**:
    - *Bug*: Content scripts counted navigation buttons as party data rows on e-Panjiyan pages, leading to false-positive party counts and infinite loop redirects.
    - *Lesson*: Restrict DOM query selections strictly to rows containing active data links and edit icons.
*   **Mobile OTP Validation and Advance Races**:
    - *Bug*: Automating the OTP sequence in e-Panjiyan crashed when SweetAlert confirmation popups blocked form submissions.
    - *Lesson*: Optimistically advance the stage tracker in the extension storage *before* submitting forms to survive redirect loops and modal delays.
*   **Local Server Binding**:
    - *Bug*: Flask running on `127.0.0.1` rejected requests from MacroDroid OTP forwarding scripts on the local Wi-Fi.
    - *Lesson*: Bind the Flask app to `0.0.0.0` to permit local network OTP forwarding.

---

## 7. Template Placeholder Discrepancies
*   **Case Incompatibilities**:
    - *Bug*: Capitalization mismatches (e.g., `chain_text` in context vs. `Chain_Text` in document templates) caused `docxtpl` to silently ignore narrative variables.
    - *Lesson*: Placeholders are strict contracts. Ensure both lowercase and capitalized representations are populated in contexts.
*   **Date Formats**:
    - *Bug*: SD templates required standard `DD.MM.YYYY` date formats, whereas RM templates required ordinal English formats (e.g. `29th June, 2026`).
    - *Lesson*: Avoid applying global date formatting; process date variables based on the target document type (RM vs. SD).
