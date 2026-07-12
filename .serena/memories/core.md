# Core Project Memory

Welcome to **RM-Maker** / **LegalDoc Automator Pro**. This codebase automates the generation of Indian legal documents (Registered Mortgages (RM) and Sale Deeds (SD)) from raw OCR/scans (Aadhaar, PAN, and deed drafts) using LLMs (specifically Google Gemini), and facilitates real-time data editing, verification, and browser-extension-based autofilling into government portals (e-Panjiyan).

## Master Memory Index

To navigate this codebase, refer to the following memories:
- **Tech Stack**: `mem:tech_stack` (Python, Flask, TailwindCSS, python-docx, Chrome extensions).
- **Suggested Commands**: `mem:suggested_commands` (Environment setup, dev servers, Tailwind watch/minify, packaging).
- **Conventions & Constraints**: `mem:conventions` (KYC protection rules, Hindi Devanagari Unicode standards, digit normalization).
- **Verification & Task Completion**: `mem:task_completion` (How to verify work, testing checklists).
- **Document Generation Pipeline**: `mem:doc_generation` (DocxTemplate, zipfile formatting, run font replacements).
- **Registered Mortgage (RM) System**: `mem:rm_architecture` (RM extractions, unassigned Aadhaar workflows, RM schemas).
- **Sale Deed (SD) System**: `mem:sd_architecture` (SD extractions, title chain parsing, narrative generation).
- **Template Builder System**: `mem:template_builder` (Tkinter GUI tool for mapping Jinja tags inside `.docx`).
- **e-Panjiyan Autofill Extensions**: `mem:epanjiyan_extensions` (Chrome extensions for automated data entry on government portal).
- **KYC & Relation Workflow**: `mem:kyc_workflow` (Aadhaar pairing, parentage/spousal splitting into `r`/`rn`, gender extraction).
- **AI Provider Adapters**: `mem:ai_adapters` (Gemini SDK integration, key rotation, failover, page-prefiltering).
- **DevLys & Unicode Handling**: `mem:devlys_unicode_handling` (Devanagari Unicode in UI vs. Legacy DevLys/KrutiDev encoding compiler).
- **Critical Files**: `mem:critical_files` (Key file catalog, descriptions).

## Agent Knowledge Base
The repository houses an agent knowledge base in `agent_knowledge/` which maps core architectures, fragile zones, decisions, and historic bug prevention strategies:
- **Architecture**: `mem:agent_knowledge/architecture` (detailed breakdown of RM/SD pipelines, template engines, and modules).
- **Historical Bugs**: `mem:agent_knowledge/historical_bugs` (lessons learned on font conversions, salutations, Aadhaar pairing, e-Panjiyan races, and template regressions).
- **Architectural Decisions**: `mem:agent_knowledge/decisions` (principles of AI data extraction vs. Word template formatting, Unicode internal/legacy external representation, and pipeline isolation).
- **Fragile Systems**: `mem:agent_knowledge/fragile_systems` (catalog of risk zones: docx runs, AJAX selectors, case.html jQuery bindings, session file locking).

## High-Level Architecture

The system follows a clean modular design split between:
1. **Flask Backend (`app.py`)**: Directs HTTP requests, serves web templates, manages session cases, and interfaces with extractors/processors.
2. **AI Extractor Layer (`modules/sd/extractor.py`, `modules/rm/extractor.py`)**: Uses the Gemini API to extract structured entities (borrowers, sellers, witnesses, loans, properties) from scanned/searchable PDFs and images.
3. **Template Compilation Layer (`modules/sd/processor.py`, `modules/rm/processor.py`)**: Coerces field formats, parses relations, and translates Unicode Hindi into DevLys/Kruti Dev legacy fonts during `.docx` generation.
4. **Data Verification UI (`web_templates/case.html`)**: Beautiful, high-end Tailwind web interface with integrated real-time English-to-Hindi transliteration API hooks.
5. **Autofill extensions (`extensions/`)**: Browser extensions loaded by operators to inject case sessions directly into e-Panjiyan portal forms.
