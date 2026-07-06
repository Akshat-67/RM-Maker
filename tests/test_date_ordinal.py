from utils.helpers import format_date_to_ordinal_english

def test_ordinal_date_formatting():
    # Test valid dates
    assert format_date_to_ordinal_english("29.06.2026") == "29th June, 2026"
    assert format_date_to_ordinal_english("01-01-2025") == "1st January, 2025"
    assert format_date_to_ordinal_english("02/02/2025") == "2nd February, 2025"
    assert format_date_to_ordinal_english("03.03.2025") == "3rd March, 2025"
    assert format_date_to_ordinal_english("11-11-2025") == "11th November, 2025"
    
    # Test fallback on empty/invalid
    assert format_date_to_ordinal_english("") == ""
    assert format_date_to_ordinal_english(None) == ""
    assert format_date_to_ordinal_english("not-a-date") == "not-a-date"
