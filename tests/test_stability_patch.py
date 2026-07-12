"""
tests/test_stability_patch.py -- V2.0 Stability Patch Regression Tests

Bug 1: Case-level file locking + atomic writes
Bug 2: Optimistic concurrency (revision numbers)
Bug 3: Filename sanitisation
Bug 4: Server-side compile safety gate

Pure-logic tests use the same fixture pattern as test_services.py.
HTTP tests hit the running dev server at http://127.0.0.1:5000.
"""
from __future__ import annotations

import os
import threading
import uuid
from io import BytesIO

import pytest
import requests

import services.session_manager as sm
import services.file_service as fs

BASE_URL = "http://127.0.0.1:5000"


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_cases_dir(tmp_path):
    old_sm = sm.CASES_DIR
    old_fs = fs.CASES_DIR
    test_dir = str(tmp_path / "cases")
    sm.CASES_DIR = test_dir
    fs.CASES_DIR = test_dir
    yield test_dir
    sm.CASES_DIR = old_sm
    fs.CASES_DIR = old_fs


def _new_server_case(doc_type: str = "RM") -> str:
    resp = requests.get(
        f"{BASE_URL}/new_case?doc_type={doc_type}",
        allow_redirects=False,
        timeout=10,
    )
    assert resp.status_code in (301, 302)
    return resp.headers["Location"].rstrip("/").split("/")[-1]


def _save(case_id: str, revision=None, data: dict | None = None) -> requests.Response:
    payload = {
        "data": data or {"note": "test"},
        "doc_type": "RM",
        "bank": "TestBank",
        "borrowers": "1",
        "loans": "1",
        "properties": "1",
        "verified_fields": [],
    }
    if revision is not None:
        payload["revision"] = revision
    return requests.post(f"{BASE_URL}/case/{case_id}/save", json=payload, timeout=15)


# ---------------------------------------------------------------------------
# Bug 1 -- File locking
# ---------------------------------------------------------------------------

class TestFileLocking:

    def test_concurrent_saves_no_crash(self, temp_cases_dir):
        """20 threads writing to the same case must all succeed without error."""
        cid = "case_lock_" + uuid.uuid4().hex[:8]
        sm.save_case_session(cid, {}, [], set(), "Bank", "1", "1")
        errors: list[str] = []

        def do_save(i: int):
            try:
                sm.save_case_session(cid, {"note": f"t{i}"}, [], set(), "Bank", "1", "1")
            except Exception as exc:
                errors.append(f"thread-{i}: {exc}")

        threads = [threading.Thread(target=do_save, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent save errors: {errors}"
        assert sm.load_case_session(cid) is not None, "session.json corrupted"

    def test_get_case_lock_returns_same_lock(self):
        assert sm._get_case_lock("case_same_a") is sm._get_case_lock("case_same_a")

    def test_different_cases_have_different_locks(self):
        assert sm._get_case_lock("case_zzz1") is not sm._get_case_lock("case_zzz2")


# ---------------------------------------------------------------------------
# Bug 2 -- Optimistic concurrency -- unit tests
# ---------------------------------------------------------------------------

class TestRevisionConcurrencyUnit:

    def test_revision_starts_at_1(self, temp_cases_dir):
        cid = "case_rev_" + uuid.uuid4().hex[:8]
        saved = sm.save_case_session(cid, {}, [], set(), "B", "1", "1")
        assert saved["revision"] == 1

    def test_revision_increments(self, temp_cases_dir):
        cid = "case_rev_" + uuid.uuid4().hex[:8]
        s1 = sm.save_case_session(cid, {}, [], set(), "B", "1", "1")
        s2 = sm.save_case_session(cid, {}, [], set(), "B", "1", "1")
        assert s2["revision"] == s1["revision"] + 1

    def test_stale_revision_raises(self, temp_cases_dir):
        cid = "case_rev_" + uuid.uuid4().hex[:8]
        s1 = sm.save_case_session(cid, {}, [], set(), "B", "1", "1")
        rev1 = s1["revision"]
        sm.save_case_session(cid, {}, [], set(), "B", "1", "1")  # advance
        with pytest.raises(sm.RevisionConflictError):
            sm.save_case_session(cid, {}, [], set(), "B", "1", "1", expected_revision=rev1)

    def test_correct_revision_passes(self, temp_cases_dir):
        cid = "case_rev_" + uuid.uuid4().hex[:8]
        s1 = sm.save_case_session(cid, {}, [], set(), "B", "1", "1")
        s2 = sm.save_case_session(cid, {}, [], set(), "B", "1", "1",
                                   expected_revision=s1["revision"])
        assert s2["revision"] == s1["revision"] + 1

    def test_none_revision_always_succeeds(self, temp_cases_dir):
        cid = "case_rev_" + uuid.uuid4().hex[:8]
        for _ in range(5):
            sm.save_case_session(cid, {}, [], set(), "B", "1", "1", expected_revision=None)


# ---------------------------------------------------------------------------
# Bug 2 -- Optimistic concurrency -- HTTP tests
# ---------------------------------------------------------------------------

class TestRevisionConcurrencyHTTP:

    def test_save_returns_revision(self):
        cid = _new_server_case()
        r = _save(cid)
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert isinstance(body.get("revision"), int)

    def test_stale_revision_returns_409(self):
        cid = _new_server_case()
        rev1 = _save(cid).json()["revision"]
        _save(cid, revision=rev1)           # advance
        r_stale = _save(cid, revision=rev1)  # stale
        assert r_stale.status_code == 409
        assert r_stale.json()["error"] == "revision_conflict"

    def test_no_revision_skips_check(self):
        cid = _new_server_case()
        for _ in range(3):
            assert _save(cid).status_code == 200


# ---------------------------------------------------------------------------
# Bug 3 -- Filename sanitisation
# ---------------------------------------------------------------------------

class TestFilenameSanitisation:

    def test_secure_filename_strips_traversal(self):
        from werkzeug.utils import secure_filename
        for name in ["../../app.py", "../../../etc/passwd", "..\\..\\routes\\cases.py"]:
            s = secure_filename(name)
            assert ".." not in s
            assert "/" not in s
            assert "\\" not in s

    def test_safe_filename_preserved(self):
        from werkzeug.utils import secure_filename
        assert secure_filename("normal_file.pdf") == "normal_file.pdf"

    def test_upload_files_sanitises_filename(self):
        from io import BytesIO
        cid = _new_server_case()
        resp = requests.post(
            f"{BASE_URL}/case/{cid}/upload_files",
            files={"files": ("../../evil.pdf", BytesIO(b"%PDF-1.4"), "application/pdf")},
            timeout=15,
        )
        assert resp.status_code == 200
        for fn in resp.json().get("new_files", []):
            assert ".." not in fn and "/" not in fn

    def test_upload_legal_report_sanitises_filename(self):
        from io import BytesIO
        cid = _new_server_case()
        resp = requests.post(
            f"{BASE_URL}/case/{cid}/upload_legal_report",
            files={"files": ("../../evil_report.pdf", BytesIO(b"%PDF-1.4"), "application/pdf")},
            timeout=15,
        )
        assert resp.status_code == 200
        for fn in resp.json().get("new_files", []):
            assert ".." not in fn and "/" not in fn


# ---------------------------------------------------------------------------
# Bug 4 -- Compile safety gate
# ---------------------------------------------------------------------------

class TestCompileGate:

    def test_unit_rm_all_present(self):
        from services.compile_gate import check_compile_prerequisites
        session = {"data": {
            "bs": [{"n": "Rakesh Kumar"}],
            "bsign": {"n": "Manager Singh"},
            "ps": [{"adr": "Plot No 5, Jaipur"}],
            "rd": "12-07-2026",
        }}
        assert check_compile_prerequisites(session, "RM") == []

    def test_unit_rm_missing_fields(self):
        from services.compile_gate import check_compile_prerequisites
        session = {"data": {"bs": [{"n": ""}], "bsign": {}, "ps": [], "rd": ""}}
        missing = check_compile_prerequisites(session, "RM")
        assert len(missing) > 0
        assert any("Borrower" in m for m in missing)

    def test_unit_sd_all_present(self):
        from services.compile_gate import check_compile_prerequisites
        session = {"data": {
            "ss": [{"n": "Ganesh Lal"}],
            "bs": [{"n": "Sita Devi"}],
            "ps": [{"adr": "Flat 3B, Jaipur"}],
            "rd": "12-07-2026",
        }}
        assert check_compile_prerequisites(session, "SD") == []

    def test_unit_sd_missing_fields(self):
        from services.compile_gate import check_compile_prerequisites
        session = {"data": {"ss": [{}], "bs": [{}], "ps": [], "rd": ""}}
        missing = check_compile_prerequisites(session, "SD")
        assert any("Seller" in m for m in missing)
        assert any("Buyer" in m for m in missing)

    def test_http_rm_compile_blocked_without_fields(self):
        cid = _new_server_case("RM")
        _save(cid, data={"bs": [{"n": ""}], "bsign": {"n": ""}, "ps": [{"adr": ""}], "rd": ""})
        resp = requests.post(f"{BASE_URL}/case/{cid}/generate", json={
            "doc_type": "RM", "bank": "TestBank", "borrowers": "1", "loans": "1", "properties": "1",
            "data": {"bs": [{"n": ""}], "bsign": {"n": ""}, "ps": [{"adr": ""}], "rd": ""},
            "verified_fields": [],
        }, timeout=30)
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"] == "compile_gate_failed"
        assert len(body["missing_fields"]) > 0

    def test_http_sd_compile_blocked_without_seller(self):
        cid = _new_server_case("SD")
        _save(cid, data={"ss": [{"n": ""}], "bs": [{"n": ""}], "ps": [{"adr": ""}], "rd": ""})
        resp = requests.post(f"{BASE_URL}/case/{cid}/generate", json={
            "doc_type": "SD", "sellers_count": "1", "buyers_count": "1",
            "chain_scenario": "", "property_type": "Plot",
            "data": {"ss": [{"n": ""}], "bs": [{"n": ""}], "ps": [{"adr": ""}], "rd": ""},
            "verified_fields": [],
        }, timeout=30)
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"] == "compile_gate_failed"
        assert any("Seller" in f for f in body["missing_fields"])

# ---------------------------------------------------------------------------
# V2.0 Release Hardening sprint tests
# ---------------------------------------------------------------------------

class TestReleaseHardening:

    def test_invalid_case_id_rejected(self):
        cid = "case_invalid_123"
        resp = requests.post(
            f"{BASE_URL}/case/{cid}/save",
            json={"data": {}, "doc_type": "RM"},
            timeout=15
        )
        assert resp.status_code == 400
        assert resp.json().get("error") == "Invalid case_id format"

    def test_invalid_bucket_name_rejected(self):
        cid = _new_server_case("SD")
        resp = requests.post(
            f"{BASE_URL}/case/{cid}/upload_bucket/invalid_bucket_123",
            files={"files": ("doc.docx", BytesIO(b"dummy docx content"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            timeout=15
        )
        assert resp.status_code == 400
        assert resp.json().get("error") == "Invalid bucket_name"

    def test_upload_extension_and_size_limits(self):
        cid = _new_server_case("RM")
        
        # 1. Invalid extension .exe
        resp = requests.post(
            f"{BASE_URL}/case/{cid}/upload_files",
            files={"files": ("malicious.exe", BytesIO(b"exe payload"), "application/octet-stream")},
            timeout=15
        )
        assert resp.status_code == 400
        assert "not allowed" in resp.json().get("error", "")

        # 2. Exceeds 25MB limit
        large_file = BytesIO(b"0" * (26 * 1024 * 1024))
        resp2 = requests.post(
            f"{BASE_URL}/case/{cid}/upload_files",
            files={"files": ("huge.pdf", large_file, "application/pdf")},
            timeout=15
        )
        assert resp2.status_code == 400
        assert "exceeds maximum size" in resp2.json().get("error", "")

    def test_duplicate_filename_renamed(self):
        cid = _new_server_case("RM")
        
        # Upload first file
        resp1 = requests.post(
            f"{BASE_URL}/case/{cid}/upload_files",
            files={"files": ("test_doc.docx", BytesIO(b"first docx"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            timeout=15
        )
        assert resp1.status_code == 200
        assert "test_doc.docx" in resp1.json().get("new_files", [])

        # Upload same file again – should get renamed
        resp2 = requests.post(
            f"{BASE_URL}/case/{cid}/upload_files",
            files={"files": ("test_doc.docx", BytesIO(b"second docx"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            timeout=15
        )
        assert resp2.status_code == 200
        new_files = resp2.json().get("new_files", [])
        assert len(new_files) == 1
        assert new_files[0] == "test_doc_1.docx"

