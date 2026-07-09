# Core Codebase Architecture (architecture.md)

This document describes the high-level architecture, pipeline routes, core modules, and system flows in the LegalDoc Automator (RM-Maker) repository.

---

## 1. Important Entry Points
*   **Flask Web Application (`app.py`)**: The primary controller of the system. Runs the server, defines API routes (`/api/cases`, `/api/case/save`, `/api/case/extract`, `/api/case/generate/rm`, `/api/case/generate/sd`, `/transliterate`), serves front-end views (`dashboard.html`, `case.html`, `devlys_to_unicode.html`), handles case session serialization, and coordinates extractor/processor calls.
*   **Case Database (`cases/cases.db`)**: SQLite database where the system stores high-level case info, status, active roles, and paths to case folders.
*   **Case Session Folder (`cases/case_<case_id>/session.json`)**: Raw data files storing verified JSON parameters (borrowers, sellers, witnesses, properties, loans, and title chains) for each case.
*   **Template Directory (`templates/`)**: Contains `.docx` master files categorized by document type (e.g. `templates/SALE_DEED/`, `templates/ICICI/`).
*   **Extension Directory (`extensions/`)**: Independent Chrome extensions loaded by users into their browsers for the portal integration.

---

## 2. Document Pipelines

### A. Registered Mortgage (RM) Pipeline
RM data is processed to generate mortgage documents.
1.  **AI Fact Extraction**: 
    - File upload feeds scanned/searchable PDFs or images into `RMDataExtractor` ([modules/rm/extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/extractor.py)).
    - Extracts structured data: `bs` (Borrowers), `ls` (Loans), `ps` (Properties), `ws` (Witnesses), `bsign` (Bank Signatory), and `ds` (Document Schedules).
2.  **UI Verification & Editing**:
    - Extracted entities are presented in `case.html` verification forms under the RM UI workflow.
3.  **Template Generation**:
    - Submitting the case calls the `/api/case/generate/rm` route.
    - Initializes `RMTemplateProcessor` ([modules/rm/processor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/processor.py)).
    - Normalizes dates, title-cases addresses, format loan words, and maps variables.
    - Applies `Unicode_to_KrutiDev` to translate Hindi fields into the legacy ASCII font mapping before rendering the `.docx` template using `docxtpl`.

### B. Sale Deed (SD) Pipeline
SD data handles property sales.
1.  **AI Fact Extraction**:
    - Feeds files into `SDDataExtractor` ([modules/sd/extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/extractor.py)).
    - Extracts `ss` (Sellers), `bs` (Buyers), `ps` (Property boundaries/dimensions), and `chain` (Title deeds history list).
2.  **Title-Chain Narrative Generation**:
    - Historical deeds inside the title chain are parsed by the narrative engine in [narrative.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/narrative.py) and mapped into dynamic templates in [chain_templates.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/chain_templates.py).
    - Uses Gemini to output a coherent, formal Hindi narrative summarizing the chronological ownership changes.
3.  **Template Generation**:
    - Submitting calls the `/api/case/generate/sd` route, initializing `SDTemplateProcessor` ([modules/sd/processor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/processor.py)).
    - Traverses the context, converts Unicode Hindi variables to DevLys legacy encoding, and renders the selected sale deed template.

---

## 3. Template Builder System
*   **Tool**: [template_builder.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/template_tools/template_builder.py).
*   **Purpose**: Tkinter desktop app that reads raw word files and translates manual field names into Jinja tags (`{{bs[0].n}}`).
*   **Formatting Guard**: Uses the `DocManipulator` class in [builder_core.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/template_tools/builder_core.py) to surgically merge split runs inside XML blocks, ensuring Jinja braces `{{` and `}}` are contained in single runs to prevent parsing compilation failures in `docxtpl`.

---

## 4. e-Panjiyan Automation Extension Suite
*   **Extension Code**: [extensions/epanjiyan_autofill/content.js](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/extensions/epanjiyan_autofill/content.js) and [extensions/epanjiyan_sd_autofill/content.js](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/extensions/epanjiyan_sd_autofill/content.js).
*   **Operation**: 
    1.  The popup reads verified case details from `/api/cases` and loads the active session into browser memory (`localStorage`).
    2.  The content scripts inject data directly into input controls on `epanjiyan.nic.in` forms.
    3.  Automates location selection, Self Category, SRO, Tehsil, and Face Value inputs.
    4.  Bypasses verification alerts and SweetAlert notifications, and orchestrates stage progressions.

---

## 5. KYC & Relation Workflow
*   **File Pairing**: Uploaded Aadhaar front and back images are automatically matched by matching character lengths, trailing numbers, and phonetic similarity, forming unified records.
*   **AI Normalization**: Gemini extractors identify raw name/relation blocks. The names are run through `normalize_name_salutation` to assign Mr./Mrs./Shri/Smt.
*   **Relation Splitting**: Relations are split using `parse_relation_text` into type `r` and relative name `rn` to allow modular assembly in templates (e.g. rendering "पुत्र श्री" or "W/o Mr." dynamically).

---

## 6. AI Model Adapters
*   **Gemini Extractor Client**: Structured around the new `google-genai` SDK using `genai.Client`.
*   **API Key Rotation**: Accepts a list of keys and automatically executes failover rotations upon encountering rate limits or API errors.
*   **Hybrid PDF Pre-filtering**: Extracts plain text from searchable PDFs using `pypdf`, matches legal terms (e.g., plot, boundaries) to select up to 12 critical pages, reducing prompt size and token costs.
