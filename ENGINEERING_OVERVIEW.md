# Engineering Overview

Welcome to the LegalDoc Automator (v3) project. This document provides a high-level engineering overview of the system's execution flow, data pipelines, and core components.

## Full Request Lifecycle

The application follows a stateless web server pattern (via Flask) where state is persisted to the local file system.

1. **Initialization:** User visits the dashboard (`/`). Existing cases are loaded from the `cases/` directory by parsing `session.json` files.
2. **Case Creation/Selection:**
   - A new case generates a unique timestamp-based ID (`/new_case`), creating a corresponding folder and `session.json`.
   - The user selects the bank, document type (Registered Mortgage - RM or Sale Deed - SD), and expected entity counts (borrowers, loans, properties) via the UI, which saves to the session.
3. **Document Upload:** User uploads source documents (PDFs, images) via the UI. These are saved to `cases/<case_id>/files/`.
4. **AI Automation (Extraction):** User triggers automation (`/case/<id>/ai`).
   - The app delegates extraction to `extractor.py`.
   - The document is sent to the Google Gemini API along with a highly specific prompt.
   - The raw JSON response is parsed and normalized.
5. **Data Merge:** The extracted data is merged into the existing session data using `smart_merge`, which protects previously verified fields.
6. **Verification & Editing:** The user reviews the extracted data in the UI and toggles fields as "verified". The session state is continuously updated.
7. **Document Generation:** User triggers generation (`/case/<id>/generate`).
   - The app selects the appropriate Word template (`.docx`) based on the case configuration.
   - `processor.py` injects the JSON state into the template using `docxtpl`.
   - The final document is saved to the case directory and sent to the user as a download.

## Important Modules

- **`app.py`:** The main Flask application. Handles routing, session management (JSON file read/write), the `smart_merge` algorithm, and UI rendering.
- **`extractor.py`:** Houses the `DataExtractor` class. Manages Gemini API interactions, prompt engineering, key rotation failovers, and rigorous data normalization (e.g., currency formatting, Hindi transliteration).
- **`processor.py`:** Contains the `TemplateProcessor`. Wraps `docxtpl` and `python-docx` to handle template injection, legacy font conversions (Unicode to DevLys/KrutiDev), and optional document highlighting.
- **`template_tools/template_builder.py`:** A standalone utility for administrators to map variables and generate new master `.docx` templates.

## Data Flow

1. **Input:** Raw PDFs/Images (from user) + Case Configuration (UI dropdowns).
2. **Extraction:** Gemini API processes Input -> Raw JSON.
3. **Normalization:** `extractor.py` processes Raw JSON -> Cleaned Python Dict.
4. **State Management:** `app.py` uses `smart_merge(Existing State, Cleaned Dict)` -> Updated State (saved to `session.json`).
5. **Output:** Updated State + Master `.docx` Template -> `processor.py` -> Final `.docx` Document.

## Case/Session Management

The application completely bypasses a traditional database in favor of a file-based storage system.
- All state resides in the `cases/` directory.
- Each case has its own folder named with a unique ID (e.g., `case_1715432100`).
- Inside the folder, `session.json` acts as the single source of truth for the case, storing configuration, extracted data, the list of uploaded files, and verified fields.
- Uploaded files are stored in `cases/<case_id>/files/`.
- State is explicitly saved by calling `save_case_session` during any mutation action (uploading, running AI, saving UI edits).

## AI Extraction Pipeline

1. **File Loading:** Files are read from the case's `files/` directory.
2. **Prompt Construction:** `extractor.py` dynamically builds a prompt based on the document type (RM vs SD) and expected entity counts to enforce output structure.
3. **API Call:** The `google-genai` client sends the prompt and file payload to the Gemini API. The system handles quota limits via a round-robin API key failover mechanism.
4. **Parsing & Normalization:** The response is strictly parsed as JSON. The `_normalize_response` method is then applied to:
   - Ensure list lengths match expectations (padding with empty objects if necessary).
   - Format dates (e.g., swapping slashes for dots).
   - Convert numerical currency to Indian format words.
   - Format salutations and relation strings cleanly.
   - Perform Hindi transliteration if required (for SD documents).

## Template Generation Pipeline

1. **Resolution:** The correct template is determined by checking the `template_map` against the selected bank, borrower count, and loan count.
2. **Padding:** Data arrays (bs, ls, ps, ws) are forcibly padded to 10 empty elements to prevent Jinja2 out-of-bounds errors during rendering.
3. **Conversion:** The `TemplateProcessor` intercepts the data context and converts any Unicode Hindi strings to legacy ASCII encodings (KrutiDev/DevLys) if the template uses those older fonts.
4. **Rendering:** `docxtpl` renders the document.
5. **Post-Processing:** If highlighting is enabled, `python-docx` is used to surgically highlight unverified or AI-generated fields in the generated document body (avoiding headers/footers to prevent corruption).

## Common Debugging Entry Points

- **UI not reflecting extracted data:** Check the `smart_merge` logic in `app.py`. It prioritizes verified fields and existing keys in arrays.
- **Gemini API Failures:** Check the `raw_generate` and `extract_with_ai` methods in `extractor.py`. Verify that the active API key has not exhausted its quota and that the failover logic is triggering correctly.
- **Template Rendering Crashes (Jinja2 Errors):** Usually caused by missing list elements. Check the padding logic in the `/case/<case_id>/generate` route in `app.py` or `_pad_indexed_lists` in `processor.py`.
- **Garbage Characters in Output Document:** This is an encoding issue. Ensure `Unicode_to_KrutiDev` in `processor.py` is correctly processing the strings, and that the template itself is formatted with the appropriate font.
