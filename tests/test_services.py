import os
import json
import shutil
import pytest
import services.session_manager
import services.file_service

@pytest.fixture
def temp_cases_dir(tmp_path):
    """Overrides CASES_DIR with a temporary path to avoid touching production data."""
    old_cases_dir = services.session_manager.CASES_DIR
    test_dir = str(tmp_path / "cases")
    
    # Apply override to both services
    services.session_manager.CASES_DIR = test_dir
    services.file_service.CASES_DIR = test_dir
    
    yield test_dir
    
    # Restore original setting
    services.session_manager.CASES_DIR = old_cases_dir
    services.file_service.CASES_DIR = old_cases_dir

@pytest.fixture
def temp_templates_dir(tmp_path):
    """Overrides TEMPLATES_DIR with a mocked temporary folder structure."""
    old_templates_dir = services.file_service.TEMPLATES_DIR
    test_dir = str(tmp_path / "templates")
    services.file_service.TEMPLATES_DIR = test_dir
    
    # Build a mock templates folder hierarchy
    os.makedirs(os.path.join(test_dir, "ICICI"), exist_ok=True)
    os.makedirs(os.path.join(test_dir, "SBI"), exist_ok=True)
    os.makedirs(os.path.join(test_dir, "SALE_DEED"), exist_ok=True)
    
    # Write empty docx files matching template pattern naming
    with open(os.path.join(test_dir, "ICICI", "RM_ICICI_2B_1L.docx"), "w") as f:
        f.write("mock")
    with open(os.path.join(test_dir, "SBI", "RM_SBI_1B_2L_two properties.docx"), "w") as f:
        f.write("mock")
    with open(os.path.join(test_dir, "SALE_DEED", "SD_NAME_2S_1B.docx"), "w") as f:
        f.write("mock")
        
    yield test_dir
    
    services.file_service.TEMPLATES_DIR = old_templates_dir


# --- services/session_manager.py Tests ---

def test_creating_new_session(temp_cases_dir):
    from services.session_manager import save_case_session, load_case_session
    case_id = "case_new_test"
    
    session = save_case_session(
        case_id=case_id,
        data={"Chain_Text": "Some timeline narrative"},
        files=["file.pdf"],
        verified_fields={"Chain_Text"},
        bank="ICICI",
        borrower_count="1",
        loan_count="1"
    )
    
    assert os.path.exists(os.path.join(temp_cases_dir, case_id, "session.json"))
    assert session["id"] == case_id
    assert session["bank"] == "ICICI"
    assert session["files"] == ["file.pdf"]
    assert session["data"]["Chain_Text"] == "Some timeline narrative"

def test_save_then_load_returns_identical_data(temp_cases_dir):
    from services.session_manager import save_case_session, load_case_session
    case_id = "case_identical_test"
    
    data = {
        "Chain_Text": "Chain details here",
        "ps": [{"adr": "Plot 12, Sanganer", "area": "100", "area_unit": "Sq Yd"}]
    }
    
    save_case_session(
        case_id=case_id,
        data=data,
        files=["doc1.docx"],
        verified_fields={"Chain_Text"},
        bank="SBI",
        borrower_count="2",
        loan_count="1",
        doc_type="RM"
    )
    
    loaded = load_case_session(case_id)
    assert loaded is not None
    assert loaded["id"] == case_id
    assert loaded["data"]["Chain_Text"] == data["Chain_Text"]
    assert loaded["data"]["ps"][0]["adr"] == data["ps"][0]["adr"]
    assert loaded["bank"] == "SBI"
    assert loaded["verified_fields"] == ["Chain_Text"]

def test_unknown_future_fields_survive(temp_cases_dir):
    from services.session_manager import save_case_session, load_case_session
    case_id = "case_future_test"
    
    # 1. Save session first with standard fields
    session = save_case_session(
        case_id=case_id,
        data={"Chain_Text": "Standard text"},
        files=[],
        verified_fields=set(),
        bank="SBI",
        borrower_count="1",
        loan_count="1"
    )
    
    # 2. Simulate injecting a future field directly inside the loaded session JSON
    path = os.path.join(temp_cases_dir, case_id, "session.json")
    with open(path, "r", encoding="utf-8") as f:
        sess_dict = json.load(f)
    sess_dict["future_telemetry_token"] = "xyz789"
    sess_dict["another_extra_future_dict"] = {"enabled": True}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sess_dict, f)
        
    # 3. Reload case session - must load these keys
    loaded = load_case_session(case_id)
    assert loaded["future_telemetry_token"] == "xyz789"
    assert loaded["another_extra_future_dict"] == {"enabled": True}
    
    # 4. Save session again - should preserve future keys
    save_case_session(
        case_id=case_id,
        data={"Chain_Text": "Updated text"},
        files=[],
        verified_fields=set(),
        bank="SBI",
        borrower_count="1",
        loan_count="1"
    )
    
    reloaded = load_case_session(case_id)
    assert reloaded["future_telemetry_token"] == "xyz789"
    assert reloaded["another_extra_future_dict"] == {"enabled": True}

def test_rm_fields_survive(temp_cases_dir):
    from services.session_manager import save_case_session, load_case_session
    case_id = "case_rm_fields"
    
    data = {
        "rd": "2026-07-10",
        "Chain_Text": "Timeline of RM",
        "second_schedule": "Schedule details",
        "bsign": {"n": "John", "pan": "ABCDE1234F"},
        "ps": [{"adr": "Plot A", "lat": 26.9}],
        "ls": [{"w": "Ten Lakhs"}],
        "some_non_rm_field": "should be pruned"
    }
    
    save_case_session(
        case_id=case_id,
        data=data,
        files=[],
        verified_fields=set(),
        bank="ICICI",
        borrower_count="1",
        loan_count="1",
        doc_type="RM"
    )
    
    loaded = load_case_session(case_id)
    assert loaded["data"]["rd"] == "2026-07-10"
    assert loaded["data"]["Chain_Text"] == "Timeline of RM"
    assert loaded["data"]["second_schedule"] == "Schedule details"
    assert loaded["data"]["bsign"]["n"] == "John"
    assert loaded["data"]["ps"][0]["adr"] == "Plot a"
    assert "some_non_rm_field" not in loaded["data"]

def test_sd_fields_survive(temp_cases_dir):
    from services.session_manager import save_case_session, load_case_session
    case_id = "case_sd_fields"
    
    data = {
        "consideration": "5000000",
        "tds": "50000",
        "hypothecation": "None",
        "ss": [{"n": "Seller One", "is_bpl": False}],
        "bs": [{"n": "Buyer One", "pan": "ABCDE1234F"}],
        "ps": [{"plot_no": "15", "scheme": "Rampuri"}],
        "some_non_sd_field": "should be pruned"
    }
    
    save_case_session(
        case_id=case_id,
        data=data,
        files=[],
        verified_fields=set(),
        bank="SBI",
        borrower_count="1",
        loan_count="1",
        doc_type="SD"
    )
    
    loaded = load_case_session(case_id)
    assert loaded["data"]["consideration"] == "5000000"
    assert loaded["data"]["tds"] == "50000"
    assert loaded["data"]["ss"][0]["n"] == "Seller One"
    assert loaded["data"]["bs"][0]["n"] == "Buyer One"
    assert loaded["data"]["ps"][0]["plot_no"] == "15"
    assert "some_non_sd_field" not in loaded["data"]

def test_hindi_digit_conversion(temp_cases_dir):
    from services.session_manager import save_case_session, load_case_session
    case_id = "case_hindi_digits"
    
    data = {
        "Chain_Text": "वर्ष २०१५ में खरीदा",
        "ps": [{"area": "१२०"}]
    }
    
    save_case_session(
        case_id=case_id,
        data=data,
        files=[],
        verified_fields=set(),
        bank="SBI",
        borrower_count="1",
        loan_count="1",
        doc_type="RM"
    )
    
    loaded = load_case_session(case_id)
    # Devanagari digits २०१५ -> 2015 and १२० -> 120
    assert loaded["data"]["Chain_Text"] == "वर्ष 2015 में खरीदा"
    assert loaded["data"]["ps"][0]["area"] == "120"

def test_empty_missing_session_handling(temp_cases_dir):
    from services.session_manager import load_case_session
    # Unknown/missing case_id must return None cleanly without raising exceptions
    assert load_case_session("non_existent_case_id") is None


# --- services/file_service.py Tests ---

def test_smart_merge_keeps_existing():
    from services.file_service import smart_merge
    old = {
        "rd": "2026-07-01",
        "ps": [{"adr": "Address One", "area": "100"}],
        "bsign": {"n": "Old Name", "a": "35"}
    }
    new = {
        "rd": "2026-07-10",
        "ps": [{"adr": "Address One", "area": "200"}],
        "bsign": {"n": "New Name"}
    }
    
    merged = smart_merge(old, new, verified_fields=set())
    
    assert merged["rd"] == "2026-07-10"
    # Merges list of dictionaries by key (adr is the key for ps)
    assert merged["ps"][0]["area"] == "200"
    # Preserves older field if omitted in new dictionary
    assert merged["bsign"]["a"] == "35"
    assert merged["bsign"]["n"] == "New Name"

def test_smart_merge_ignores_empty_overwrites():
    from services.file_service import smart_merge
    old = {
        "rd": "2026-07-01",
        "bsign": {"n": "Old Name", "a": "35"}
    }
    new = {
        "rd": "",
        "bsign": {"n": ""}
    }
    
    # smart_merge must ignore empty string overwrites and preserve populated fields
    merged = smart_merge(old, new, verified_fields=set())
    assert merged["rd"] == "2026-07-01"
    assert merged["bsign"]["n"] == "Old Name"
    assert merged["bsign"]["a"] == "35"

def test_template_discovery(temp_templates_dir):
    from services.file_service import discover_templates
    template_map, sd_template_map, bank_folders = discover_templates()
    
    # Verify discover_templates scans directories correctly
    assert "SBI" in bank_folders
    assert "ICICI" in bank_folders
    assert "2" in sd_template_map  # SD_NAME_2S_1B.docx parses as 2 sellers
    assert "1" in sd_template_map["2"]
    
    assert template_map["ICICI"]["2"]["1"]["1"].endswith("RM_ICICI_2B_1L.docx")
    assert template_map["SBI"]["1"]["2"]["2"].endswith("RM_SBI_1B_2L_two properties.docx")

def test_missing_files_handled_safely(temp_cases_dir):
    from services.file_service import resolve_case_file_path, remove_file_from_disk
    
    # Path resolution returns None for directory
    dir_path, name = resolve_case_file_path("test_case", "non_existent_file.docx")
    assert dir_path is None
    assert name == "non_existent_file.docx"
    
    # Deleting missing files returns false and doesn't crash
    success, err = remove_file_from_disk("test_case", "non_existent_file.docx")
    assert success is False
    assert err == "File not found"

def test_save_valuation_quote_preserves_session(temp_cases_dir):
    from services.session_manager import save_case_session, load_case_session
    case_id = "case_valuation_quote_test"
    
    # 1. Setup a valid SD session
    data = {
        "consideration": "2500000",
        "ss": [{"n": "Seller Alice"}],
        "bs": [{"n": "Buyer Bob"}]
    }
    files = ["aadhaar_alice.pdf"]
    verified_fields = {"consideration", "ss"}
    
    save_case_session(
        case_id=case_id,
        data=data,
        files=files,
        verified_fields=verified_fields,
        bank="",
        borrower_count="1",
        loan_count="1",
        doc_type="SD"
    )
    
    # 2. Simulate saving a valuation quote by calling save_case_session with valuation_quote kwarg
    session = load_case_session(case_id)
    assert session is not None
    
    quote_data = {
        "stamp_duty": "125000",
        "registration_fee": "25000",
        "cess_surcharge": "2500",
        "total_fee": "152500",
        "timestamp": "2026-07-10T22:15:00"
    }
    
    # Call save_case_session with all proper parameters (replicating fixed endpoint call)
    save_case_session(
        case_id=case_id,
        data=session.get("data", {}),
        files=session.get("files", []),
        verified_fields=set(session.get("verified_fields", [])),
        bank=session.get("bank", ""),
        borrower_count=session.get("borrower_count", "1"),
        loan_count=session.get("loan_count", "1"),
        properties_count=session.get("properties_count", "1"),
        doc_type=session.get("doc_type", "SD"),
        sellers_count=session.get("sellers_count", "1"),
        buyers_count=session.get("buyers_count", "1"),
        valuation_quote=quote_data
    )
    
    # 3. Reload session and verify no corruption occurred
    reloaded = load_case_session(case_id)
    assert reloaded is not None
    
    # Verify valuation_quote is correctly saved at the top level
    assert reloaded["valuation_quote"] == quote_data
    
    # Verify core session fields are intact and not corrupted
    assert reloaded["doc_type"] == "SD"
    assert reloaded["files"] == files
    assert sorted(reloaded["verified_fields"]) == sorted(list(verified_fields))
    assert reloaded["data"]["consideration"] == "2500000"
    assert reloaded["data"]["ss"][0]["n"] == "Seller Alice"
    assert reloaded["data"]["bs"][0]["n"] == "Buyer Bob"


# --- services/epanjiyan_service.py Tests ---

def test_split_address():
    from services.epanjiyan_service import split_address
    
    # 1. Address with pincode, state, and plot prefix
    addr = "PLOT NO. 115-A, KESAR NAGAR, MANSAROVAR, JAIPUR, RAJASTHAN 302020"
    split = split_address(addr)
    assert split["house_no"] == "115-A"
    assert split["colony"] == "KESAR NAGAR"
    assert split["area"] == "MANSAROVAR"
    assert split["city"] == "JAIPUR"
    assert split["pincode"] == "302020"
    
    # 2. Simple clean-up
    assert split_address("") == {
        "house_no": "00",
        "colony": "",
        "area": "",
        "city": "JAIPUR",
        "pincode": ""
    }

def test_format_recent_cases():
    from services.epanjiyan_service import format_recent_cases
    import time
    
    cases = [
        {
            "id": "case_rm",
            "doc_type": "RM",
            "last_updated": 1774000000,
            "data": {
                "bs": [{"n": "Jane Doe"}],
                "bsign": {"n": "Auth Sig"}
            }
        },
        {
            "id": "case_sd",
            "doc_type": "SD",
            "last_updated": 1774000100,
            "data": {
                "es": [{"n": "Seller Bob"}],
                "purchaser_name": "Buyer Jane"
            }
        }
    ]
    
    recent = format_recent_cases(cases)
    assert len(recent) == 2
    assert recent[0]["case_id"] == "case_rm"
    assert recent[0]["name"] == "JANE DOE"
    assert recent[1]["case_id"] == "case_sd"
    assert recent[1]["name"] == "SELLER BOB"

def test_generate_epanjiyan_payload():
    from services.epanjiyan_service import generate_epanjiyan_payload
    import datetime
    
    # Setup mock session for SD
    session = {
        "id": "case_101",
        "doc_type": "SD",
        "bank": "",
        "data": {
            "public_dlc_profile": {"sro": "JODHPUR-II"},
            "ss": [{
                "n": "Seller Alice",
                "rn": "Father Bob",
                "s": "Mr",
                "r": "S/O",
                "adr": "House 12, Area X, Jaipur",
                "c": "General",
                "is_bpl": False,
                "a": "45",
                "id": "1234 5678 9012",
                "pan": "ABCDE1234F"
            }],
            "bs": [{
                "n": "Buyer Charlie",
                "rn": "Father Dave",
                "s": "Mr",
                "r": "S/O",
                "adr": "House 15, Area Y, Jodhpur",
                "a": "30",
                "id": "9876 5432 1098",
                "pan": "XYZW9876A"
            }],
            "ws": [{
                "n": "Witness Walter",
                "rn": "Father William",
                "r": "S/O",
                "adr": "House 20, Area Z, Jaipur",
                "a": "35",
                "id": "1111 2222 3333"
            }],
            "ps": [{
                "adr": "Property Address, Area X",
                "area": "150",
                "road_width": 40,
                "lat": "26.5",
                "lng": "75.8",
                "e_en": "East boundary",
                "w_en": "West boundary",
                "n_en": "North boundary",
                "s_en": "South boundary"
            }]
        }
    }
    
    payload = generate_epanjiyan_payload(session)
    
    assert payload["case_id"] == "case_101"
    assert payload["doc_type"] == "SD"
    assert payload["sro"] == "JODHPUR-II"
    assert payload["tehsil"] == "JODHPUR"
    assert payload["execution_date"] == datetime.date.today().strftime("%d-%m-%Y")
    
    # Verify Executants (Sellers) mapping
    assert len(payload["executants"]) == 1
    assert payload["executants"][0]["name_en"] == "SELLER ALICE"
    assert payload["executants"][0]["gender"] == "MALE"
    assert payload["executants"][0]["aadhaar"] == "123456789012"
    
    # Verify Claimant (Buyers) mapping
    assert payload["claimant"]["name_en"] == "BUYER CHARLIE"
    assert payload["claimant"]["gender"] == "MALE"
    assert payload["claimant"]["aadhaar"] == "987654321098"
    
    # Verify Witnesses mapping
    assert len(payload["witnesses"]) == 1
    assert payload["witnesses"][0]["name_en"] == "WITNESS WALTER"
    
    # Verify Properties mapping
    assert len(payload["properties"]) == 1
    assert payload["properties"][0]["area"] == "150"
    assert payload["properties"][0]["east"] == "East boundary"


# --- services/ai_client.py Tests ---

def test_ai_client_init():
    from services.ai_client import AIClient
    
    keys = ["key1", "key2", "key3"]
    client = AIClient(api_keys=keys)
    assert client.api_keys == keys
    assert client.active_key_index == 0

def test_ai_client_rotation():
    from services.ai_client import AIClient
    
    keys = ["key1", "key2"]
    client = AIClient(api_keys=keys)
    assert client.active_key_index == 0
    
    rotated = client._rotate_key()
    assert rotated is True
    assert client.active_key_index == 1
    
    rotated = client._rotate_key()
    assert rotated is True
    assert client.active_key_index == 0

def test_ai_client_list_models_default():
    from services.ai_client import AIClient
    
    client = AIClient()
    models = client.list_models()
    assert "gemini-2.5-flash" in models


# --- delete_case_directory Tests ---

def test_delete_case_directory(temp_cases_dir):
    from services.file_service import delete_case_directory
    
    case_id = "test_delete_case_123"
    case_path = os.path.join(temp_cases_dir, case_id)
    os.makedirs(case_path, exist_ok=True)
    assert os.path.exists(case_path)
    
    # Run deletion
    res = delete_case_directory(case_id)
    assert res is True
    assert not os.path.exists(case_path)
    # Run deletion on non-existent case
    res2 = delete_case_directory("non_existent_case_abc")
    assert res2 is False

