# Testing Philosophy & Test Suites

This document describes the testing guidelines, test structures, command invocations, and regression test policies for the RM-Maker codebase.

---

## 1. Testing Philosophy
Automated tests are first-class assets of this project. No production change or bug fix is complete without corresponding test coverage. Tests ensure that modifications to one pipeline (such as the SD extraction rules) do not cause regressions in another stable pipeline (such as RM document generation).

---

## 2. Test Architecture
The test suites reside in `/tests` and are split into backend and browser tests:

- **Pytest (Backend Logic)**: Covers schemas, text normalization, name splitting, file classification, API keys rotation, AI proofreader rules, and template compilation.
- **Playwright (Frontend & Portal Autofill)**: Verifies case creation forms, tab navigation, splitscreen document rendering, and Chrome extension autofill behavior.

---

## 3. Running Tests
Run the backend tests using the following commands:

```powershell
# Run the entire backend test suite (excluding HTTP/server tests)
$env:PYTHONPATH="."; pytest tests/ --ignore=tests/test_stability_patch.py -v

# Run a specific test file
$env:PYTHONPATH="."; pytest tests/test_autocrop_improvements.py -v

# Run tests matching a specific pattern
$env:PYTHONPATH="."; pytest tests/test_ingestion_pipeline.py -k "test_nested_subfolder" -v
```

---

## 4. Regression Test Policy
- **Feature Additions**: Every new feature or API endpoint must include unit or integration tests verifying success and failure bounds.
- **Bug Fixes**: Every bug fix must include a regression test reproducing the failure scenario prior to the patch.
- **Test Integrity**: Never delete or bypass existing assertions unless the underlying business rules or template specifications have changed.
