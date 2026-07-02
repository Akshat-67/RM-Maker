# Developer Onboarding Guide & Sitemap
*A comprehensive reference guide for future AI agents and developers working on the RM/SD Generator codebase.*

---

## 1. Directory Sitemap & Codebase Layout

```
RM-Maker-MAIN/
├── AGENTS.md                          # CRITICAL project rules and developer constraints (Do NOT violate)
├── PROJECT_GUIDE.md                   # This onboarding and architecture documentation
├── app.py                             # Core Flask backend server (handles session management, routing, compilation)
├── requirements.txt                   # Backend Python dependencies (google-genai, docxtpl, python-docx, etc.)
│
├── modules/                           # Core business logic modules
│   ├── rm/                            # Registered Mortgage (RM) Pipeline
│   │   ├── extractor.py               # AI data extraction from PDFs/images via Gemini (Locked)
│   │   ├── processor.py               # Jinja context normalization & Word template rendering
│   │   └── schema.py                  # Database serialization, pruning, and validation schema (Locked)
│   │
│   └── sd/                            # Sale Deed (SD) Pipeline
│       ├── extractor.py               # AI data extraction via Gemini (Locked)
│       ├── processor.py               # Jinja context normalization & Word template rendering
│       └── narrative.py               # Specialized title-chain Hindi narrative sentence compiler
│
├── extensions/                        # Chrome Extension for portal feeding automation
│   └── epanjiyan_autofill/
│       ├── manifest.json              # Extension manifest (v3, matches *.rajasthan.gov.in)
│       ├── popup.html / popup.js      # Extension popup UI and user-triggered actions
│       └── content.js                 # Core automation script, observer, and state machine loop
│
├── templates/                         # Word (.docx) templates grouped by Bank
│   ├── CAPRI/, CHOLA/, HFFC/, ICICI/  # Bank folders containing index-mapped documents
│   └── SALE_DEED/                     # Sale Deed templates mapped by Sellers/Buyers count
│
├── web_templates/                     # Jinja2 HTML layouts for the web application UI
│   └── case.html                      # The primary, dense verification and editing dashboard
│
├── agent_knowledge/                   # Contextual documentation, audits, and plans
│   └── ARCHITECTURE/
│       ├── IMPLEMENTATION_MASTER_CONTEXT.md # Master context, Canonical Data Model details
│       └── EPANJIYAN_FEEDING_WORKFLOW.md   # Detailed Chrome Extension auto-run documentation
│
└── cases/                             # Active cases directory (JSON sessions and uploaded raw files)
    └── case_<case_id>/
        ├── session.json               # Temporary JSON-based database for the case session
        └── files/                     # Raw uploaded PDF and JPEG documents
```

---

## 2. Core Architectural Pipelines

### A. AI Extraction Pipeline (`extractor.py`)
* The system utilizes the `google-genai` SDK to call Google Gemini (`gemini-2.5-flash`).
* When files (PDFs/images) are uploaded, they are read as binary parts and sent **in a single payload** along with a detailed prompt describing the required JSON structure.
* **Registered Mortgage (RM) Identity Funneling:** In RM mode, all identity document extractions (Aadhaar cards, PAN cards) are routed exclusively into `unassigned_aadhars`. They are never mapped directly to borrowers or witnesses during extraction.

### B. Session Merging & Save Flow (`app.py`)
* The backend does not use an external database; it uses a local, temporary JSON file-based database in `cases/case_<case_id>/session.json`.
* When the user edits values in the UI and clicks save, the UI sends a POST request to `/case/<case_id>/save`.
* The `smart_merge` function in `app.py` reconciles the incoming edits with the existing `session.json`, using the canonical legacy keys (e.g. `adr`, `id`, `a`, `dob`).

### C. Context Compilation & Padding (`processor.py`)
* To prevent `IndexError` crashes in the Word document rendering layer (e.g. if the template references `bs[1]` but the case only has 1 borrower), the processor automatically pads the list arrays (`bs`, `ls`, `ps`, `ws`, `ds`) with blank dictionaries matching the schema default values.
* Custom filters (like `basename`) are registered in Jinja to format file paths safely.

### D. DevLys Legacy Font Conversion
* Legal documents in the Jaipur region are compiled using legacy Devanagari Hindi encodings (specifically `DevLys 010` or `Kruti Dev`).
* The rendering engine translates Unicode Devanagari text to DevLys characters at the compilation edge using `Unicode_to_KrutiDev` right before writing to the Word XML elements.

---

## 3. Chrome Extension Portal Automation

Located under `extensions/epanjiyan_autofill/content.js`.

### A. Auto-Run State Machine Sequence
When the user clicks the **⚡ Auto-Run: New Valuation → Duty** button, the state machine is initialized in storage and runs the following sequential steps:

1. **Dashboard:** Auto-clicks "+ Add New Valuation", selects District.
2. **Valuation Page:** Fills document details (SRO, Tehsil, Type, Subtype), clicks save.
3. **SweetAlert Success Dialog:** Listens for success popup and auto-clicks OK.
4. **PropertyDetail Intermediate Page:** Identifies URL redirect and auto-clicks "Calculate Duty".
5. **CalculateDuty Page:** Autofills execution date and loan face value, triggers Pass 1 "Calculate & Save".
6. **Pass 2 Calculation:** Pauses 2.5 seconds, commits redirect state to storage, and triggers Pass 2 "Calculate & Save" click.
7. **PropertyDetail Intermediate Page:** Identifies redirect and auto-clicks "Party Detail >" button (with programmatic post submit fallback).
8. **Viewparty list:** Enters the sequential party autofill loop.

### B. Multi-Party Sequence Details (`awaiting_executant_autofill` state)
Once on the Party Details page, the script executes a sequential loop to add all required parties:
1. **On `/Party/Viewparty` (Party List Page):**
   * Automatically clicks the party type button (Executant, Claimant, or Witness).
   * Automatically selects `"Public"` verification type and `"Without OTP Verification"` in the dialog, then clicks `"Submit"`.
2. **On `/Party/PartyAdd` (Form Details Page):**
   * Autofills the fields (name, relation, age, address, ID).
   * Saves the next transition state to storage first (to avoid race conditions).
   * Pauses `1.2` seconds for page validators to settle.
   * Clicks the **Save** button (`#saveDetail`).
   * Polls every `200ms` for the SweetAlert2 popup (`button.swal2-confirm` / "OK") and clicks it to trigger the redirect back to the party list.
3. **Loop:** Repeats for `Executant` $\rightarrow$ `Claimant` $\rightarrow$ `Witness 1` $\rightarrow$ `Witness 2` $\rightarrow$ `flow_completed`.

### C. Continue From Anywhere Testing Capability
`startAutoRunFlow()` detects the current browser URL:
* If the user is on the Valuation page, it starts directly from Valuation details.
* If the user is on the intermediate PropertyDetail page, it starts directly from stamp duty calculation.
* If the user is on the Party Details list, it starts directly from the Executant autofill sequence.
This isolates testing to the specific phase.

---

## 4. Key Developer Constraints

All future agents must strictly follow these rules (documented in `AGENTS.md`):
1. **DO NOT MODIFY EXTRACTION CODE:** Do not touch `modules/sd/extractor.py`, `modules/rm/extractor.py`, `modules/rm/schema.py`, or `utils/helpers.py` without consent.
2. **PRESERVE DEVANAGARI UNICODE IN UI:** All browser UI text areas and text fields must be styled in clean Unicode fonts (e.g. `Segoe UI`, `Mangal`). Legacy encodings (like `DevLys`) are strictly restricted to the backend Word compilation stage.
3. **PRESERVE DIGIT TRANSLATION:** Devanagari numerals (`०-९`) must be converted to English digits (`0-9`) globally (during extraction, loading, and saving).
4. **SAVE STATE BEFORE REDIRECT CLICKS:** In the Chrome Extension, always commit state changes to storage *before* executing `.click()` or `.submit()` calls that unload the page. This prevents race conditions where timeouts are cut off.
