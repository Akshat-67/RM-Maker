# SPEC.md — Project Specification

> **Status**: `FINALIZED`
>
> ⚠️ **Planning Lock**: No code may be written until this spec is marked `FINALIZED`.

## Vision
The LegalDoc Automator (v5) is a premium, web-based automation platform designed to assist law firms in generating error-free Registered Mortgage (RM) documents. By transitioning from a Tkinter GUI to a highly responsive and aesthetically refined Flask web application, and integrating advanced multi-case session management with smart-merging OCR capabilities (via Gemini API), the application eliminates layout truncation, supports incremental document scrutiny, and ensures absolute data integrity.

## Goals
1. **Flask-Based Cross-Platform Web Interface** — Replace the legacy Tkinter desktop UI with a robust web interface featuring a modern dashboard and a highly interactive, dual-panel case workspace.
2. **Multi-Session Case Management Dashboard** — Support starting a new case, listing all active cases with recent metadata, deleting old cases, and resuming saved case sessions.
3. **Aadhaar Guided OCR & Smart Role Mapper** — Extract Aadhaar card information (Aadhaar ID, exact Aadhar address, age/YOB, relation details) into an unassigned queue, allowing one-click role assignment (Borrower 1/2/3, Witness 1/2, or Bank Signatory) with auto-verification locking.
4. **Non-Destructive Smart Merging** — Allow incremental document uploads and OCR processing. Do not overwrite user-modified or verified fields on subsequent extraction runs.
5. **Advanced Data Cleaning & Age Calculation** — Perform accurate age calculation from Aadhaar YOB/DOB as of 2026, dynamic salutation prediction, formatting relative parentage properly, and stripping C/o or S/o parentage prefixes from the start of the address field.

## Non-Goals (Out of Scope)
- Direct cloud database storage (SQLite or local JSON files under `cases/` are sufficient).
- Real-time multi-user collaboration (the system runs locally on a single machine).
- Direct document translation (only Indian documents in standard English/Hindi or simple localized formats).

## Constraints
- **Gemini API Access** — Depends entirely on a valid `GEMINI_API_KEY` for OCR and entity extraction.
- **Word Document Manipulation** — Must use the existing robust regex-based `TemplateProcessor` in `processor.py` for rendering `.docx` documents.
- **Jinja2 Compatibility** — Context keys in final generation must align with the placeholders in templates (`bs`, `ls`, `ps`, `ws`, `bsign`, `ds`, `ds_text`, `second_schedule`).

## Success Criteria
- [x] Flask server launches successfully and serves the dashboard on `http://127.0.0.1:5000`.
- [x] Case sessions are fully persisted to `cases/<case_id>/session.json` and accurately loaded upon resumption.
- [x] Users can upload new documents, and the Gemini API processes them without erasing previously verified fields.
- [x] Calculated age is a pure numeric string based on YOB/DOB as of the year 2026.
- [x] Unassigned Aadhaar cards are displayed in a clean, interactive table and successfully assign values to their respective borrower/witness fields with checkmarks.
- [x] Final `.docx` document correctly generates with highlighted unverified fields (yellow) and missing fields (red, with `[MISSING]` text) without damaging headers, footers, or formatting.

## Technical Requirements

| Requirement | Priority | Notes |
|-------------|----------|-------|
| Web App Architecture | Must-have | Flask + HTML5/CSS3 + Bootstrap 5 |
| Case Persistent State | Must-have | Session JSON with list of processed files |
| Multimodal Extraction | Must-have | google-genai SDK with multimodal PDF/image OCR |
| Smart Merging Utility | Must-have | Respects verified field set, merges dicts/lists recursively |
| Aadhaar Role Assignment | Must-have | Interactive UI mapping logic in JS/HTML |
| Post-Rendering Highlights | Must-have | `docxtpl` in-memory paragraph and run highlight scanner |

---

*Last updated: 2026-05-30*
