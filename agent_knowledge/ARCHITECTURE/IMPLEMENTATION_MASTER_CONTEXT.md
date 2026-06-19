# Implementation Master Context

This document is the definitive single source of truth for all implementation work on the LegalDoc Automator (RM/SD Generator). It consolidates all accepted decisions, architectural rules, domain knowledge, and technical debt findings. **Future implementation agents should read this document instead of scattered historical audits.**

---

## 1. Project Overview

The LegalDoc Automator comprises two isolated pipelines:
*   **RM Generator (`modules/rm/`)**: Handles Registered Mortgages. Typically involves 1-3 borrowers and 1-2 loans.
*   **SD Generator (`modules/sd/`)**: Handles Sale Deeds, primarily in the Jaipur residential market. Features a specialized title-chain narrative engine.

**Architecture Goals:**
Transition from a rapid-prototype to a maintainable, generalized system. The architecture enforces strict separation of concerns: Python code strictly owns business logic (extraction, validation, chronology), while `.docx` templates strictly own presentation logic.

**Supported Workflows:**
Users upload source documents (PDFs, images) -> Gemini AI extracts structured JSON -> Python processor merges data into `session.json` and prepares a Jinja context -> A rendering engine uses `docxtpl` to insert the DevLys-converted context into `.docx` legal templates.

---

## 2. Current Architecture

The system follows a strict linear flow, isolated by document type:

1.  **Extraction Pipeline (`extractor.py`)**: Monolithic, single-pass Google Gemini extraction. Parses source documents into a raw JSON dictionary.
2.  **Normalization Pipeline**: OCR cleanup (e.g., trailing commas, relation standardizations) occurs in the extractor before translation. Generic font conversions (`Unicode_to_KrutiDev`) occur via `utils/helpers.py`.
3.  **Session Generation (`app.py`)**: `smart_merge` reconciles incremental AI extractions with UI saves. Payload is stored as temporary JSON in `cases/`.
4.  **Context Generation**: Currently mixed between `app.py` and `modules/sd/narrative.py`. Prepares data arrays, fallback values, and padding (e.g., hardcoded padding to 10 to avoid Jinja errors).
5.  **Template Rendering (`processor.py`)**: `RMTemplateProcessor` and `SDTemplateProcessor` execute `.docx` tag replacement via `docxtpl`.

*Note: `modules/rm` and `modules/sd` must never cross-import.*

---

## 3. Canonical Data Model

The codebase currently uses legacy shorthand aliases that are tightly coupled to the `.docx` templates. A mass renaming migration is **ON HOLD**. The current implementation reality must be respected:

**Canonical Structures & Aliases in Use:**
*   **Global Entities**:
    *   `address` (Alias in use: `adr`)
    *   `aadhaar` (Alias in use: `id`)
    *   `pan` (Alias in use: `pan`)
    *   `age` (Alias in use: `a`)
    *   `caste` (Alias in use: `c`)
    *   `name` (Alias in use: `n`)
    *   `salutation` (Alias in use: `s`)
    *   `relation_type` (Alias in use: `r`)
    *   `relative_name` (Alias in use: `rn`)
    *   `relation_text` (Alias in use: `relation_text`)
*   **Array Groupings**:
    *   `ss` (Sellers - SD only)
    *   `bs` (Buyers for SD / Borrowers for RM)
    *   `ws` (Witnesses)
    *   `ps` (Properties)
    *   `chain` (Title Chain Events)
*   **Nested Groupings**:
    *   `sale.amount`, `sale.amount_words`, `sale.payment_details`
    *   *Rule: Retain nested structures. Do not flatten for arbitrary consistency.*

---

## 4. Accepted Architectural Decisions

*   **Strict RM/SD Isolation:** Unification of RM and SD processors/extractors is suspended. Keep them isolated.
*   **Deterministic Drafting:** Final legal wording comes from template selection and field population. The LLM is an *extractor of facts*, not a drafter of paragraphs.
*   **Text Replacement Classification:** Not all string replacement is harmful.
    *   *DEVLYS_NORMALIZATION* (e.g., `ç` -> `iz`) is valid and kept in `helpers.py`.
    *   *EXTRACTION_COMPENSATION* (e.g., AI hallucinated commas) is valid but must be moved upstream to the schema/extractor.
    *   *TEMPLATE_COMPENSATION* (Python fixes for typos in Word templates) is valid but targeted for future synchronized removal.
*   **Title Chain Event Preservation:** Preserve explicit legal event types (`WILL`, `GIFT_DEED`, `PARTITION`) in the schema. Do not collapse them into a generic `TRANSFER`.
*   **Technical Debt Removal:** Generated artifacts (`diff.txt`, `.docx` dumps) and case-specific hardcoded scripts (`heal_session*.py`) are confirmed technical debt and must be deleted.

---

## 5. Rejected Decisions

*   **LLM-Generated Legal Narratives:** Rejected. Natively generating final Hindi text via Gemini is prohibited due to the need for strict deterministic control.
*   **Immediate Title-Chain Rewrite / Ownership Graph:** Rejected. The linear array (`CHAIN_SCHEMA.md`) works sufficiently for Sale Deeds. Complex recursive narrative engines or adjacency-list graph rewrites are unnecessary risk.
*   **Rewrite Rendering Pipeline & DevLys System:** Rejected. The current processing pipeline and legacy font conversion engine remain functional and should not be rewritten wholesale.
*   **Flatten All Nested Objects:** Rejected. Removing logical groupings (e.g., `sale.amount`) is forbidden.
*   **Delete All Debug/Test Scripts:** Rejected. Valuable historical investigations must be archived, not blindly deleted.

---

## 6. Extraction Rules

*   **Payload Optimization (Minimum Document Set):** To prevent Gemini API timeouts, never send redundant documents. Filter duplicate WhatsApp images and exclude target output drafts (`.doc` / `.docx`) from the extraction prompt.
*   **Upstream Compensation:** Clean up OCR/AI weaknesses (e.g., stripping trailing commas, standardizing relations like `स्वर्गीय`) as early as possible—inside the extractor or schema validation layer, *not* in the rendering processor.
*   **Field Preservation:** Ensure prompts extract real event types (`WILL`, `GIFT_DEED`) and capture relational metadata (`consideration_type`, `receipt_number`).
*   **Graceful Degradation:** If Gemini API fails during automated tests, gracefully log the failure or use mocked schemas rather than crashing the pipeline.

---

## 7. Template Rules

*   **Ownership Boundaries:** Templates strictly own presentation logic (formatting, wording, `docxtpl` tags). Python code strictly owns business logic (data merging, chronological sorting, relation extraction). Do not place business rules inside Word templates.
*   **DevLys Processing:** Legacy font adjustments and Unicode-to-KrutiDev conversion happen at the Python rendering edge, right before template insertion.
*   **Template Compensation Debt:** Removing Python string matches that fix surgical template typos (e.g., `è` ligatures) is *ON HOLD*. Doing so requires simultaneously modifying the underlying Word XML, which is high-risk.

---

## 8. Domain Knowledge

*   **Allotment Letters:** The root of most title chains (Society or JDA). Typically preceded by the word "सर्वप्रथम". Society allotments often lack a specific `allotment_number`, relying instead on a `receipt_number` (रसीद संख्या). Allotments are legally coupled with "Possession" (कब्जा) and a "Site Plan" (साइट प्लान).
*   **Patta / Lease Deeds:** Primary government land grants (JDA, RHB). Meticulously track registration details (Book, Volume, Page, Serial). Often associated with "Lease Hold to Free Hold" conversions.
*   **Possession Letters:** Formal physical handover. JDA/RHB issue explicit Possession Letters. In private resales, possession is documented purely as a narrative declaration within the Sale Deed ("भौतिक कब्जा").
*   **Title Chain Patterns:** Dominant chronological flow: *Origin (Allotment/Lease) -> [Optional Sales/Gifts] -> Final Sale*.

---

## 9. Security Rules

*   **Credential Loading:** Strict reliance on `.env` loaded via standard mechanisms. No hardcoded credentials in the repository.
*   **Multi-Key Gemini System:** The extractor handles Gemini API rate limits. Fallback mechanisms may involve hardcoded key rotation logic inside the extractor class to maintain availability during heavy validation runs.
*   **Local Storage:** The system uses a local, temporary JSON file-based storage mechanism in `cases/`. There is no built-in authentication or authorization for these temporary files.
*   **Git Security:** Use targeted `.gitignore` patterns (e.g., `diff*.txt`, `test_out.docx`) to exclude sensitive generated case data, while preserving legitimate template `.docx` files.

---

## 10. Technical Debt Register

*   **Accepted (Actionable Debt):**
    *   Root directory clutter and generated artifact dumps.
    *   Hardcoded case-specific healing scripts (`heal_session*.py`).
    *   Fragmented array padding and data healing logic across `app.py`.
*   **Deferred / On Hold:**
    *   Canonical Field Renaming Migration (Updating all legacy `.docx` tags).
    *   Removing TEMPLATE_COMPENSATION rules.
    *   Full `app.py` modularization (Flask Blueprints).
    *   Ownership Graph / Title Engine abstraction.
    *   RM/SD BaseExtractor & BaseProcessor Unification.
*   **Rejected:**
    *   Full DevLys subsystem rewrite.
    *   LLM native drafting.

---

## 11. Implementation Priorities

1.  **Highest Value / Highest Impact:** Gemini API Payload Optimization. Resolving API `ServerError` timeouts by filtering duplicate images and large irrelevant PDFs from the extraction context.
2.  **Lowest Risk:** Context Generation Relocation. Moving array padding, fallback values, and aliasing logic out of the monolithic `app.py` into dedicated `context.py` files within `modules/rm` and `modules/sd`.
3.  **Medium Priority:** Title Chain Structuring. Formally extract `allotment_letter_no`, `allotment_date`, `receipt_number`, and `issuing_authority` for Allotment/Patta events, preventing them from being handled as generic "Sales".

---

## 12. Agent Operating Instructions

1.  **Do Not Re-Audit Accepted Decisions:** Use this document as the final source of truth. Do not create new architecture proposals to replace accepted patterns.
2.  **No Case-Specific Hardcoding:** Patches fixing specific party names, addresses, or lease numbers are strictly forbidden.
3.  **Respect Canonical Mappings:** Operate using the legacy aliases (`bs`, `ss`, `chain`) currently in place. Do not initiate a mass field-renaming migration.
4.  **Preserve Legal Events:** Extract exact event types (`GIFT_DEED`, `WILL`, `PATTA`). Do not aggressively collapse title chains into generic `TRANSFER` strings.
5.  **Fix Order of Operations:** Always attempt to fix data issues upstream: 1. Extraction -> 2. Schema Validation -> 3. Context Generation -> 4. Python Render Engine. Post-processing string replacement is a last resort.
6.  **Validate Changes:** Run existing tools (`tools/validate_cases.py` or `tests/test_e2e_sd.py`) against at least 3 historical cases to ensure any logic changes do not break backward compatibility.
7.  **Maintain Strict Isolation:** Shared code belongs in `utils/` or `core/`. Do not cross-import business logic between `modules/rm/` and `modules/sd/`.
8.  **Knowledge Preservation:** Store any new significant findings or audits in `agent_knowledge/`. Do not leave status documents in the repository root.
