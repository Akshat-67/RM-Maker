# Contributing Guide for AI Agents

Welcome, AI Engineer. This document outlines the strict guidelines, coding conventions, and workflow expectations for modifying the LegalDoc Automator application.

## Workflow Expectations (The GSD Protocol)

This repository operates strictly on the "Get Shit Done" (GSD) meta-prompting methodology.

1. **SPEC:** Define the requirements in `.gsd/SPEC.md`. Do not write code until the specification is marked as `FINALIZED`.
2. **PLAN:** Decompose the work into atomic steps using the orchestrator's planning tools.
3. **EXECUTE:** Implement changes exactly as planned.
4. **VERIFY:** Prove the change works (using file reads, bash execution, or frontend verification). "Trust me, it works" is strictly banned.
5. **COMMIT:** One conceptual task = one atomic commit. Follow conventional commit formats: `type(scope): description`.

## Coding Conventions

- **Flask Only:** Ignore any Tkinter implementations found within merge conflict markers. The canonical implementation is the Flask web application.
- **Stateless Web, Stateful Disk:** Do not introduce in-memory global state. All case state must be persisted to and read from `cases/<case_id>/session.json`.
- **Defensive Data Handling:** The AI output is unpredictable. Always use `.get()` with defaults when accessing dictionaries returned by the AI.
- **Single Responsibility:** Keep Flask routing in `app.py`, AI interaction in `extractor.py`, and document manipulation in `processor.py`.

## Dangerous Areas to Avoid

- **`cases/` Directory:** Never write code that assumes the structure of the cases directory will remain static or that cleans it up arbitrarily.
- **Hardcoding AI Models:** Do not hardcode a specific model version unless absolutely necessary. Rely on the dynamic model fetching available in `extractor.py`.
- **Modifying Templates Directly:** Do not edit the `.docx` files in `templates/` using automated scripts unless specifically instructed. Use `template_builder.py` for template mapping.

## How `smart_merge` Works

The `smart_merge(old, new, verified_fields, path)` function in `app.py` is the core mechanism for updating state incrementally.
- It recursively traverses dictionaries and lists.
- If a field path (e.g., `bs.0.n`) is in the `verified_fields` set, the function immediately returns the `old` value, ignoring the `new` value from the AI.
- For specific entity lists (`ls`, `ps`, `unassigned_aadhars`), it merges items based on a unique key (e.g., matching Aadhaar numbers or Property Addresses) rather than array indices to prevent array shifting during incremental uploads.

## How Extractor Normalization Works

The `_normalize_response` method in `extractor.py` intercepts the raw JSON from Gemini before it reaches the application.
- **Enforcement:** It ensures the counts of entities (borrowers, loans) exactly match the user's configuration, padding the output with empty dictionaries if the AI hallucinated fewer entities.
- **Legal Formatting:** It cleans Parentage strings (stripping "S/o", "W/o" from addresses), forces dates to use dot notation (`15.04.2024`), and uses the `num2words` library to ensure currency values match Indian legal standards (Lakh/Crore logic).
- **Hindi Transliteration:** For Sale Deeds (`SD`), it enforces Devanagari Hindi outputs.

## How Templates are Processed

The `TemplateProcessor` in `processor.py` manages the final document generation.
- **Data Injection:** Uses `docxtpl` (Jinja2 syntax) to inject the JSON state into the Word document.
- **Legacy Fonts:** If the template expects legacy Hindi fonts (KrutiDev/DevLys), `processor.py` intercepts the data and runs it through character-replacement algorithms before injection.
- **Highlighting:** After injection, it scans the generated document body (avoiding headers/footers) using `python-docx` to apply yellow highlighting to fields that were not marked as verified in the UI.

## "Before Changing Anything" Checklist

1. [ ] Have I searched the codebase (`grep`) instead of reading entire files unnecessarily?
2. [ ] Are there existing Git merge conflicts I need to navigate around or resolve?
3. [ ] Is my plan documented and approved by the user?
4. [ ] If I am changing extraction logic, have I reviewed the prompt strings in `extractor.py`?
5. [ ] If I am changing UI state, have I updated how `save_case_session` handles it?

## How to Safely Test Changes

Because there is no automated test suite, you must test manually and defensively:
1. **Extraction Changes:** Use `run_in_bash_session` to write a small script that instantiates `DataExtractor` and passes it a sample document or string to verify your normalization logic doesn't crash.
2. **Merge Changes:** Create dummy dictionaries in a Python REPL within the bash session and run them through the `smart_merge` function to verify the output.
3. **Frontend Changes:** Always run the `frontend_verification_instructions` Playwright scripts to capture screenshots of your UI changes to prove they render correctly.