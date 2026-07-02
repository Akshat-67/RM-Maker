from modules.rm.extractor import RMDataExtractor

def test_rm_prefiltering_scores():
    extractor = RMDataExtractor(api_keys=[])
    # We have 5 pages.
    # Page 1: relevant
    # Page 2: non-relevant, but adjacent to Page 1 (so included)
    # Page 3: non-relevant, not adjacent to any relevant page (so filtered out)
    # Page 4: non-relevant, but adjacent to Page 5 (so included)
    # Page 5: relevant
    pages = [
        (1, "This page talks about loan agreement, mortgage, borrower details, and interest rate. It specifies the financial terms of the loan."),
        (2, "This page contains some generic legal text that does not talk about the terms or other details. Just filler text to occupy space."),
        (3, "Deeply historical information that has some random story about kings and queens from Europe. They lived in castles and fought battles."),
        (4, "More details that are not directly relevant but preceding the security. It talks about the general history of the region and landscape."),
        (5, "Guarantor property details list and schedule items original. It has the property description and schedules of the security.")
    ]
    texts, nums = extractor._filter_relevant_pages(pages, min_pages_threshold=1, score_threshold=1)
    
    # Page 1 and 5 must be in because they have relevant keywords.
    assert 1 in nums
    assert 5 in nums
    
    # Page 2 and 4 must be in because they are adjacent to page 1 and page 5 respectively.
    assert 2 in nums
    assert 4 in nums
    
    # Page 3 must NOT be in because it is non-relevant and not adjacent.
    assert 3 not in nums

def test_rm_prefiltering_threshold():
    extractor = RMDataExtractor(api_keys=[])
    pages = [
        (1, "loan"),
        (2, "random"),
        (3, "filler")
    ]
    # Since total pages (3) <= min_pages_threshold (5), it should bypass filtering.
    texts, nums = extractor._filter_relevant_pages(pages, min_pages_threshold=5, score_threshold=1)
    assert nums == [1, 2, 3]

def test_rm_prefiltering_no_match():
    extractor = RMDataExtractor(api_keys=[])
    pages = [
        (1, "This is a completely random page with historical text about ancient civilizations. It has absolutely no relevance to banking or lending."),
        (2, "Another page filled with random descriptions of nature, forests, rivers, and mountains. Used purely as placeholder text for this test."),
        (3, "The final page containing recipes for baking bread, cooking pasta, and making delicious desserts. Absolutely nothing about security.")
    ]
    # Since no pages match score_threshold, it should return all pages as fallback.
    texts, nums = extractor._filter_relevant_pages(pages, min_pages_threshold=1, score_threshold=1)
    assert nums == [1, 2, 3]

def test_rm_prefiltering_too_short():
    extractor = RMDataExtractor(api_keys=[])
    pages = [
        (1, "short loan text"),
    ]
    texts, nums = extractor._filter_relevant_pages(pages, min_pages_threshold=0, score_threshold=1)
    assert texts is None
    assert nums is None
