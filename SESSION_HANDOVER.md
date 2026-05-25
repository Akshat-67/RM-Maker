# Session Handover - LegalDoc Automator v4

## Current Status
- **UI:** `app.py` has been updated with a professional Tkinter UI. It now features a scrollable left panel to ensure all sections (Case Settings, Upload Documents, AI Configuration) and the "START AI AUTOMATION" button are visible on all screen sizes.
- **AI Integration:** Migrated to the new `google-genai` SDK. Standardized content handling (images/PDFs/text). Prompts are optimized for minimal AI usage, focusing only on data extraction.
- **Master Template Creator:** `template_tools/template_builder.py` is fully functional with an "Indestructible" replacement engine that handles Word's run-splitting. It now handles all header/footer types and tables.
- **Logic:** `extractor.py` handles Indian currency (Lakh/Crore) accurately. Field naming (`id` for Aadhar) is synchronized across the app.

## Key Files
- `app.py`: Main RM Generator application.
- `extractor.py`: AI extraction logic using Gemini.
- `processor.py`: `docxtpl` wrapper for rendering.
- `template_tools/template_builder.py`: Expert mode tool for creating `.docx` master templates.
- `template_tools/TAGS_REFERENCE.md`: List of all available Jinja2 tags.

## Pending / Future
- The user may want to verify extraction accuracy with specific documents in `docs/tests`.
- More bank templates (Home First, Piramal) can be created using the `template_builder.py`.

## Notes for Reviewer
- The UI uses a Canvas + Scrollbar for the left panel. The `left_p` frame is where all widgets are packed.
- `extractor.py` uses `types.Part` for multimodal inputs.
- `template_builder.py` uses a sophisticated regex-based replacement on joined run text to preserve formatting.
