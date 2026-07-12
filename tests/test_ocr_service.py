import os
import pytest
from services.ocr_service import ocr_extract_text

def test_ocr_extract_text_empty_list():
    result = ocr_extract_text("case_test", [])
    assert result == ""

def test_ocr_extract_text_with_missing_api_key(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "")
    result = ocr_extract_text("case_test", ["non_existent_file.png"])
    assert "NVIDIA_API_KEY not configured" in result
