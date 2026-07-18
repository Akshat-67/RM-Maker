# Core Codebase Architecture

This document describes the high-level architecture, pipeline flows, repository structure, and critical constraints of the RM-Maker application.

---

## 1. System Pipeline Flow
RM-Maker automates the processing of legal document data using a structured sequence:

```
Upload (PDF/Image) → AI Extraction → Schema Validation → Processing → Context Generation → docxtpl Rendering
```

1. **Upload**: Users upload raw files (PDFs, images, or legacy docs) through the Case Workspace or auto-drop folders into the monitored case inbox.
2. **AI Extraction**: Extractor modules parse facts (parties, loans, properties) using Gemini models.
3. **Schema Validation**: Extracted parameters are validated against strict JSON schemas.
4. **Processing**: Normalizes names, resolves relations, standardizes addresses, and converts numerals.
5. **Context Generation**: Assembles verified fields into Jinja-compatible dictionary payloads.
6. **docxtpl Rendering**: Translates Unicode fields to legacy fonts (DevLys 010/Kruti Dev) at the rendering boundary and compiles the output `.docx` document.

---

## 2. Repository Structure
Below is the role and responsibility of each directory in the workspace:

| Directory | Purpose |
| :--- | :--- |
| `modules/rm/` | Core Registered Mortgage (RM) extraction and template processing scripts. |
| `modules/sd/` | Core Sale Deed (SD) extraction, timeline builders, and narrative generators. |
| `services/` | Shared backend services (auto-cropping, file storage, ingestion pipelines, AI models). |
| `routes/` | Modular Flask blueprints defining Web & API handlers. |
| `templates/` | Master `.docx` templates categorized by bank or document type. |
| `web_templates/` | Jinja HTML templates for the browser dashboard and case workspace. |
| `extensions/` | Chrome extension files for automatic online portal data entry. |
| `tests/` | Unit, integration, and E2E test suites. |
| `utils/` | Shared helpers, configurations, and address parsers. |

---

## 3. High Impact Files
The following files control core business logic and require extra caution before making changes:

- **[modules/rm/](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/)**: Stability is paramount; do not modify RM schema, extractors, or processors unless explicitly requested.
- **[modules/sd/](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/)**: Handles property sales, title chains, and narrative compilation.
- **[utils/helpers.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/utils/helpers.py)**: Houses universal converters, address splitters, and string normalizations.
- **[app.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/app.py)**: Entry point for the server, manages middleware and blueprint registration.
- **[web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)**: The main splitscreen workspace interface and client-side reactive logic.

---

## 4. Architectural Rules & Constraints

### A. Unicode-First Paradigm
- All internal processing (AI extraction, database storage, session serialization, web forms, and schema validations) must use standard Unicode Devanagari.
- Legacy non-Unicode fonts (e.g. `DevLys 010`, `Kruti Dev 010`) are **never** allowed for browser styling, inputs, or database files.
- Legacy encoding is applied **only at the final rendering boundary** immediately before generating the compiled Word document.

### B. Digit Standardizing
- Devanagari numerals (`०-९`) must always be converted to standard English digits (`0-9`) globally. This transformation is applied automatically during AI extraction, session loading, and session saving.

### C. Real-Time Transliteration
- The web interface triggers automatic English-to-Hindi transliteration on field defocusing/Tab by calling `/transliterate` or falling back to the client-side `Sanscript` library. Keep this flow intact.
