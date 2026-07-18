import pytest
from services.validation.three_way_validator import ThreeWayValidator
from services.validation.models import Discrepancy

def test_three_way_validator_no_data():
    validator = ThreeWayValidator()
    # No nvidia_data or gemini_data, should find 0 discrepancies
    case_data = {
        "doc_type": "RM",
        "bs": [{"n": "Akshat Shah", "aadh": "123456789012"}]
    }
    findings = validator.validate(case_data)
    assert len(findings) == 0

def test_three_way_validator_matching():
    validator = ThreeWayValidator()
    case_data = {
        "doc_type": "RM",
        "bs": [{"n": "Akshat Shah", "aadh": "123456789012"}],
        "nvidia_data": {
            "bs": [{"n": "Akshat Shah", "aadh": "123456789012"}]
        },
        "gemini_data": {
            "bs": [{"n": "Akshat Shah", "aadh": "123456789012"}]
        }
    }
    findings = validator.validate(case_data)
    assert len(findings) == 0

def test_three_way_validator_mismatch():
    validator = ThreeWayValidator()
    case_data = {
        "doc_type": "RM",
        "bs": [{"n": "Akshat Shah", "aadh": "123456789012"}],
        "nvidia_data": {
            "bs": [{"n": "Akshat", "aadh": "123456789012"}] # Mismatch name
        },
        "gemini_data": {
            "bs": [{"n": "Akshat Shah", "aadh": "999999999999"}] # Mismatch Aadhaar
        }
    }
    findings = validator.validate(case_data)
    # We should have:
    # 1. Form name vs nvidia name mismatch
    # 2. Form aadhaar vs gemini aadhaar mismatch
    # 3. AI mismatch (Gemini name "Akshat Shah" vs NVIDIA name "Akshat")
    # 4. AI mismatch (Gemini aadhaar "999999999999" vs NVIDIA aadhaar "123456789012")
    assert len(findings) > 0
    
    explanations = [f.explanation for f in findings]
    assert any("is 'Akshat Shah' but NVIDIA pre-extracted 'Akshat'" in exp for exp in explanations)
    assert any("is '123456789012' but Gemini extracted '999999999999'" in exp for exp in explanations)
    assert any("AI Discrepancy" in exp for exp in explanations)

def test_three_way_validator_numeric_normalization():
    validator = ThreeWayValidator()
    case_data = {
        "doc_type": "RM",
        "ls": [{"amt": "10,00,000", "ten": "120"}],
        "nvidia_data": {
            "ls": [{"amt": "1000000.00", "ten": "120"}] # Should match after normalization
        }
    }
    findings = validator.validate(case_data)
    assert len(findings) == 0
