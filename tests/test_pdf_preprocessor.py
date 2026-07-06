import os
import pytest
from utils.helpers import select_relevant_pdf_pages, extract_pdf_pages_text

def test_preprocessor_empty_or_invalid():
    # Verify fallback on invalid files
    assert select_relevant_pdf_pages("nonexistent.pdf") == []
    assert extract_pdf_pages_text("nonexistent.pdf", [0]) == ""
