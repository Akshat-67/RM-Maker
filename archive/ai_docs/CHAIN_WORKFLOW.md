# Title Chain Workflow Architecture (`CHAIN_WORKFLOW.md`)

This document details the end-to-end processing pipeline for generating the Title Chain section in Sale Deeds, based on real-world JDA/Society patterns.

## 1. Legal Report (Source)
The workflow starts with the upload of a **Title Search Report (TSR)** or scanned copies of previous registry documents. The text is often a narrative history of ownership spanning 10-40 years.

## 2. Chain Extraction (AI Pipeline)
The Gemini AI processes the document via `extractor.py`.
- **Extraction Directive**: Parse the chain of title into an ordered JSON array (`title_chain[]`).
- **Translation / Script Standard**: The AI must return all names, document types, and office locations in **Unicode Hindi**, regardless of whether the source document was in English or Hindi.
- **Mandatory Registration Data**: Book, Vol, Page, and Serial Number must be isolated.

## 3. Chain Review (Workspace UI)
The `case.html` workspace renders the array into manageable chronological cards.
- **Validation**: The Quality Assistant verifies that registration numbers and dates are not empty.
- **Correction**: Operators can use the dynamic row manager (`addListRow('tc')`) to append missing events (like an intermediate POA) or use `Ctrl+G` (Hindi preview) to correct transliteration errors.

## 4. Chain Storage (Session State)
Data is saved into `session.json` purely as Unicode strings.

## 5. Chain Rendering (Template Processor)
When the final `.docx` is requested:
- **Jinja2 Loops**: The Word template uses dynamic loops rather than hardcoded fields for historical events:
  ```jinja2
  {% for tc in title_chain %}
  {{ tc.event_narrative_paragraph }}
  {% endfor %}
  ```
  *(Note: The `event_narrative_paragraph` is logically constructed either inside the python processor based on `CHAIN_EVENT_LIBRARY.md` patterns, or coded explicitly in the Jinja2 template with if/else blocks checking `tc.event_type`).*

## 6. SD Generation (Word Output)
The final stage is formatting for the legacy legal environment.
- The `TemplateProcessor` converts the populated Unicode Hindi text back into **DevLys 040** ASCII.
- It applies the `<w:rFonts w:ascii="DevLys 040"... />` XML formatting, guaranteeing that the complex multi-stage title history prints correctly for sub-registrar submission.