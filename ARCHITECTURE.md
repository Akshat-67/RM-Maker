# Architecture

This document describes the architectural layout, component dependencies, and systemic characteristics of the LegalDoc Automator application.

## Directory Structure

```text
/
├── app.py                      # Main Flask application and routing
├── extractor.py                # AI Extraction logic and normalization
├── processor.py                # Word document generation and formatting
├── requirements.txt            # Project dependencies
├── README.md                   # Project overview and installation instructions
├── cases/                      # (Generated) Local storage for case state and files
│   └── case_<id>/
│       ├── session.json        # Single source of truth for case state
│       └── files/              # Uploaded user documents
├── templates/                  # Master .docx templates mapped by bank/type
├── web_templates/              # HTML/Jinja2 templates for the Flask UI
├── static/                     # CSS, JS, and image assets for the frontend
├── template_tools/             # Utilities for administrators
│   ├── template_builder.py     # Tool to map fields onto new .docx templates
│   └── TAGS_REFERENCE.md       # Reference for available Jinja2 tags
└── .gsd/                       # System metadata and planning (GSD workflow)
```

## Component Responsibilities

1. **Web Server (`app.py`):** Acts as the controller. Manages HTTP requests, reads/writes file-based session state, handles file uploads, merges new AI data with existing state (`smart_merge`), and serves the UI.
2. **AI Extractor (`extractor.py`):** Acts as the data abstraction layer. Communicates with external LLM APIs (Gemini). Encapsulates prompt engineering, API key failover, and strict data normalization rules specific to the legal domain.
3. **Template Processor (`processor.py`):** Acts as the view/rendering engine for documents. Takes clean data from the server and injects it into Word templates safely, handling complex encoding requirements (Hindi transliteration) and formatting (highlighting).

## Dependencies Between Modules

- `app.py` strictly depends on `extractor.py` (for data extraction) and `processor.py` (for document generation).
- `extractor.py` depends heavily on the external `google-genai` SDK and the availability of the Google Gemini API.
- `processor.py` depends on `docxtpl` and `python-docx` for document manipulation.
- Both `extractor.py` and `app.py` depend directly on the local filesystem (`cases/`) for inputs and outputs.
- `template_tools/template_builder.py` is an isolated tool that does not depend on the main application, but the main application depends on the templates it produces.

## Critical Paths

1. **State Hydration/Persistence:** The functions `load_case_session` and `save_case_session` in `app.py` are the backbone of the application. Any failure to read/write `session.json` corrupts the case.
2. **Smart Merge:** The `smart_merge` function in `app.py` dictates how manual user edits and AI extractions are reconciled. Bugs here result in data loss or overwritten verified fields.
3. **Extraction Prompting:** The prompt strings defined in `_build_prompt` and `_build_sd_prompt` inside `extractor.py` are critical. Even minor changes to these prompts can drastically alter the shape and quality of the JSON returned by the AI.

## Fragile Areas

- **File-Based Concurrency:** Because the application uses JSON files for state instead of a database, simultaneous requests modifying the same case (e.g., uploading files while an AI extraction is running) can result in race conditions and data corruption.
- **API Key Failover:** The round-robin API key rotation in `extractor.py` relies on a hardcoded list of keys. If all keys exhaust their quotas simultaneously, the extraction pipeline fails entirely.
- **Template Padding Requirements:** `docxtpl` requires lists to exist in the context to avoid index out-of-bounds errors. The logic in `app.py` that forcefully pads arrays (e.g., `while len(data['bs']) < 10`) is a brittle workaround for Jinja2 template strictness.
- **Git Merge Conflicts:** As of the current state, `app.py` and `extractor.py` contain unresolved Git merge markers containing two divergent codebases (Flask vs Tkinter).

## Scaling Concerns

This application is currently designed for single-node, local deployment. It is fundamentally unsuited for horizontal scaling in its current state:
1. **Local Filesystem Dependency:** Instances cannot share `cases/` state easily without a shared network drive (NFS/EFS), which introduces latency and locking issues.
2. **No Database:** The lack of a relational database means queries (like listing all cases) require scanning the disk and parsing numerous JSON files, which is O(N) operations and highly inefficient.
3. **Synchronous AI Calls:** AI extraction blocks the request thread. Under heavy load, the web server will quickly exhaust available worker threads waiting for the Gemini API.

## Technical Debt

- **Missing Authentication/Authorization:** The app assumes total trust. Any user can view, edit, or delete any case.
- **No Test Coverage:** The lack of a formal test suite (unit/integration tests) makes refactoring the complex `smart_merge` or extraction normalization logic highly risky.
- **Hardcoded Secrets:** Default API keys are checked directly into the source code in `app.py` and `extractor.py`.
- **Dual Implementations:** The presence of a Tkinter implementation tangled with the Flask implementation via Git merge markers creates significant confusion and compilation errors.