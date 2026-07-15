import pytest
from unittest.mock import patch, MagicMock
import os
from routes.cases import classify_case_pdfs, get_classified_report_texts
from services.validation.nim_proofreader import NIMProofreader

@patch('pypdf.PdfReader')
@patch('os.path.exists')
@patch('os.listdir')
def test_classify_case_pdfs(mock_listdir, mock_exists, mock_pdf_reader):
    mock_exists.return_value = True
    # Simulate directory files
    mock_listdir.side_effect = lambda path: ["report_a.pdf", "report_b.pdf", "doc_c.pdf"] if "files" in path or "legal_reports" in path else []
    
    # Mock PDF reader instances for different files
    mock_readers = []
    
    # 1. Technical Report (contains "3. VISIT DETAILS")
    reader_tech = MagicMock()
    page_tech = MagicMock()
    page_tech.extract_text.return_value = "Section 3. VISIT DETAILS\nAddress of Property: Plot 105"
    reader_tech.pages = [page_tech]
    
    # 2. Legal Report (contains "flow of title")
    reader_legal = MagicMock()
    page_legal = MagicMock()
    page_legal.extract_text.return_value = "Legal Scrutiny report. Flow of Title history: original sale deed"
    reader_legal.pages = [page_legal]
    
    # 3. Standard document (no markers)
    reader_other = MagicMock()
    page_other = MagicMock()
    page_other.extract_text.return_value = "Simple Scan of ID card"
    reader_other.pages = [page_other]
    
    def pdf_side_effect(filepath):
        if "report_a" in filepath:
            return reader_tech
        elif "report_b" in filepath:
            return reader_legal
        return reader_other
        
    mock_pdf_reader.side_effect = pdf_side_effect
    
    session = {
        "files": ["/mock/path/report_a.pdf", "/mock/path/report_b.pdf", "/mock/path/doc_c.pdf"],
        "legal_report_files": []
    }
    
    legal_files, technical_files = classify_case_pdfs("case_123", session)
    
    # Verify classifications
    assert any("report_b.pdf" in f for f in legal_files)
    assert any("report_a.pdf" in f for f in technical_files)
    assert not any("doc_c.pdf" in f for f in legal_files)
    assert not any("doc_c.pdf" in f for f in technical_files)


@patch('routes.cases.classify_case_pdfs')
@patch('utils.helpers.select_relevant_pdf_pages')
@patch('utils.helpers.extract_pdf_pages_text')
@patch('pypdf.PdfReader')
def test_get_classified_report_texts(mock_pdf_reader, mock_extract, mock_select, mock_classify):
    mock_classify.return_value = (["/mock/legal.pdf"], ["/mock/tech.pdf"])
    mock_select.return_value = [0]
    mock_extract.return_value = "Mocked PDF text output"
    
    # Mock PDF reader inside tech report loop
    mock_reader = MagicMock()
    mock_reader.pages = [MagicMock()]
    mock_pdf_reader.return_value = mock_reader
    
    session = {}
    legal_text, technical_text = get_classified_report_texts("case_123", session)
    
    assert "Mocked PDF text output" in legal_text
    assert "Mocked PDF text output" in technical_text


@patch('services.validation.nim_proofreader.OpenAI')
def test_nim_proofreader_rules_prompt(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='[]'))
    ]
    mock_client.chat.completions.create.return_value = mock_response
    
    findings = NIMProofreader.proofread(
        docx_text="Rendered deed text content",
        session_data={"bs": [{"n": "Aditya"}]},
        ocr_text="Raw scanned OCR text content",
        legal_text="Legal scrutiny report text content",
        tech_text="Technical report text content"
    )
    
    assert findings == []
    
    # Verify that the OpenAI client call was made and prompt contained the keywords/sections
    mock_client.chat.completions.create.assert_called_once()
    args, kwargs = mock_client.chat.completions.create.call_args
    prompt_content = kwargs['messages'][0]['content']
    
    # Assert all five content parts and custom rules exist in prompt
    assert "=== Ground Truth Variables (extracted/edited form data) ===" in prompt_content
    assert "=== Raw KYC Document OCR Text ===" in prompt_content
    assert "=== Legal Search Report Text ===" in prompt_content
    assert "=== Technical Valuation Report Text ===" in prompt_content
    assert "=== Rendered Deed Text ===" in prompt_content
    assert "Aditya Birla" in prompt_content
    assert "Cholamandalam" in prompt_content
    assert "seller/present owner" in prompt_content
    assert "title chain document/event" in prompt_content
