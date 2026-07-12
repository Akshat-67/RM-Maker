import pytest
from services.validation.engine import ValidationEngine
from services.validation.models import Discrepancy, FixAction
from services.validation.identity_validator import IdentityValidator, verhoeff_validate

def test_verhoeff_checksum_algorithm():
    # Valid Aadhaar numbers with valid checksums
    assert verhoeff_validate("123456789012") is False # Random number
    assert verhoeff_validate("368294528141") is True # Valid Aadhaar (check digit 1)
    assert verhoeff_validate("500968512810") is True # Valid Aadhaar (check digit 0)
    assert verhoeff_validate("999912345679") is False # Invalid Aadhaar
    # Format and character filtering checks
    assert verhoeff_validate("abc") is False
    assert verhoeff_validate("") is False

def test_validation_empty_case():
    case_data = {
        "doc_type": "RM",
        "data": {}
    }
    result = ValidationEngine.validate("RM", case_data)
    assert result.is_valid is True
    assert len(result.discrepancies) == 0

def test_validation_valid_rm_case():
    case_data = {
        "doc_type": "RM",
        "bs": [
            {
                "n": "Kiran Devi",
                "id": "3682 9452 8141", # Valid Aadhaar digits checksum
                "pan": "ABCDE1234F"     # Valid PAN
            }
        ],
        "bsign": {
            "n": "Rakesh Kumar",
            "id": "5009 6851 2810", # Valid Aadhaar
            "pan": "XYZAB5678C"     # Valid PAN
        }
    }
    result = ValidationEngine.validate("RM", case_data)
    assert result.is_valid is True
    assert len(result.discrepancies) == 0

def test_validation_invalid_aadhaar_format_and_checksum():
    case_data = {
        "doc_type": "RM",
        "bs": [
            {
                "n": "Kiran Devi",
                "id": "1234", # Too short
                "pan": "ABCDE1234F"
            }
        ]
    }
    result = ValidationEngine.validate("RM", case_data)
    assert result.is_valid is False
    assert len(result.discrepancies) == 1
    assert "must be exactly 12 digits" in result.discrepancies[0].explanation

    # Checksum failure
    case_data_wrong_check = {
        "doc_type": "RM",
        "bs": [
            {
                "n": "Kiran Devi",
                "id": "123456789012", # 12 digits but invalid Verhoeff check
                "pan": "ABCDE1234F"
            }
        ]
    }
    result_check = ValidationEngine.validate("RM", case_data_wrong_check)
    assert result_check.is_valid is False
    assert len(result_check.discrepancies) == 1
    assert "checksum validation failed" in result_check.discrepancies[0].explanation

def test_validation_invalid_pan_format():
    case_data = {
        "doc_type": "RM",
        "bs": [
            {
                "n": "Kiran Devi",
                "id": "3682 9452 8141", # Valid Aadhaar
                "pan": "invalidpan" # Invalid syntax
            }
        ]
    }
    result = ValidationEngine.validate("RM", case_data)
    assert result.is_valid is False
    assert len(result.discrepancies) == 1
    assert "PAN number format invalid" in result.discrepancies[0].explanation

def test_validation_duplicate_ids():
    case_data = {
        "doc_type": "RM",
        "bs": [
            {
                "n": "Kiran Devi",
                "id": "3682 9452 8141", # Valid Aadhaar
                "pan": "ABCDE1234F"
            },
            {
                "n": "Rakesh Kumar",
                "id": "3682 9452 8141", # Duplicate Aadhaar
                "pan": "ABCDE1234F"     # Duplicate PAN
            }
        ]
    }
    result = ValidationEngine.validate("RM", case_data)
    assert result.is_valid is False
    # Expect 2 discrepancies: one for duplicate Aadhaar, one for duplicate PAN
    assert len(result.discrepancies) == 2
    explanations = [d.explanation for d in result.discrepancies]
    assert any("Duplicate Aadhaar number" in e for e in explanations)
    assert any("Duplicate PAN number" in e for e in explanations)
