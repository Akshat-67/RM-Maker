# Title-Chain System Audit
**Date**: 2026-06-17

## Executive Summary
This report evaluates the current title-chain system to determine if the architecture can support future scalability across diverse legal document types over the next 10 years.

**Conclusion**: The current architecture will **not** survive the introduction of complex document types without major rewrites. It is a highly tailored, overfitted engine designed specifically to generate Sale Deeds based on a narrow set of reference documents. The system heavily mixes data, business logic, and presentation layers, and relies on brittle textual substitutions rather than a generic ownership graph.

---

## 1. Generic vs. SD-Specific Components

### What is Generic?
*   **The Schema Concept:** The idea of a `title_chain` array containing sequential events (with fields for dates, parties, and registration details) is broadly applicable.
*   **The LLM Fallback Mechanism:** Key rotation and model fallback logic in `extractor.py` is generic to any AI task.

### What is SD-Specific?
*   **Location of Logic:** Almost all title-chain logic lives inside `modules/sd/` (specifically `extractor.py`, `narrative.py`, `schema.py`, and `processor.py`).
*   **Classification Collapse:** The prompt in `extractor.py` explicitly forces the LLM to map nuance (Gift Deeds, Relinquishment, Wills, Partition) into a generic `"TRANSFER"` event type, destroying the semantic meaning needed for anything other than a Sale Deed historical narrative.
*   **Presentation Generation:** The templates in `chain_templates.py` (`SALE_DEED_FLAT`, `ALLOTMENT_PLOT`, etc.) are heavily tailored to the phrasing needed for the current Sale Deed outputs.

---

## 2. Layer Mixing

The system currently violates the separation of concerns, heavily mixing the Data, Business Logic, and Presentation layers.

*   **Data & Presentation:** The extraction prompts instruct the LLM to format addresses into specific formal strings rather than pure structured data (e.g., instructing the LLM to output "पुत्र श्री" instead of capturing the parent's name cleanly).
*   **Logic & Presentation:** `narrative.py` handles business logic (deduplication, chronological sorting, resolving the 'builder' entity for construction events) *and* directly invokes presentation templates.
*   **Presentation Post-Processing:** `processor.py` intercepts the generated strings and applies highly specific, hardcoded regex and text replacements to force the output to match a reference document's exact stylistic quirks (e.g., replacing spaces, fixing specific ligatures).

---

## 3. Overfitting Analysis

The system exhibits extreme overfitting, making it brittle to new or real-world variations.

### Case-Specific Logic & Healing
*   `processor.py` contains hardcoded case identifiers. For example:
    ```python
    if "cnjokl" in text and "if'pe" in text:
        if "Mh&2341" in text:
            text = text.replace("if'pe 30 QhV", "if*pe 30 QhV")
    ```
    This logic specifically looks for the "Baderwal" case, the direction "West", and the exact patta number "D-2341" to fix a specific font/ligature issue.
*   `narrative.py` and `extractor.py` make hardcoded assumptions about how to find a project name using exact regex patterns (`r'परियोजना\s+का\s+नाम\s+...'`).

### Case-Specific Prompt Engineering
*   Prompts in `extractor.py` are seeded with values from the reference tests, such as asking for lease deed numbers with `(e.g. 'D-2341')` or flat numbers with `(e.g. 'S-1')`. While intended as examples, they indicate the prompt was tuned to pass these specific tests.

### Reference-Driven Architecture
*   The architecture aims to reproduce the text of reference approved documents word-for-word rather than modeling the abstract legal reality. The existence of `audit_parity.py` and exact string matching replacements in `processor.py` proves the goal has been visual/textual mimicry rather than semantic correctness.

---

## 4. Scalability Risks

### Architectural Scalability
*   **Linear Chronology Constraint:** The current system assumes a strict, linear chronological timeline. It cannot easily handle complex graph-like ownership scenarios such as:
    *   **Partitions/Subdivisions:** A single plot splitting into multiple ownership paths.
    *   **Joint Ownership to Single (Release Deeds):** Multiple parties converging.
    *   **Inheritance:** Branching family trees taking ownership fractions.
*   **Loss of Nuance:** Because Wills, Gifts, and Court Orders are squashed into the `"TRANSFER"` bucket, a future document that needs to treat a Will differently than a Sale Deed will not have the required data.

### Maintainability Scalability
*   **Exploding Complexity:** If a new document type (e.g., Gift Deed) is added, developers must:
    1. Update the bloated prompt in `extractor.py`.
    2. Add new highly specific heuristics to `narrative.py`.
    3. Add new templates to `chain_templates.py`.
    4. Add new hardcoded edge-cases to `processor.py` to fix whatever textual anomalies arise.
*   **Fragile Text Parsing:** Healing logic relies heavily on Regex parsing of Hindi Unicode strings. Changes in drafting styles, document quality, or OCR accuracy will silently break these healers.

## Recommendations for the Future
To support 10 years of diverse legal documents, the system must be decoupled:
1.  **Extract Pure Data:** Stop asking the LLM to format strings. Extract pure entities (Person, Event, Property).
2.  **Build an Ownership Graph:** Move away from linear arrays to an entity-relationship model that can handle partitions, inheritance fractions, and mergers.
3.  **Preserve Semantic Types:** Never collapse event types (keep Will as Will, Gift as Gift).
4.  **Isolate Presentation:** Use a robust templating engine (like Jinja or docxtpl natively) instead of string formatting and post-processing regex replacements.