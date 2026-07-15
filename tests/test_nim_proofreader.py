import os
from unittest.mock import patch, MagicMock
from services.validation.nim_proofreader import NIMProofreader
from services.validation.name_match_validator import NameMatchValidator

@patch('services.validation.nim_proofreader.OpenAI')
def test_proofreader_mock(mock_openai):
    # Setup mock response
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='[{"category": "proofreader", "severity": "high", "explanation": "Duplicate word Mr. Mr. found", "suggested_fix": "Fix duplicates"}]'))
    ]
    mock_client.chat.completions.create.return_value = mock_response
    
    findings = NIMProofreader.proofread("Mr. Mr. John Doe", {"bs": [{"n": "John Doe"}]})
    assert len(findings) == 1
    assert findings[0].severity == "high"
    assert findings[0].explanation == "Duplicate word Mr. Mr. found"


def test_name_match_validator_empty():
    val = NameMatchValidator()
    # If no files or case ID, should return empty
    res = val.validate({"id": "non_existent_case_123"})
    assert res == []
