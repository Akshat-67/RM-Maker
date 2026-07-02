import os
import tempfile
from modules.sd.extractor import SDDataExtractor

def test_sd_legal_prefiltering_runs():
    extractor = SDDataExtractor(api_keys=["dummy_key"])
    called_contents = []
    def mock_call_gemini(model, contents, prompt):
        called_contents.extend(contents)
        return {"ps": [{"adr": "Mock Address"}]}
    extractor._call_gemini = mock_call_gemini
    
    # Create a dummy searchable PDF
    from reportlab.pdfgen import canvas
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "legal_report.pdf")
    
    # Generate a PDF with enough pages to trigger filtering (e.g. 10 pages)
    c = canvas.Canvas(pdf_path)
    # Page 1
    c.drawString(100, 750, "Cover Page of Legal Report")
    c.showPage()
    # Page 2
    c.drawString(100, 750, "This page talks about chain of title, विक्रय पत्र, and deeds.")
    c.showPage()
    # Page 3
    c.drawString(100, 750, "Another random page with nothing of relevance.")
    c.showPage()
    # Page 4
    c.drawString(100, 750, "Yet another page.")
    c.showPage()
    # Page 5
    c.drawString(100, 750, "Still nothing here.")
    c.showPage()
    # Page 6
    c.drawString(100, 750, "Some general instructions.")
    c.showPage()
    # Page 7
    c.drawString(100, 750, "More general stuff.")
    c.showPage()
    # Page 8
    c.drawString(100, 750, "Flow of ownership tracing details.")
    c.showPage()
    # Page 9
    c.drawString(100, 750, "Conclusion page.")
    c.showPage()
    # Page 10
    c.drawString(100, 750, "Signatures.")
    c.save()
    
    buckets = {"legal": [pdf_path]}
    result = extractor.extract_buckets_with_ai(buckets, "gemini-2.5-flash")
    assert result is not None
    assert "ps" in result
    assert result["ps"][0]["adr"] == "Mock Address"
    
    # Check that pre-filtering was actually called and passed page-filtered text to _call_gemini
    assert len(called_contents) > 0
    found_filtered = False
    for part in called_contents:
        if hasattr(part, 'text') and part.text and 'Legal Report Page-Filtered Content' in part.text:
            found_filtered = True
            # Let's also assert the page numbers that were kept/filtered
            # Page 2 and 8 are the only relevant ones (with adjacent pages).
            # So page 2 (with 1 and 3) and page 8 (with 7 and 9) should be present.
            assert "PAGE 2" in part.text
            assert "PAGE 8" in part.text
            assert "PAGE 5" not in part.text # Page 5 is not adjacent to 2 or 8 and is not relevant, so it shouldn't be here.
    assert found_filtered, "Did not find filtered text part in Gemini call contents!"

def test_sd_prefiltering_scores():
    extractor = SDDataExtractor(api_keys=[])
    # 5 pages
    # Page 1: relevant (contains 'chain of title')
    # Page 2: non-relevant, but adjacent to Page 1 (so included)
    # Page 3: non-relevant, not adjacent to any relevant page (so filtered out)
    # Page 4: non-relevant, but adjacent to Page 5 (so included)
    # Page 5: relevant (contains 'flow of ownership')
    pages = [
        (1, "This page talks about chain of title, history of title, and flow of title."),
        (2, "This page contains some generic legal text that does not talk about the terms or other details."),
        (3, "Deeply historical information that has some random story about kings and queens from Europe."),
        (4, "More details that are not directly relevant but preceding the security. History of the region."),
        (5, "Flow of ownership details list and schedule items.")
    ]
    texts, nums = extractor._filter_relevant_pages(pages, min_pages_threshold=1, score_threshold=1)
    
    assert nums is not None
    # Page 1 and 5 must be in because they have relevant keywords.
    assert 1 in nums
    assert 5 in nums
    
    # Page 2 and 4 must be in because they are adjacent to page 1 and page 5 respectively.
    assert 2 in nums
    assert 4 in nums
    
    # Page 3 must NOT be in because it is non-relevant and not adjacent.
    assert 3 not in nums

def test_sd_prefiltering_threshold():
    extractor = SDDataExtractor(api_keys=[])
    pages = [
        (1, "chain of title"),
        (2, "random text"),
        (3, "filler")
    ]
    # Since total pages (3) <= min_pages_threshold (5), it should bypass filtering.
    texts, nums = extractor._filter_relevant_pages(pages, min_pages_threshold=5, score_threshold=1)
    assert nums == [1, 2, 3]

def test_sd_prefiltering_no_match():
    extractor = SDDataExtractor(api_keys=[])
    pages = [
        (1, "This is a completely random page with historical text about ancient civilizations."),
        (2, "Another page filled with random descriptions of nature, forests, rivers, and mountains."),
        (3, "The final page containing recipes for baking bread, cooking pasta, and making delicious desserts.")
    ]
    # Since no pages match score_threshold, it should return all pages as fallback.
    texts, nums = extractor._filter_relevant_pages(pages, min_pages_threshold=1, score_threshold=1)
    assert nums == [1, 2, 3]

def test_sd_prefiltering_too_short():
    extractor = SDDataExtractor(api_keys=[])
    pages = [
        (1, "short"),
    ]
    # Since total text length < 200, it is detected as scanned PDF/too short and returns None, None
    texts, nums = extractor._filter_relevant_pages(pages, min_pages_threshold=0, score_threshold=1)
    assert texts is None
    assert nums is None
