import pytest
import os
import sys
import tempfile
import shutil

# Add project root to sys.path
sys.path.append(r"c:\Users\aksha\Documents\RM Generator\RM-Maker\RM-Maker-MAIN")

from utils.helpers import validate_case_id, format_date_to_ordinal_english, convert_hindi_digits_to_english, amount_to_words, format_indian_currency
from modules.rm.processor import RMTemplateProcessor
from services.generation_service import compile_and_render_document, _prepare_context

def test_validate_case_id_security():
    # Attempting traversal or command injection payloads
    assert not validate_case_id("../case_123")
    assert not validate_case_id("case_123/../../abc")
    assert not validate_case_id("case_123; rm -rf /")
    assert not validate_case_id("case_123.json")
    assert not validate_case_id("inbox_abc/../xyz")
    assert not validate_case_id("")
    assert not validate_case_id(None)
    assert not validate_case_id(12345)

def test_ordinal_date_boundaries():
    # Pass weird formatting, null values, or unexpected types
    assert format_date_to_ordinal_english("") == ""
    assert format_date_to_ordinal_english(None) == ""
    # Should fallback gracefully without throwing exception
    assert format_date_to_ordinal_english("gibberish-date") == "gibberish-date"
    assert format_date_to_ordinal_english("31/12/9999") == "31st December, 9999"
    assert format_date_to_ordinal_english("01-01-1900") == "1st January, 1900"
    assert format_date_to_ordinal_english("29-02-2024") == "29th February, 2024" # Leap year
    assert format_date_to_ordinal_english("29-02-2023") == "29-02-2023" # Invalid leap day

def test_digit_conversion_robustness():
    # Hindi to English digit conversion boundary cases
    assert convert_hindi_digits_to_english(None) is None
    assert convert_hindi_digits_to_english(123) == 123
    assert convert_hindi_digits_to_english("०१२३४५६७८९") == "0123456789"
    
    # Complex dictionary structures
    nested = {
        "a": "१२३",
        "b": ["४५६", {"c": "७८९"}]
    }
    expected = {
        "a": "123",
        "b": ["456", {"c": "789"}]
    }
    assert convert_hindi_digits_to_english(nested) == expected

def test_currency_formatting_boundary_cases():
    # Try formatting weird character inputs or extremely large numbers
    assert format_indian_currency("1000") == "1,000/-"
    assert format_indian_currency("100000") == "1,00,000/-"
    assert format_indian_currency("10000000") == "1,00,00,000/-"
    assert format_indian_currency("") == ""
    assert format_indian_currency(None) == ""
    # Gibberish input should return unmodified
    assert format_indian_currency("one thousand") == "one thousand"
    # Extremely large numbers
    huge = "9" * 30
    assert format_indian_currency(huge).endswith("/-")

def test_context_preparation_with_extreme_structures():
    # Test preparing context when fields are completely missing, empty or structured differently
    minimal_data = {}
    context = _prepare_context(minimal_data, doc_type="RM")
    
    # Ensure nested fields are padded properly up to default sizes without raising key errors
    assert isinstance(context["bs"], list)
    assert len(context["bs"]) >= 10
    assert isinstance(context["ws"], list)
    assert len(context["ws"]) >= 10
    assert isinstance(context["ds"], list)
    assert len(context["ds"]) >= 10

def test_docx_template_compilation_under_hostile_injections():
    # Inject scripts, SQL code, long strings, or custom characters to see if it breaks rendering
    hostile_context = {
        "rd": "12.12.2024",
        "ad": "12.12.2024",
        "bs": [{
            "n": "<script>alert('xss')</script> SELECT * FROM Users --", 
            "adr": "'; DROP TABLE cases; -- \n新世代 😭 Unicode Test"
        }],
        "ls": [{"a": "9999999999999999999", "w": "A" * 1000}],
        "ps": [{"adr": "PLOT 1" * 50}],
        "ws": [{"n": "Witness 1"}, {"n": "Witness 2"}],
        "bsign": {"n": "Signer 1"},
        "second_schedule": "Multiline Doc Schedule Line 1\nLine 2\nLine 3"
    }
    
    template_path = r"c:\Users\aksha\Documents\RM Generator\RM-Maker\RM-Maker-MAIN\templates\ICICI\RM_ICICI_1B_1L(One Property).docx"
    if not os.path.exists(template_path):
        pytest.skip("Template not found for integration compile check")
        
    processor = RMTemplateProcessor(template_path)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "hostile_rendered.docx")
        
        # Test rendering – must not raise XML or parsing exceptions
        processor.generate(hostile_context, out_path, highlight_ai=True, highlight_missing=True)
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0
