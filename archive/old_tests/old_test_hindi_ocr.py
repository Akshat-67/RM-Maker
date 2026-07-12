import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extractor import DataExtractor

def test_prompts():
    print("Testing prompt generation...")
    extractor = DataExtractor(api_keys=["TEST_KEY"])
    
    # 1. Test build SD prompt
    prompt = extractor._build_sd_prompt(
        expected_sellers=2,
        expected_buyers=1,
        expected_witnesses=2,
        seller_hints="Vivek Saxena",
        buyer_hints="Vijay Laxmi",
        current_data=None
    )
    assert "Sellers:2" in prompt, "Failed to compile expected Sellers in prompt"
    assert "Buyers:1" in prompt, "Failed to compile expected Buyers in prompt"
    assert "Vivek Saxena" in prompt, "Failed to compile seller hints in prompt"
    print("✓ Prompt builder test passed!")

def test_normalization():
    print("Testing Sale Deed normalization pipeline...")
    extractor = DataExtractor(api_keys=["TEST_KEY"])
    
    dummy_ai_data = {
        "sellers": [
            {
                "s": "Mr.",
                "n": "विवेक सक्सेना",
                "a": "58",
                "r": "Son of",
                "rn": "जे.बी. सक्सेना",
                "caste": "हिन्दू",
                "adr": "Care of Mr. J.B. Saxena, फ्लैट न. 101, जयपुर",
                "id": "1234 5678 9012"
            }
        ],
        "buyers": [
            {
                "s": "Mrs.",
                "n": "विजय लक्ष्मी",
                "a": "25",
                "r": "Wife of",
                "rn": "धर्मेंद्र सिंह",
                "caste": "हिन्दू",
                "adr": "एफ-115, मुहाना, जयपुर",
                "id": "9876 5432 1098"
            }
        ],
        "ps": [
            {
                "flat_no": "एस-1",
                "floor": "द्वितीय",
                "building": "साईं रेजीडेंसी",
                "adr": "कृष्णपुरी, जयपुर",
                "area": "1087.19",
                "area_unit": "वर्ग फुट",
                "parking": "Yes",
                "e": "रोड",
                "w": "प्लॉट"
            }
        ],
        "ws": [
            {
                "n": "witness1",
                "r": "S/o",
                "rn": "father",
                "adr": "address"
            }
        ]
    }
    
    normalized = extractor._normalize_response(
        dummy_ai_data,
        doc_type="SD",
        expected_sellers=2,
        expected_buyers=1,
        expected_witnesses=2
    )
    
    # Assert counts are forced correctly
    assert len(normalized["sellers"]) == 2, f"Expected 2 sellers, got {len(normalized['sellers'])}"
    assert len(normalized["buyers"]) == 1, f"Expected 1 buyer, got {len(normalized['buyers'])}"
    assert len(normalized["ws"]) == 2, f"Expected 2 witnesses, got {len(normalized['ws'])}"
    
    # Assert cleaning rules (strip Care of)
    cleaned_address = normalized["sellers"][0]["adr"]
    assert "Care of" not in cleaned_address, f"Parentage prefix clean failed: {cleaned_address}"
    assert "Mr. J.B. Saxena" not in cleaned_address, f"Parentage name clean failed: {cleaned_address}"
    
    # Assert salutation normalization for Hindi relatives and witnesses
    assert normalized["sellers"][0]["rn"] == "Mr. जे.बी. सक्सेना", f"Salutation prefix failed: {normalized['sellers'][0]['rn']}"
    assert normalized["buyers"][0]["rn"] == "Mr. धर्मेंद्र सिंह"
    assert normalized["ws"][0]["rn"] == "Mr. father"
    
    # Assert property details have boundaries padded
    assert normalized["ps"][0]["s"] == ""
    assert normalized["ps"][0]["n"] == ""
    assert normalized["ps"][0]["e"] == "रोड"
    
    print("✓ Normalization test passed!")

if __name__ == "__main__":
    test_prompts()
    test_normalization()
    print("All extraction/OCR tests passed successfully!")
