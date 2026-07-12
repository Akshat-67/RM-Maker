# AI Confidence Indicators

AI extraction confidence indicators help operators quickly scan for fields that require closer inspection.

## Backend Integration
- Extractor prompts (`modules/rm/extractor.py` and `modules/sd/extractor.py`) request a top-level `"confidence_scores"` dictionary where the Gemini model estimates extraction confidence (float 0.0 - 1.0) and lists a descriptive `"reason"` if the score is under 1.0.
- Stored as `confidence_scores` at the top level of the session JSON document via `save_case_session` in `routes/cases.py`.

## Frontend Layout & Design
- Inputs are styled dynamically inside `workspace_preview.js` via `applyVisualConfidenceBorders()`:
  - **High Confidence** (score >= 0.90): Green left-border (`.confidence-high`) and checkmark badge (`✓`).
  - **Medium Confidence** (0.70 <= score < 0.90): Gold left-border (`.confidence-medium`) and warning badge (`?`).
  - **Low Confidence** (score < 0.70): Red left-border (`.confidence-low`) and critical alert badge (`!`).
- Badges display custom tooltips detailing the exact confidence percentage and explanation reason (e.g. "Image blur on PAN Card scan page") to lower clerk cognitive fatigue.
