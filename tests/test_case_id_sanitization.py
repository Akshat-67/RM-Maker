import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_case_id_path_traversal_blocked(client):
    _audiences = {
        "/case/../../etc/passwd",
        "/case/../../../windows/system32",
        "/case/test/../../../etc/passwd",
    }
    for path in _audiences:
        resp = client.get(path)
        assert resp.status_code == 400, f"Expected 400 for {path}, got {resp.status_code}"

def test_case_id_with_dots_blocked(client):
    resp = client.get("/case/test..case")
    assert resp.status_code == 400

def test_valid_case_id_allowed(client):
    # A valid case_id should not be blocked by sanitization itself
    # (but may 404 if the case doesn't exist, which is fine)
    resp = client.get("/case/valid_case_123")
    # Should not be 400 — may be 404 if case doesn't exist
    assert resp.status_code != 400
