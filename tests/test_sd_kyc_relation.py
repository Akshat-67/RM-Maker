import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.sd.extractor import SDDataExtractor
from utils.helpers import normalize_name_salutation, normalize_relation_prefix, parse_relation_text


def test_sd_relation_labels_from_kyc_are_normalized_and_split():
    samples = {
        "पिता का नाम मोहनलाल": ("पुत्र", "श्री मोहनलाल"),
        "पति का नाम रामलाल": ("पत्नी", "श्री रामलाल"),
        "Father's Name Mohan Lal": ("पुत्र", "श्री Mohan Lal"),
        "Husband Name Ram Lal": ("पत्नी", "श्री Ram Lal"),
    }

    for raw, expected in samples.items():
        normalized = normalize_relation_prefix(raw, "SD")
        assert parse_relation_text(normalized) == expected


def test_sd_bucket_final_normalization_splits_unassigned_aadhaar_relation_text():
    extractor = SDDataExtractor(api_keys=[])
    data = {
        "unassigned_aadhars": [
            {
                "s": "श्री",
                "n": "रमेश",
                "a": "40",
                "relation_text": "पिता का नाम मोहनलाल",
                "adr": "जयपुर",
                "id": "1234",
            }
        ]
    }

    normalized = extractor._normalize_final_data(data, None, None, None)

    aadhaar = normalized["unassigned_aadhars"][0]
    assert aadhaar["relation_text"] == "पुत्र श्री मोहनलाल"
    assert aadhaar["r"] == "पुत्र"
    assert aadhaar["rn"] == "श्री मोहनलाल"


def test_sd_kyc_late_name_uses_swargiya_prefix():
    assert normalize_name_salutation("Late Mohan Lal") == "स्वर्गीय श्री Mohan Lal"
    assert normalize_name_salutation("स्व. मोहनलाल") == "स्वर्गीय श्री मोहनलाल"


def test_sd_kyc_late_relative_name_uses_swargiya_prefix():
    normalized = normalize_relation_prefix("Father's Name Late Mohan Lal", "SD")
    assert normalized == "पुत्र स्वर्गीय श्री Mohan Lal"
    assert parse_relation_text(normalized) == ("पुत्र", "स्वर्गीय श्री Mohan Lal")


def test_convert_hindi_digits_to_english():
    from utils.helpers import convert_hindi_digits_to_english
    data = {
        "adr": "फ्लैट न.लग-१ लोअर विनायक",
        "nested": [
            "१०१, पहली मंजिल",
            {"number": "२८, सेक्टर ४"}
        ]
    }
    expected = {
        "adr": "फ्लैट न.लग-1 लोअर विनायक",
        "nested": [
            "101, पहली मंजिल",
            {"number": "28, सेक्टर 4"}
        ]
    }
    assert convert_hindi_digits_to_english(data) == expected
