# Title Chain Decisions

**Date**: 2026-06-17
**Context**: Evaluation of the title-chain system's scalability to support diverse legal documents (Gifts, Wills, Releases, Partitions) over the next 10 years without a complete rewrite.

---

## 1. ACCEPTED

*   **Preserve event types:** Stop mapping distinct events (Gifts, Wills, etc.) into a generic `TRANSFER` type.
*   **Support future document types:** Broaden the extraction and schema to explicitly recognize `GIFT_DEED`, `WILL`, `RELEASE_DEED`, `INHERITANCE`, and `PARTITION`.
*   **Document assumptions currently baked into the system:** Formally log that `extractor.py` and `narrative.py` currently assume 1-to-1 linear transfers, monetary consideration, and chronological string concatenation.
*   **Add metadata that improves future compatibility:** Add fields like `consideration_type` and `relationship_to_previous_owner` to the extraction schema to support non-sale transfers cleanly.

---

## 2. PARTIALLY ACCEPTED

*   **`event_id` / `parent_event_ids`:** Accepted conceptually as a way to link events, but implementation must be cautious to avoid breaking the current linear `narrative.py` loop.
*   **Fractional ownership modeling:** Accepted as metadata (e.g., extracting a "50% share" string), but rejected as a programmatic math engine.
*   **Lineage tracking mechanisms:** Tracking "who got what from whom" is accepted via basic ID pointers, but full traversal/topological sorting logic is deferred.

*Critical Evaluation:* Introducing graph-like pointers (`parent_event_ids`) into a fundamentally linear processor (`narrative.py`) risks creating edge cases where the template engine doesn't know how to render a split. These should be extracted purely as passive data for now, rather than active routing logic.

---

## 3. REJECTED

*   **LLM-generated legal narratives:** Native generation of the final narrative string by the LLM is rejected. We must maintain strict, deterministic control over the final Hindi legal text via templates and Python logic.
*   **Immediate title-chain rewrite:** The current `modules/sd` implementation works well enough for Sale Deeds. An immediate ground-up rewrite is unnecessary risk.
*   **Recursive narrative engine redesign:** Moving away from a simple loop to a recursive tree-traversal in `narrative.py` is rejected as too complex for the current scope.
*   **Throwing away `narrative.py`:** The core logic of extracting array items and populating templates will remain the foundation.

---

## 4. ON HOLD

*   **Ownership graph:** Full implementation of an adjacency-list graph data structure.
*   **Ownership state machine:** A Python engine that validates fractional mathematical splits over time.
*   **`modules/title_engine`:** A completely isolated, generic module separate from specific deed implementations.
*   **Entity relationship architecture:** Splitting the flat array into distinct relational tables for `Parties`, `Properties`, and `Events`.
*   **Generic legal-history platform:** The ambitious goal of building a platform capable of handling any theoretical document type.

---

## 5. Smallest Safe Improvements

Assuming the current architecture stays intact, these are the smallest changes that provide the biggest future-proofing benefits without redesigning the system:

### High Value / Low Risk
1.  **Update Extraction Prompts:** Modify `extractor.py` to allow the LLM to return `GIFT_DEED`, `WILL`, `RELEASE_DEED`, `INHERITANCE`, and `PARTITION`.
2.  **Add Passive Metadata Fields:** Update `schema.py` and prompts to capture `consideration_type` (e.g., "Love and Affection") and `relationship_to_previous_owner`.
3.  **Graceful Template Fallbacks:** Update `narrative.py` to route newly extracted event types to safe, generic textual templates (e.g., `TRANSFER_GENERIC`) so the system doesn't crash when encountering a Gift Deed.

### High Value / Medium Risk
1.  **Introduce Sibling Routing in `narrative.py`:** Add logic to handle cases where `amount_str` is empty or non-numeric (e.g., for Wills/Gifts) without breaking the existing template formats.
2.  **Add `event_id` and `parent_event_ids`:** Instruct the LLM to assign and reference IDs within the array. This is medium risk because while the data is passive, ensuring the LLM reliably links them without hallucinating IDs requires prompt tuning.

### Future Work
1.  **Custom Templates for New Deeds:** Draft and implement specific `chain_templates.py` variants for `TEMPLATE_INHERITANCE` or `TEMPLATE_GIFT` to replace the generic fallback.
2.  **Multi-Party Sibling Merging:** Write lightweight logic in `narrative.py` to identify adjacent events with identical `parent_event_ids` (e.g., a partition) and format them into a single list string before template injection.

---

## 6. Recommended Roadmap

*   **Phase 1: Data Preservation (Immediate):** Stop data destruction. Update `extractor.py` to preserve the real `event_type` and add metadata fields (`consideration_type`). Route all new types to the existing `TRANSFER` template.
*   **Phase 2: Relational Metadata (Short-Term):** Add `event_id` and `parent_event_ids` to the extraction schema as passive data points. Do not change `narrative.py` logic yet.
*   **Phase 3: Template Expansion (Mid-Term):** As new document types are officially supported (e.g., the firm starts drafting Gift Deeds), add specific templates to `chain_templates.py` and route them accordingly in `narrative.py`.
*   **Phase 4: Linear Hacks for Non-Linear Events (Long-Term):** For Partitions, implement localized logic in `narrative.py` that peeks at adjacent array items to group them for rendering, faking a graph while keeping the architecture flat.