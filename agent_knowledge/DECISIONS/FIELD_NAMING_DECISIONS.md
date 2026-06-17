# Field Naming Decisions

This document tracks the architectural decisions regarding field naming consistency across the LegalDoc Automator project (RM, SD, session.json, context generation, and templates).

## 1. ACCEPTED

The following findings and architectural directions have been fully accepted:

*   **Alias Proliferation Is Technical Debt**: The existence of multiple names for the same field (e.g., `title_chain` vs `chain`, `adr` vs `address`) is confirmed as architectural debt that complicates maintainability.
*   **CHAIN_SCHEMA Mismatch**: Documentation claiming one structure while code implements another (e.g., `executant.name` vs `executant_name`) must be corrected so there is a single source of truth.
*   **Padding / Healing Logic Is Fragmented**: The logic that pads arrays or heals data across `app.py`, `extractor.py`, and `processor.py` is fragmented and should eventually be centralized.
*   **Need For Canonical Field Documentation**: The project will maintain a documented canonical field map to act as the single source of truth, document aliases, and prevent future divergence.

## 2. PARTIALLY ACCEPTED

The following findings have been accepted in principle but with caveats:

*   **Field Standardization**: While a canonical naming strategy is desirable, the specific short-hand names proposed (e.g., `adr`, `id`, `a`, `c`) are not automatically approved. The standardization process must evaluate readability and maintainability.
*   **Financial & Deed Metadata Naming**: The identified inconsistency (e.g., `amount` vs `sale.amount`, `rd` vs `deed.execution_date`) is valid, but the recommendation to flatten all structures is rejected. Nested structures may be architecturally preferable.

## 3. REJECTED

The following recommendations have been explicitly rejected:

*   **Flatten All Nested Objects**: Do not remove nested objects solely for naming consistency. Nested fields like `sale.amount`, `sale.amount_words`, and `sale.payment_details` can be preferable to root-level flat fields for logical grouping.
*   **Short Keys As Permanent Canonical Standard**: Do not assume legacy shorthand keys (like `adr`, `id`, `a`, `c`) must become the permanent project standard. Full words (like `address`, `aadhaar`, `age`, `caste`) are more readable and maintainable long-term.

## 4. ON HOLD

The following actions are recognized but deferred:

*   **Full Field Renaming Migration**: Changing field names impacts the extractor, schema, `session.json`, `app.py`, processors, templates, and test infrastructure. This requires a dedicated, carefully planned migration strategy.
*   **Session Schema Redesign**: Any major overhaul of the overall `session.json` schema is on hold.
*   **Computed vs Persisted Field Strategy**: The recommendation to persist only atomic fields and regenerate computed fields at render time requires separate architectural review before implementation.

---

## 5. Recommended Canonical Field Map

The following map defines the proposed canonical names versus their legacy aliases. The primary goal is to move toward readable, full-word keys while preserving established semantic groupings.

| Canonical Area | Canonical Name | Legacy Aliases | Reasoning |
| :--- | :--- | :--- | :--- |
| **Parties (Global)** | `address` | `adr` | Clarity and readability. `adr` is ambiguous. |
| | `aadhaar` | `id` | Clarity. `id` could mean internal database ID, whereas `aadhaar` is explicit. |
| | `pan` | `pan` | Already clear. |
| | `age` | `a` | Readability. `a` is too terse. |
| | `caste` | `c` | Readability. |
| | `name` | `n` | Readability. |
| | `salutation` | `s` | Readability. |
| | `relation_type` | `r` | More descriptive than `r`. |
| | `relative_name` | `rn` | More descriptive than `rn`. |
| | `relation_text` | `relation_text` | Accurate description of the raw string. |
| **Sellers/Buyers** | `sellers` | `ss` | Full word is clearer, especially since `ss` is only SD specific. |
| | `buyers` | `bs` | Full word prevents collision/confusion with RM where `bs` means "borrowers". |
| | `borrowers` | `bs` | Distinguishes RM borrowers from SD buyers. |
| **Property** | `properties` | `ps` | Readability. |
| | `land_area` | `land_area` | Clear. |
| | `const_area` | `const_area` | Clear. |
| | `area_unit` | `unit` | `area_unit` is more precise. |
| **Witnesses** | `witnesses` | `ws` | Readability. |
| **Title Chain** | `title_chain` | `chain` | `title_chain` is more descriptive. |
| | `executant_name` | `executant.name` | Aligning with the actual flat implementation in code for simplicity unless nested objects are needed. |
| | `claimant_name` | `claimant.name` | Aligning with code. |
| | `reg_book` | `book_no` | Standardize on the `reg_` prefix for registration fields. |
| | `reg_vol` | `volume_no` | Standardize on the `reg_` prefix. |
| | `reg_page` | `page_no` | Standardize on the `reg_` prefix. |
| **Financial/Deed** | `sale.amount` | `amount` | Groups financial details logically. |
| | `sale.amount_words`| `amount_words` | Groups financial details logically. |
| | `sale.payment_details`| `payments` | Groups financial details logically. |
| | `deed.execution_date`| `rd` | Grouped logically and much clearer than `rd`. |

---

## 6. Migration Risk Assessment

**High Risk:**
*   **Existing `session.json` Data**: Renaming fields means old cases in the `cases/` directory will fail to load or process correctly without a migration script to map old keys to new ones on load.
*   **Templates**: All `.docx` templates rely heavily on legacy short tags (e.g., `{{bs[0].n}}`). Updating to canonical names (e.g., `{{borrowers[0].name}}`) requires modifying every single template file. This is highly error-prone and requires extensive manual verification.

**Medium Risk:**
*   **Extractors (`RMDataExtractor`, `SDDataExtractor`)**: The AI prompts currently instruct the LLM to output the short keys to save tokens. Changing prompts to output full words might slightly increase token usage and requires re-testing AI output stability.
*   **Processors (`RMTemplateProcessor`, `SDTemplateProcessor`)**: The logic that heals, pads, and formats data is tightly coupled to the legacy keys.

## 7. Suggested Implementation Order

If the field renaming migration is taken off hold, it should proceed in this order to minimize disruption:

1.  **Update Prompts & Extractors**: Change the AI extraction instructions to output the new canonical JSON structure.
2.  **Session Migration Layer**: Implement a backward-compatibility layer in `app.py` (`load_case_session`) that automatically transforms legacy JSON keys into the new canonical keys when reading old cases.
3.  **Update Processors**: Refactor `RMTemplateProcessor` and `SDTemplateProcessor` to operate exclusively on the new canonical field names.
4.  **Template Update**: Manually update all `.docx` templates in the `templates/` directory to use the new placeholder names.
5.  **Clean up `app.py`**: Remove the temporary aliasing shims that were bridging the gap between old extractors and new templates.
6.  **Update Documentation**: Finalize `SD_SCHEMA.md` and `CHAIN_SCHEMA.md` to perfectly match the implemented codebase.