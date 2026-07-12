# Agent Knowledge: Architecture

This memory summarizes the system design and pipeline paths of LegalDoc Automator (RM-Maker) detailed in [architecture.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/agent_knowledge/architecture.md).

## Key Entry Points
- **`app.py`**: Flask server directing REST routes, session loading/saving, and CORS filters.
- **`cases/cases.db`**: SQLite database indexing case statuses and file folders.
- **`cases/case_<id>/session.json`**: Case parameter database.
- **`templates/`**: Word `.docx` templates.
- **`extensions/`**: e-Panjiyan Chrome automation scripts.

## Document Pipelines
- **Registered Mortgage (RM)**: Extracts structured borrower/loan parameters via `RMDataExtractor`, verifies them in the UI (drag-and-drop unassigned Aadhaar cards), and generates documents via `RMTemplateProcessor` after converting Unicode Hindi to legacy DevLys.
- **Sale Deed (SD)**: Extracts buyer/seller entities and title history using `SDDataExtractor`, compiles dynamic Hindi title history narratives in `narrative.py` (referencing `chain_templates.py`), and renders `.docx` via `SDTemplateProcessor`.

## Core Utilities
- **Template Builder (`template_builder.py`)**: Traverses word files and maps manual names to standardized Jinja tag runs (`DocManipulator`).
- **KYC & Relation workflow**: Pairs Aadhaar front/back scans phonetically and splits relationship lines into `r` (relation type) and `rn` (relative name).
- **AI model adapters**: Translates PDFs to plain text using `pypdf`, selects up to 12 target pages, and implements API key rotation.
