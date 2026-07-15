from services.validation.gender_validator import GenderValidator
from services.validation.missing_fields_validator import MissingFieldsValidator
from services.validation.template_validator import TemplateValidator

def test_gender_validator():
    val = GenderValidator()
    # Mr. with relation W/o must trigger high discrepancy
    case_data = {
        "bs": [{"s": "Mr.", "r": "W/o", "rn": "John", "gender": "Female"}],
        "doc_type": "RM"
    }
    res = val.validate(case_data)
    assert len(res) > 0
    assert res[0].severity == "high"
    assert res[0].category == "gender"

def test_missing_fields_validator():
    val = MissingFieldsValidator()
    case_data = {
        "rd": "",
        "bs": [{"n": "", "id": "", "adr": "", "rn": ""}],
        "ls": [],
        "ps": [],
        "doc_type": "RM"
    }
    res = val.validate(case_data)
    assert len(res) > 0
    categories = [d.category for d in res]
    assert "missing" in categories

def test_template_validator():
    val = TemplateValidator()
    case_data = {
        "selected_template": "RM_ICICI_2B_1L.docx",
        "bs": [{"n": "Akshat Sharma"}], # Only 1 active borrower
        "ls": [{"a": "500000"}],
        "doc_type": "RM"
    }
    res = val.validate(case_data)
    assert len(res) > 0
    assert "Borrower(s)" in res[0].explanation
