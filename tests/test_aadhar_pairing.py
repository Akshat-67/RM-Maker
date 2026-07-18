import pytest
from modules.rm.extractor import RMDataExtractor
from modules.sd.extractor import SDDataExtractor

def test_rm_aadhar_pairing_by_surname():
    extractor = RMDataExtractor(api_keys=["mock"])
    mock_response = {
        "unassigned_aadhars": [
            {
                "s": "Mr", "n": "Akshay Meena", "id": "12345", "adr": "",
                "files": [{"file": "img1.jpg", "type": "aadhar_front"}]
            },
            {
                "s": "", "n": "", "id": "", "adr": "Jaipur", "rn": "Ram Naresh Meena",
                "files": [{"file": "img2.jpg", "type": "aadhar_back"}]
            }
        ]
    }
    merged = extractor._merge_unpaired_aadhars(mock_response)
    uadhars = merged["unassigned_aadhars"]
    assert len(uadhars) == 1
    assert uadhars[0]["n"] == "Akshay Meena"
    assert uadhars[0]["adr"] == "Jaipur"
    assert uadhars[0]["rn"] == "Ram Naresh Meena"
    assert len(uadhars[0]["files"]) == 2

def test_sd_aadhar_pairing_by_proximity():
    extractor = SDDataExtractor(api_keys=["mock"])
    mock_response = {
        "unassigned_aadhars": [
            {
                "s": "Mr", "n": "Dinesh Sharma", "id": "12345", "adr": "",
                "files": [{"file": "Aadhar_Front_Dinesh.jpg", "type": "aadhar_front"}]
            },
            {
                "s": "", "n": "", "id": "", "adr": "Jaipur", "rn": "",
                "files": [{"file": "Aadhar_Back_Dinesh_1.jpg", "type": "aadhar_back"}]
            }
        ]
    }
    merged = extractor._merge_unpaired_aadhars(mock_response)
    uadhars = merged["unassigned_aadhars"]
    assert len(uadhars) == 1
    assert uadhars[0]["n"] == "Dinesh Sharma"
    assert uadhars[0]["adr"] == "Jaipur"

def test_already_paired_not_deleted():
    extractor = RMDataExtractor(api_keys=["mock"])
    mock_response = {
        "unassigned_aadhars": [
            {
                "s": "Mr", "n": "Monika Jain", "id": "9095", "adr": "Bundi",
                "files": [
                    {"file": "1.jpeg", "type": "aadhar_front"},
                    {"file": "2.jpeg", "type": "aadhar_back"}
                ]
            },
            {
                "s": "Mr", "n": "Deepesh Jain", "id": "2424", "adr": "Bundi",
                "files": [
                    {"file": "5.jpeg", "type": "aadhar_front"},
                    {"file": "6.jpeg", "type": "aadhar_back"}
                ]
            }
        ]
    }
    merged = extractor._merge_unpaired_aadhars(mock_response)
    uadhars = merged["unassigned_aadhars"]
    assert len(uadhars) == 2
    assert uadhars[0]["n"] == "Monika Jain"
    assert uadhars[1]["n"] == "Deepesh Jain"

