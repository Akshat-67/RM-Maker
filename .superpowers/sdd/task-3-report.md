# Task 3 Report: Integrate DB in App Routes

## Summary
In this task, we successfully integrated the SQLite `cases` database into Flask application routes by configuring Flask-SQLAlchemy and rewriting key session management functions.

## Implementation Details
1. **SQLAlchemy Setup:**
   - Modified `app.py` to import `Case` and `db` from `models.case`.
   - Programmatically resolved the database URI using `os.path.abspath` to point to `cases/cases.db` in the workspace root, preventing Flask-SQLAlchemy from defaulting to the `instance/` folder.
   - Initialized `db` and generated all tables if they did not exist under `app.app_context()`.
2. **`load_case_session` Rewrite:**
   - Replaced file-based loading with querying the database via `db.session.get(Case, case_id)`.
   - Reconstructed the standard session dictionary structure.
   - Dynamically calculated `borrower_name` for backward compatibility in templates and dashboard.
   - Maintained all Devanagari conversion and bidirectional synchronization logic.
3. **`save_case_session` Rewrite:**
   - Refactored session saving to update/insert the `Case` object in the SQLite database.
   - Preserved core directory-creation logic (`os.makedirs`) to ensure compatibility with downstream file generation and uploads.
   - Maintained merge logic, template-key synchronization, schema-pruning (`prune_case_data`), and Devanagari conversion.
4. **`list_cases` Rewrite:**
   - Rewrote case listing to fetch all cases from SQLite, sorted by `last_updated` in descending order.
   - Dynamically calculated `borrower_name` for correct rendering on the dashboard.

## Verification Results
- Ran the test suite using `python -m pytest tests/`.
- All 14 tests (including DB model, migration, pipeline, and case ID sanitization tests) passed cleanly.
- Resolved SQLAlchemy legacy `Query.get()` warnings by migrating queries to `db.session.get()`.

## Fix: Resolve Buckets Loss on Session Reload
We identified and resolved an issue where the `buckets` dictionary passed to `save_case_session` was discarded, causing file upload lists inside buckets to be lost on reloading.

### Changes Made:
1. **`save_case_session` Modification in [app.py](file:///C:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/app.py):**
   - Added logic to retrieve `buckets` from parameters. If `buckets` is `None`, it defaults to the existing buckets using `existing.get("buckets", {})`.
   - Stored `buckets` inside the `pruned_data` dictionary before serializing it using `json.dumps` and committing the session to the database.
2. **`load_case_session` Modification in [app.py](file:///C:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/app.py):**
   - Added retrieval of the `"buckets"` key from the parsed `case.data` JSON blob: `sess["buckets"] = sess["data"].get("buckets", {})`.
3. **`list_cases` Modification in [app.py](file:///C:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/app.py):**
   - Added the `"buckets"` key to the returned dictionary for each listed case: `"buckets": data_dict.get("buckets", {})`.
4. **Verification Test Suite in [tests/test_case_session_buckets.py](file:///C:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/tests/test_case_session_buckets.py):**
   - Created a comprehensive integration test checking session saving, loading, listing, and defaulting behavior for case buckets.
   - Verified that all 15 tests pass successfully.
