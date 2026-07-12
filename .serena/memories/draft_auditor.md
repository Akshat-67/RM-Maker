The Draft Auditor (added in V2.1) is a validation layer designed to check compiled English Registered Mortgage (RM) documents for inconsistencies, omissions, and placeholder leaks.

Key Architecture:
1. **NVIDIA NIM `nemotron-ocr-v2` (`services/ocr_service.py`):**
   - Transcribes scanned KYC/legal PDF and image pages to text.
   - Automatically handles large files exceeding 180,000 base64 chars by uploading them via NVIDIA's Assets API first.
   - Caches the plain text locally in `cases/<case_id>/ocr_cache.json` to prevent repeated OCR charges.
2. **Semantic Auditor (`services/audit_service.py`):**
   - Performs rule-based scanning (leaks like `{{`, duplicate words, bold markup checks).
   - Calls Gemini (2.5/3.5 Flash) on plain cached OCR text vs. compiled draft text, comparing them in a Red-Team audit role and outputting a JSON list of warnings.
3. **Interactive Autofixes (Option A):**
   - Accessible via the **🔍 Draft Auditor** tab in `review.html`.
   - Click "Fix" on mismatches to update input form values in the database, automatically updating input forms and updating the Word preview in real-time.