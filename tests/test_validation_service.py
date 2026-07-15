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

def valid_base_case():
    return {
        "doc_type": "RM",
        "rd": "25-05-2026",
        "bs": [
            {
                "n": "Kiran Devi",
                "id": "3682 9452 8141",
                "pan": "ABCDE1234F",
                "s": "Mrs.",
                "r": "W/o",
                "rn": "John",
                "gender": "Female",
                "adr": "Test address 1"
            }
        ],
        "bsign": {
            "n": "Rakesh Kumar",
            "id": "5009 6851 2810",
            "pan": "XYZAB5678C",
            "adr": "Test Bank address"
        },
        "ls": [{"a": "1000000"}],
        "ps": [{"adr": "Test Property address 1"}]
    }

def test_validation_empty_case():
    case_data = {
        "doc_type": "RM",
        "data": {}
    }
    result = ValidationEngine.validate("RM", case_data)
    assert result.is_valid is False
    # Empty case should have multiple missing field discrepancies
    assert len(result.discrepancies) > 0

def test_validation_valid_rm_case():
    case_data = valid_base_case()
    result = ValidationEngine.validate("RM", case_data)
    assert result.is_valid is True
    assert len(result.discrepancies) == 0

def test_validation_invalid_aadhaar_format_and_checksum():
    case_data = valid_base_case()
    case_data["bs"][0]["id"] = "1234" # Too short
    result = ValidationEngine.validate("RM", case_data)
    assert result.is_valid is False
    assert any("must be exactly 12 digits" in d.explanation for d in result.discrepancies)

    # Checksum failure
    case_data_wrong_check = valid_base_case()
    case_data_wrong_check["bs"][0]["id"] = "123456789012" # Invalid Verhoeff check
    result_check = ValidationEngine.validate("RM", case_data_wrong_check)
    assert result_check.is_valid is False
    assert any("checksum validation failed" in d.explanation for d in result_check.discrepancies)

def test_validation_invalid_pan_format():
    case_data = valid_base_case()
    case_data["bs"][0]["pan"] = "invalidpan"
    result = ValidationEngine.validate("RM", case_data)
    assert result.is_valid is False
    assert any("PAN number format invalid" in d.explanation for d in result.discrepancies)

def test_validation_duplicate_ids():
    case_data = valid_base_case()
    # Add second borrower with same Aadhaar/PAN
    case_data["bs"].append({
        "n": "Rakesh Kumar",
        "id": "3682 9452 8141", # Duplicate
        "pan": "ABCDE1234F",     # Duplicate
        "s": "Mr.",
        "r": "S/o",
        "rn": "Father Name",
        "gender": "Male",
        "adr": "Test address 2"
    })
    result = ValidationEngine.validate("RM", case_data)
    assert result.is_valid is False
    explanations = [d.explanation for d in result.discrepancies]
    assert any("Duplicate Aadhaar number" in e for e in explanations)
    assert any("Duplicate PAN number" in e for e in explanations)

def test_validation_engine_with_gender_and_missing_validators():
    case_data = valid_base_case()
    case_data["rd"] = "" # Missing execution date
    case_data["bs"][0]["s"] = "Mr." # Mismatched salutation for W/o & Female

    result = ValidationEngine.validate("RM", case_data)
    assert result.is_valid is False
    explanations = [d.explanation for d in result.discrepancies]
    assert any("relation is 'W/o' but salutation is 'Mr.'" in e for e in explanations)
    assert any("Execution Date is missing" in e for e in explanations)
