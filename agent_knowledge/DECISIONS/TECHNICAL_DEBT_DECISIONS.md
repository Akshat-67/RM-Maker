# Technical Debt Decisions

This document classifies findings from the Technical Debt Audit based on the project's "Get Things Working" methodology. The overarching goal is to preserve useful engineering knowledge and institutional history, prioritize RM/SD isolation over blind unification, and focus on genuine debt removal rather than merely minimizing file count.

## 1. ACCEPTED

The following findings are accepted and represent actionable technical debt.

### Root Directory Clutter
**Status:** Accepted.
Generated artifacts should not permanently live in the repository root.
**Examples:**
* `diff.txt`, `diff2.txt`, `parity_diff.txt`, `parity_diff_new.txt`, `parity_diff_current.txt`, `out.txt`, `validation_output.txt`
* Generated DOCX outputs (e.g., `test_out.docx`, `debug_output.docx`, `debug_highlight_output.docx`, `Validated_AI.docx`, `ReEval_AI.docx`)
**Action:** These will either be deleted, ignored via `.gitignore`, or moved to proper locations.

### One-Off Case Healing Scripts
**Status:** Accepted.
Scripts containing hardcoded case IDs, party data, witness data, and addresses represent overfitting and technical debt.
**Examples:**
* `heal_session.py`, `heal_session_allotment.py`, `heal_session_final.py`, `heal_session_landmark.py`, `heal_session_witnesses.py`
* `reorder_chain.py`
**Action:** These are confirmed technical debt.

### Need For Better Tool Organization
**Status:** Accepted.
Useful infrastructure is currently mixed with temporary scripts. The repository requires clearer separation.
**Target Structure:**
* tools
* tests
* investigations
* archives

### app.py Complexity
**Status:** Accepted.
The finding that `app.py` has become very large is valid.
**Caveat:** No refactor is approved yet.

---

## 2. PARTIALLY ACCEPTED

The following findings contain valid observations but the recommended solutions or underlying assumptions have been modified to align with project goals.

### Debug Scripts
**Status:** Partially Accepted.
Do not assume all debug scripts are worthless. Many were created during difficult SD investigations and contain valuable knowledge.
**Examples:**
* `debug_gen.py`, `debug_kru.py`, `validate_fixes.py`
**Action:** We must distinguish between obsolete, historically valuable, and still useful debug scripts rather than blanket deletion.

### Test Scripts
**Status:** Partially Accepted.
The existence of test scripts does not automatically make them debt.
**Examples:**
* `test_chain.py`, `test_chain2.py`, `test_conversion.py`, `test_symbols.py`, `test_date_kru.py`, `test_hex.py`, `test_pipeline.py`
**Action:** Must evaluate for useful validation logic, unique test cases, and preservable knowledge before recommending deletion.

### Duplicate RM / SD Logic
**Status:** Partially Accepted.
The duplication finding is valid, but unification is NOT approved.
**Caveat:** The project has not approved `BaseExtractor`, `BaseProcessor`, or a shared-core architecture. RM/SD isolation is a primary concern. Consolidation cannot be assumed desirable.

### Processor Post-Processing Debt
**Status:** Partially Accepted.
The existence of large replacement blocks is a valid finding.
**Caveat:** The project has not approved removing all post-processing, rewriting DevLys conversion, or replacing the rendering pipeline.
**Action:** Must distinguish between generic necessary normalization, case-specific overfitting, and obsolete rules.

---

## 3. REJECTED

The following recommendations are NOT approved.

* **Delete Everything That Looks Temporary:** Rejected. The project values historical knowledge. Age does not equal uselessness.
* **Immediate RM/SD Processor Unification:** Rejected. RM/SD isolation remains a project principle.
* **Rewrite DevLys Conversion:** Rejected. Insufficient evidence for a rewrite.
* **Large-Scale Flask Architecture Rewrite:** Rejected. A rewrite is not currently approved, though splitting `app.py` may eventually be desirable.

---

## 4. ON HOLD

The following architectural changes require separate architectural review and are currently On Hold:

* `BaseExtractor`
* `BaseProcessor`
* RM/SD Shared Core
* Full App Modularization
* Rendering Architecture Replacement

---

## 5. Technical Debt Prioritization Matrix

| Item | Classification | Rationale |
|---|---|---|
| Generated outputs (`diff.txt`, `.docx` dumps) | **Delete / Ignore** | Pure artifacts; hold no code logic. Add to `.gitignore`. |
| Hardcoded case healers (`heal_session*.py`) | **Delete** | Case-specific data overfits; no reusable generic logic. |
| Hardcoded logic fixes (`reorder_chain.py`) | **Delete / Refactor** | Hardcoded date fixing; should be evaluated if the logic belongs in `extractor.py` and then deleted. |
| Investigation dumps (`dump_tags.py`, `dump_texts.py`) | **Archive** | Useful tools for template debugging, but clutter root. |
| Low-level investigations (`check_ligature.py`, `test_hex.py`, `test_symbols.py`, `search_xml.py`) | **Archive / Keep As-Is** | Retain valuable insights into Word XML and DevLys hex issues. Move to `investigations/` or `tools/`. |
| Validation tools (`audit_parity.py`, `test_e2e_sd.py`) | **Keep As-Is** | Valuable infrastructure. Move to `tools/` and `tests/`. |
| Debug generators (`debug_gen.py`, `validate_fixes.py`) | **Needs Investigation** | Evaluate if they should be parameterized and kept, or if they represent historical SD development knowledge to archive. |
| Experimental Converter (`utils/devlys_to_unicode.py`) | **Needs Investigation** | Determine if it holds unique logic not present in `devlys_converter.py` before archiving or deleting. |
| `app.py` Size | **Keep As-Is** | Large size noted, but rewrite is rejected/on hold. |
| RM / SD Duplication | **Keep As-Is** | Duplication noted, but shared-core is on hold to maintain strict isolation. |
| Processor `_postprocess_saved_doc` | **Needs Investigation** | Review blocks to distinguish generic normalization vs. overfitting. Rewrite rejected. |

---

## 6. Knowledge Preservation Review

The project actively preserves lessons learned. The following files, while potentially appearing as clutter, contain valuable institutional knowledge from SD development:

* **Valuable Scripts:** `test_conversion.py`, `test_symbols.py`, `test_hex.py` contain explicit, reproducible examples of how DevLys mapping and Unicode conversions fail or behave.
* **Valuable Investigations:** `check_actual_date_chars.py`, `check_actual_font.py`, `check_ligature.py` represent deep dives into formatting anomalies. They document *why* certain post-processing hacks exist.
* **Valuable Audits:** `audit_parity.py` and `audit_parity_surgical.py` contain the methodology used to achieve byte-for-byte or char-for-char parity during the SD generation.
* **Temporary Files to Archive:** `fix_template_drafter.py`, `fix_template_lines.py`, and `revert_template.py` represent historical attempts to patch Word templates programmatically. They should be archived in `agent_knowledge/` or a dedicated `archive/` folder, as the docx manipulation logic might be useful later.

---

## 7. Recommended Cleanup Order

1. **Delete & Ignore Artifacts:** Remove output `.docx`, `.txt` diffs, and log files from the root. Update `.gitignore`.
2. **Delete Destructive / Overfitted Debt:** Remove all `heal_session_*.py` and case-specific logic patching scripts (e.g., `reorder_chain.py`).
3. **Organize Tools & Tests:** Create `tools/` and `tests/` directories. Move valuable infrastructure (`audit_parity.py`, `test_e2e_sd.py`) into them.
4. **Archive Investigations:** Create an `investigations/` or `archive/` directory. Move hex checkers, ligature checkers, and XML searchers here to preserve their knowledge without cluttering the root.
5. **Investigate Debug Generators:** Review `debug_gen.py` and `validate_fixes.py` to determine if they should be parameterized into a generic tool or archived as SD development history.
6. **Investigate Post-Processing:** Audit `_postprocess_saved_doc` in both RM and SD processors solely to identify and remove case-specific overfitting, leaving generic normalizations intact.
