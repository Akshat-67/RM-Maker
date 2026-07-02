# Project Memory Index & Architecture Map

This document serves as the canonical memory index and reference guide for future AI agents and developers working on the RM-Maker codebase.

---

## 1. Directory Sitemap & Codebase Layout

```
RM-Maker-MAIN/
├── AGENTS.md                          # CRITICAL project rules and developer constraints (Do NOT violate)
├── MEMORY.md                          # This comprehensive architecture and memory index
├── PROJECT_GUIDE.md                   # Onboarding sitemap and Chrome Extension workflows
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
│       └── narrative.py               # Title-chain Hindi narrative sentence compiler
│
├── extensions/                        # Chrome Extension for portal feeding automation
│   └── epanjiyan_autofill/
│       ├── manifest.json              # Extension manifest (v3, matches *.rajasthan.gov.in)
│       ├── popup.html / popup.js      # Extension popup UI and user-triggered actions
│       └── content.js                 # Core automation script, observer, and state machine loop
│
├── templates/                         # Word (.docx) templates grouped by Bank/Type
│   ├── CAPRI/, CHOLA/, HFFC/, ICICI/  # Bank folders containing index-mapped documents
│   └── SALE_DEED/                     # Sale Deed templates mapped by Sellers/Buyers count
│
├── web_templates/                     # Jinja2 HTML layouts for the web application UI
│   └── case.html                      # The primary, dense verification and editing dashboard
│
├── cases/                             # Active cases directory (JSON sessions and uploaded raw files)
│   └── case_<case_id>/
│       ├── session.json               # Temporary JSON-based database for the case session
│       └── files/                     # Raw uploaded PDF and JPEG documents
```

---

## 2. Core Architectural Pipelines

### A. AI Extraction Pipeline (`extractor.py`)
- **API and Keys:** Powered by the `google-genai` SDK (`gemini-2.5-flash`). API key rotation and NVIDIA NIM fallbacks are built-in.
- **Rules & Logic:**
  - **Identity Funneling (RM):** All uploaded identity documents (Aadhaar, PAN) are funneled exclusively into `unassigned_aadhars`. They are never mapped directly to borrowers or witnesses during extraction.
  - **Witness OCR Isolation:** Witness details must not be extracted into `unassigned_aadhars`.
  - **Multi-Image Pairing:** The front and back of Aadhaar cards are paired into a single dictionary entry.
  - **Digit Translation:** Devanagari numerals (`०-९`) are universally converted to standard English digits (`0-9`) at the extraction level.

### B. Session Merging & Save Flow (`app.py`)
- **Storage:** Local JSON file-based database per case at `cases/case_<case_id>/session.json`.
- **Merge Logic:** UI edits sent via POST to `/case/<case_id>/save` are reconciled using `smart_merge` in `app.py`. It synchronizes long keys (from AI extraction) and short keys (from UI inputs), formats addresses, and translates numerals.

### C. Context Compilation & Padding (`processor.py`)
- **IndexError Protection:** Padds array lists (`bs`, `ls`, `ps`, `ws`, `ds`) with default empty dictionaries matching the schema.
- **Highlighting:** Highlights AI-extracted (yellow) and missing (red) fields, except for the title chain/document list.
- **Substitutions:** Automated cleanups for common word/character/ligature substitutions (e.g. `Lo- Jh` -> `LoxhZ; Jh` or `mRrjkf/kdkjh`).

### D. DevLys Font Conversion
- **Compilation Edge:** Hindi legal documents in the Jaipur region require legacy non-Unicode encodings (`DevLys 010` / `Kruti Dev`).
- **Mapping:** The backend performs character translation (`Unicode_to_KrutiDev`) right before writing to the Word XML elements.

---

## 3. Chrome Extension Portal Automation

Located under `extensions/epanjiyan_autofill/content.js`.

- **Sequence:** valuation → calculate duty (Pass 1 & 2) → party details.
- **Party Autofill Loop:**
  - On `/Party/Viewparty` (Party List Page): Clicks the type button (Executant, Claimant, or Witness), submits verification dialog.
  - On `/Party/PartyAdd` (Form Details Page): Autofills fields, saves transition state to storage first, pauses `1.2` seconds, clicks save, and handles SweetAlert2 popups.
- **Race Condition Prevention:** The extension commits state changes to local storage *before* executing redirect clicks or form submissions to prevent losing track during page unloads.

---

## 4. Critical Rules & Constraints (from `AGENTS.md`)

1. **Extraction Code Lock:** Do NOT modify `modules/sd/extractor.py`, `modules/rm/extractor.py`, `modules/rm/schema.py`, or `utils/helpers.py` without explicit user consent.
2. **Universal Digit Conversion:** Ensure Devanagari numerals (`०-९`) are converted to English digits (`0-9`) globally at extraction, loading, and saving.
3. **Typographic Standard:** The verification UI must present Hindi text in clean Unicode Devanagari font (`Segoe UI` or `Mangal`). Legacy encodings must NOT style browser inputs.
4. **Real-time Transliteration:** Real-time English-to-Hindi transliteration (blur/tab calls to `/transliterate`) must remain intact.
5. **RM Relations Flow:** In RM mode, Aadhaar card extractions go exclusively to `unassigned_aadhars`. Do not modify relation parsing or assignment.