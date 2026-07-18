# RM-Maker Code-Health Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the critical security vulnerabilities identified in the code review, begin modularizing the monolithic Flask application, and introduce automated tests while preserving existing functionality.

**Architecture:**
1. Split the large `app.py` into focused Flask Blueprints (case handling, document generation, API helpers).
2. Introduce a shared AI‑client service that encapsulates the Gemini/NVIDIA key handling.
3. Replace the file‑based case storage with a lightweight SQLite database accessed via SQLAlchemy.
4. Add comprehensive unit and integration tests for the new modules and the security fixes.

**Tech Stack:** Python 3.9+, Flask, Flask‑Blueprints, SQLAlchemy (SQLite), python‑dotenv, Werkzeug, Jinja2, pytest, logging.

## Global Constraints
- **Do NOT modify** the extraction pipelines: `modules/rm/*`, `modules/sd/*`, `utils/helpers.py`. 
- **Do NOT change** the DevLys conversion logic.
- **All new code must be backward‑compatible** with existing endpoints.
- **Environment variables** must be used for any secret (API keys, basic‑auth credentials).
- **All routes that accept `case_id`** must sanitize it with `werkzeug.utils.secure_filename`.
- Use the standard library `logging` module for all new logging; remove `print` statements.
- Commit after every completed task (see each task’s commit step).

---

## Phase 1 – Critical Security Fixes

### Task 1.1 – Move API Keys to Environment Variables
**Files:**
- Create: `.env.example` (sample file with placeholder keys)
- Modify: `modules/rm/extractor.py` (replace hard‑coded NVIDIA key with `os.getenv('NVIDIA_API_KEY')`)
- Modify: `modules/sd/extractor.py` (same replacement)
- Modify: `app.py` (add `from dotenv import load_dotenv; load_dotenv()` near the top)
- Modify: `requirements.txt` (add `python-dotenv`)

**Interfaces:**
- Consumes: Existing `raw_generate` functions (unchanged signature).
- Produces: `utils/config.get_nvidia_api_key() -> str` helper.

- [ ] **Step 1:** Write a failing test that verifies the environment variable is read.
```python
def test_nvidia_key_missing(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    from utils.config import get_nvidia_api_key
    with pytest.raises(RuntimeError):
        get_nvidia_api_key()
```
- [ ] **Step 2:** Run the test – it should fail because the function does not yet raise.
- [ ] **Step 3:** Implement `utils/config.py` with `def get_nvidia_api_key():` that reads `os.getenv('NVIDIA_API_KEY')` and raises `RuntimeError("NVIDIA_API_KEY not set")` if missing.
- [ ] **Step 4:** Update `modules/rm/extractor.py` and `modules/sd/extractor.py` to call `get_nvidia_api_key()` instead of the hard‑coded string.
- [ ] **Step 5:** Run the test again – it should now pass.
- [ ] **Step 6:** Add a `.env.example` containing `NVIDIA_API_KEY=your_key_here`.
- [ ] **Step 7:** Update `requirements.txt` with `python-dotenv`.
- [ ] **Step 8:** Commit the changes.

### Task 1.2 – Sanitize `case_id` Parameters
**Files:**
- Modify: `app.py` (all route definitions that accept `<case_id>`).

**Interfaces:**
- Consumes: Existing route parameters.
- Produces: Sanitized file paths via `secure_filename`.

- [ ] **Step 1:** Write a failing test that calls `/case/../../etc/passwd/view` and expects a 400 response.
```python
def test_case_id_traversal(client):
    resp = client.get("/case/../../etc/passwd/view")
    assert resp.status_code == 400
```
- [ ] **Step 2:** Run the test – it fails because the route does not validate.
- [ ] **Step 3:** In `app.py`, import `secure_filename` and wrap every `case_id` usage:
```python
case_id = secure_filename(case_id)
if ".." in case_id or case_id.startswith('/'):
    abort(400, "Invalid case identifier")
```
- [ ] **Step 4:** Run the test – it should now pass.
- [ ] **Step 5:** Apply the same sanitization to any other endpoint using `case_id`.
- [ ] **Step 6:** Commit the changes.

### Task 1.3 – Restrict CORS to Same Origin
**Files:**
- Modify: `app.py` (CORS header section).

- [ ] **Step 1:** Write a failing test that sends a request with `Origin: http://evil.com` and asserts the response does **not** contain `Access-Control-Allow-Origin: *`.
```python
def test_cors_restricted(client):
    resp = client.get("/", headers={"Origin": "http://evil.com"})
    assert resp.headers.get("Access-Control-Allow-Origin") != "*"
```
- [ ] **Step 2:** Run – fails because wildcard is still present.
- [ ] **Step 3:** Replace the wildcard header with the actual host (e.g., `request.host_url.rstrip('/')`).
```python
response.headers["Access-Control-Allow-Origin"] = request.host_url.rstrip('/')
```
- [ ] **Step 4:** Run the test – it should now pass.
- [ ] **Step 5:** Commit the change.

### Task 1.4 – Add Basic Authentication (optional but recommended)
**Files:**
- Create: `utils/auth.py` (simple HTTP Basic auth helper using `flask_httpauth`).
- Modify: `app.py` (apply `@auth.login_required` to all routes).

- [ ] **Step 1:** Write a failing test that accesses a protected endpoint without credentials and receives a 401.
```python
def test_auth_required(client):
    resp = client.get("/case/list")
    assert resp.status_code == 401
```
- [ ] **Step 2:** Run – fails (no auth enforced).
- [ ] **Step 3:** Implement `utils/auth.py` reading `APP_USER` and `APP_PASS` from environment variables.
- [ ] **Step 4:** Decorate all route functions in `app.py` with `@auth.login_required`.
- [ ] **Step 5:** Run the test – passes.
- [ ] **Step 6:** Add `APP_USER` and `APP_PASS` placeholders to `.env.example`.
- [ ] **Step 7:** Commit.

---

## Phase 2 – Modularize the Flask Application

### Task 2.1 – Create Blueprint for Case Management
**Files:**
- Create: `blueprints/case/__init__.py` (registers blueprint)
- Create: `blueprints/case/routes.py` (moves all `/case/*` routes from `app.py`)
- Modify: `app.py` (register blueprint: `app.register_blueprint(case_bp, url_prefix="/case")`)

- [ ] **Step 1:** Write a failing integration test that hits `/case/<id>/view` and expects 200 (using a known test case). The route will be missing after the move.
- [ ] **Step 2:** Run – fails.
- [ ] **Step 3:** Move the relevant route functions to `blueprints/case/routes.py`, preserving imports.
- [ ] **Step 4:** Ensure `blueprints/case/__init__.py` creates `case_bp = Blueprint('case', __name__)` and registers routes.
- [ ] **Step 5:** Update `app.py` to import and register the blueprint.
- [ ] **Step 6:** Run the integration test – passes.
- [ ] **Step 7:** Commit.

### Task 2.2 – Create Blueprint for Document Generation
**Files:**
- Create: `blueprints/generation/__init__.py`
- Create: `blueprints/generation/routes.py` (contains `/generate_rm`, `/generate_sd` endpoints)
- Modify: `app.py` (register blueprint with `url_prefix="/generate"`).

- Follow the same test‑driven pattern as Task 2.1, ensuring the endpoints still work after the move.

### Task 2.3 – Extract Shared AI Client to `utils/ai_client.py`
**Files:**
- Create: `utils/ai_client.py` (wraps `raw_generate`, includes fallback logic, reads API key via `utils.config.get_nvidia_api_key()`).
- Modify: `modules/rm/extractor.py` & `modules/sd/extractor.py` to import and call `ai_client.generate()` instead of duplicating code.

- Write a unit test for `utils/ai_client.py` that mocks the underlying HTTP call and verifies the fallback sequence.

---

## Phase 3 – Replace File‑Based Session Storage with SQLite

### Task 3.1 – Add SQLAlchemy Models for Cases
**Files:**
- Create: `models/case.py` (SQLAlchemy `Case` model with columns matching current JSON fields).
- Modify: `requirements.txt` (add `SQLAlchemy`, `Flask-SQLAlchemy`).

- Write a failing test that creates a `Case` instance, commits it, and queries it back.

### Task 3.2 – Migrate Existing JSON Sessions to DB (One‑off Script)
**Files:**
- Create: `scripts/migrate_sessions.py` (iterates over `cases/` directory, loads each `session.json`, inserts a row into the DB).

- Write an integration test that runs the script on a temporary fixture directory and verifies that the DB now contains the same number of rows as JSON files.

### Task 3.3 – Update Routes to Use DB Instead of Files
**Files:**
- Modify: `blueprints/case/routes.py` (replace file reads/writes with `Case.query` and `db.session.add/commit`).

- Write failing tests for the modified routes (e.g., retrieve a case, update a field, ensure DB persists).

---

## Phase 4 – Add Comprehensive Test Suite

### Task 4.1 – Unit Tests for New Utilities
- Tests for `utils/config.py`, `utils/auth.py`, `utils/ai_client.py`.

### Task 4.2 – Integration Tests for Blueprints
- Use Flask’s `test_client` to hit each endpoint (case management, generation, authentication).

### Task 4.3 – Security Regression Tests
- Ensure the previously fixed vulnerabilities stay patched (API‑key exposure, path traversal, CORS).

### Task 4.4 – CI Configuration (optional)
- Add a simple GitHub Actions workflow (`.github/workflows/ci.yml`) that runs `pytest` on push.

---

**Plan saved to** `docs/superpowers/plans/2026-07-02-rm-maker-code-health.md`.

**Execution option:** You selected **Subagent‑Driven (recommended)**. I will now dispatch a fresh subagent for each task, pause for your review after every task, and continue iteratively.

Shall I start with **Task 1.1 – Move API Keys to Environment Variables**?