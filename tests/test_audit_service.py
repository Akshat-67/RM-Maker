import os
import pytest
from services.audit_service import run_case_audit

def test_run_case_audit_no_case():
    res = run_case_audit("case_missing_123", "RM")
    assert "error" in res or res.get("discrepancies") == []
