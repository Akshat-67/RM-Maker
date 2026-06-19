# API Credential Security Remediation

## Credential Locations Found
* **app.py**: Found hardcoded list `DEFAULT_GEMINI_API_KEYS`. Status: Scrubbed and replaced with dynamic import from `utils/config.py`.
* **template_tools/template_builder.py**: Found hardcoded list `DEFAULT_API_KEYS`. Status: Scrubbed and replaced with dynamic import from `utils/config.py`.
* **archive/old_scripts/verify_builder_recovery.py**: Found hardcoded key strings. Status: Scrubbed.
* **archive/old_scripts/list_models.py**: Found hardcoded key strings. Status: Scrubbed.
* **archive/old_tests/**: Multiple files (`test_builder_regression.py`, `test_flash_latest.py`, `test_all_keys.py`, `test_models.py`, `test_flash_only.py`, `test_env_key.py`, `test_flash_latest_retry.py`) contained raw API key strings. Status: Scrubbed and replaced with `os.getenv("GEMINI_API_KEY_N")`.

## Multi-Key System Analysis
* **How rotation currently works:** `modules/sd/extractor.py` and `modules/rm/extractor.py` take an array of `api_keys`. They maintain an `active_key_index` and a `_rotate_key` method that increments the index modulo the list length when API errors occur, seamlessly re-initializing the client.
* **Issues discovered:** The keys were hardcoded in multiple entry points (`app.py` and `template_tools/template_builder.py`). This led to duplication and the risk of committing secrets to the repository.
* **Fixes applied:** Created `utils/config.py` which dynamically reads `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, etc., and standardizes the array. Entry points now consume this array, preserving the exact same failover queue without any hardcoded credentials.

## Security Fixes Applied
* Removed hardcoded keys across the application and archive.
* Standardized credential loading using `python-dotenv` in `utils/config.py`.
* Repository protections added by modifying `.gitignore` to strictly exclude `.env`, `.env.*`, `credentials.json`, and `secret*.json`, while permitting `.env.example`.
* Created `.env.example` to demonstrate correct placeholder structure.

## Validation Results
* **Startup:** `app.py` starts correctly and does not crash when initializing clients.
* **RM/SD Workflows:** `validate_cases.py` and unit tests confirm that instances of `RMDataExtractor` and `SDDataExtractor` successfully receive and configure the centralized key arrays.
* **Tooling:** Template builder regression functionality operates correctly using the centralized config.

## Remaining Risks
* Archived code still requires manual inspection if new files are un-archived, but the root cause of automated keys leaks via standard endpoints is fully addressed. No raw keys remain in the source tree.