import pytest
from app import app

def test_run_audit_endpoint_missing_case():
    with app.test_client() as client:
        res = client.post("/api/case/case_missing_123/run_audit")
        assert res.status_code == 404

def test_autofix_endpoint_missing_case():
    with app.test_client() as client:
        res = client.post("/api/case/case_missing_123/autofix", json={
            "field_path": "bs.0.n",
            "suggested_fix": "Mr. Rakesh"
        })
        assert res.status_code == 404
