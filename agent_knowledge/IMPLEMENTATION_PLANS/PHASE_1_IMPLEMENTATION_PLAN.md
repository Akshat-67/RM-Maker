# Phase 1 Implementation Plan

This document outlines the detailed execution strategy for **Phase 1 (Immediate Execution)** items as defined in `agent_knowledge/ARCHITECTURE/MASTER_REMEDIATION_CONTEXT.md`.

**Scope restriction:** This plan strictly covers low-risk, high-confidence, already-approved cleanup tasks. It does not introduce any architectural changes, field renaming, or template modifications reserved for later phases.

---

## 1. Remove Confirmed Overfitting

*   **Objective:** Remove brittle, case-specific logic and hardcoded patches that overfit the system to specific reference documents.
*   **Exact files expected to be touched:**
    *   `heal_session_allotment.py`
    *   `heal_session_final.py`
    *   `heal_session_landmark.py`
    *   `heal_session_witnesses.py`
    *   `heal_session.py`
    *   `reorder_chain.py`
    *   `modules/sd/processor.py` (specifically searching for and removing case-specific hardcoded name, address, or lease number patches)
*   **Expected risk level:** Low
*   **Validation strategy:** Ensure that removing `heal_session_*.py` and `reorder_chain.py` does not break any core E2E pipelines. Run `test_e2e_sd.py` (or execute at least 3 existing cases) to verify that the removal of case-specific logic in `processor.py` does not cause broader rendering regressions.
*   **Rollback strategy:** Restore deleted files via Git and revert `modules/sd/processor.py` to the previous commit.
*   **Dependencies:** None
*   **Estimated implementation order:** 1

---

## 2. Repository Cleanup

*   **Objective:** Remove generated artifacts and text diffs from the repository root to improve project legibility and prevent future commits of junk data.
*   **Exact files expected to be touched:**
    *   `.gitignore`
    *   Root-level text files to be deleted/archived: `diff.txt`, `diff2.txt`, `parity_diff.txt`, `parity_diff_current.txt`, `parity_diff_new.txt`, `out.txt`, `validation_output.txt`
    *   Root-level generated DOCX files to be deleted: `test_out.docx`, `debug_output.docx`, `debug_highlight_output.docx`, `ReEval_AI.docx`, `Validated_AI.docx`
*   **Expected risk level:** Low
*   **Validation strategy:** Execute `git status` after deletion to confirm clean working directory. Review the updated `.gitignore` rules to ensure future runs of `audit_parity.py` or debug scripts do not leave untracked artifacts.
*   **Rollback strategy:** Revert the `.gitignore` changes and restore the deleted files via Git.
*   **Dependencies:** None
*   **Estimated implementation order:** 2

---

## 3. Knowledge Organization

*   **Objective:** Segregate valuable testing and investigation infrastructure from the root directory into dedicated folders, preserving institutional knowledge without clutter.
*   **Exact files expected to be touched:**
    *   `audit_parity.py`, `audit_parity_surgical.py`, `test_e2e_sd.py` (move to `tools/` or `tests/`)
    *   `test_chain.py`, `test_chain2.py`, `test_conversion.py`, `test_date_kru.py`, `test_hex.py`, `test_pipeline.py`, `test_symbols.py` (review/archive to `tests/` or `investigations/`)
    *   `debug_gen.py`, `debug_gen_highlight.py`, `debug_kru.py`, `dump_tags.py`, `dump_texts.py`, `search_xml.py`, `search_xml2.py`, `check_actual_date_chars.py`, `check_actual_font.py`, `check_actual_hex.py`, `check_ligature.py`, `validate_fixes.py` (move to `investigations/` or `agent_knowledge/archive/`)
    *   `fix_template_drafter.py`, `fix_template_lines.py`, `revert_template.py` (archive)
*   **Expected risk level:** Low
*   **Validation strategy:** Verify that moved E2E tests (`test_e2e_sd.py`) and parity tools (`audit_parity.py`) still execute successfully from their new paths. Update any internal relative imports inside these tools if necessary.
*   **Rollback strategy:** Revert the commit to restore file locations.
*   **Dependencies:** Repository Cleanup (Step 2)
*   **Estimated implementation order:** 3

---

## 4. Documentation Alignment

*   **Objective:** Create a single source of truth for the extraction schema by correcting existing documentation to match the implemented codebase keys.
*   **Exact files expected to be touched:**
    *   `CHAIN_SCHEMA.md`
    *   `SD_SCHEMA.md` (if discrepancies are found against the code)
*   **Expected risk level:** Low
*   **Validation strategy:** Perform a manual side-by-side verification of the `CHAIN_SCHEMA.md` documentation against the actual JSON schema output and the extraction prompts in `modules/sd/extractor.py`. The documentation must accurately reflect the shorthand keys currently in use (e.g., documenting `chain` vs `title_chain`).
*   **Rollback strategy:** Revert changes to the `.md` documentation files.
*   **Dependencies:** None
*   **Estimated implementation order:** 4