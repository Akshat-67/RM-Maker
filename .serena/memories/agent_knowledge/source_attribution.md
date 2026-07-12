# Field-Level Source Attribution

Field-level source attribution maps extracted case values directly to their sources (document filename, page, bounding box coordinates).

## Backend Integration
- The AI extraction pipeline (`modules/rm/extractor.py` and `modules/sd/extractor.py`) has been extended to ask the Gemini model to return an `extractions` dictionary alongside main data.
- This dictionary maps key paths (e.g. `bs.0.n`) to objects containing:
  - `source_file`: The filename of the source document.
  - `page_number`: The page where the fact was located.
  - `extracted_text`: The raw text of the fact.
  - `bounding_box`: The bounding box coordinates `[y1, x1, y2, x2]` (or null).
- In `routes/cases.py`, this metadata is stored in the top-level keys `extractions` and `confidence_scores` of the session JSON file, preserving backward compatibility.

## Frontend Ergonomics
- In `workspace_preview.js`, focusing an input field calls `snapPreviewToFieldSource` which:
  - Resolves the matching page number and filename.
  - Switches the preview iframe to target this page.
  - Renders a small inline source chip (e.g. `📄 Aadhaar.pdf P1`) next to the active field label.
  - Draws a highlight overlay `previewHighlightOverlay` on the preview viewport if `bounding_box` coordinates are provided.
