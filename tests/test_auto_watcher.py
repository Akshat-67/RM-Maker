import os
import json
import pytest
import shutil
import time

from services.folder_watcher import scan_inbox_directory
from services.ingestion_pipeline import run_auto_ai_extraction
from services.session_manager import load_case_session, CASES_DIR

def test_folder_watcher_detection_and_extraction(tmp_path, monkeypatch):
    # Set monitored folder environment variable mock
    inbox_dir = os.path.join(tmp_path, "monitored_inbox")
    os.makedirs(inbox_dir, exist_ok=True)
    
    # Clean cases dir location mock for testing
    cases_dir_mock = os.path.join(tmp_path, "cases")
    os.makedirs(cases_dir_mock, exist_ok=True)
    monkeypatch.setattr("services.session_manager.CASES_DIR", cases_dir_mock)
    monkeypatch.setattr("services.folder_watcher.CASES_DIR", cases_dir_mock)
    monkeypatch.setattr("services.ingestion_pipeline.CASES_DIR", cases_dir_mock)
    
    # Create subfolder in monitored inbox ending in '-EX'
    case_folder_name = "Ankit Jain Capri RM -EX"
    case_folder_path = os.path.join(inbox_dir, case_folder_name)
    os.makedirs(case_folder_path, exist_ok=True)
    
    # Place numeric Aadhar file, Legal and Sanction files
    with open(os.path.join(case_folder_path, "1.jpeg"), "w") as f:
        f.write("mock front kyc")
    with open(os.path.join(case_folder_path, "L.pdf"), "w") as f:
        f.write("mock legal")
    with open(os.path.join(case_folder_path, "S.pdf"), "w") as f:
        f.write("mock sanction")
    with open(os.path.join(case_folder_path, "unnecessary_file.pdf"), "w") as f:
        f.write("mock unnecessary")
        
    monkeypatch.setenv("CASE_INBOX_DIR", inbox_dir)
    monkeypatch.setattr("utils.config.CASE_INBOX_DIR", inbox_dir)
    
    # Mock start_inbox_ingestion_thread to prevent async thread from running
    thread_called = []
    def mock_start_thread(case_id):
        thread_called.append(case_id)
        
    monkeypatch.setattr("services.folder_watcher.start_inbox_ingestion_thread", mock_start_thread)
    
    # Run watcher detection
    scan_inbox_directory()
    
    expected_case_id = "inbox_ankit_jain_capri_rm"
    assert len(thread_called) == 1
    assert thread_called[0] == expected_case_id
    
    # Verify session fields
    session = load_case_session(expected_case_id)
    assert session is not None
    assert session["case_name"] == "Ankit Jain Capri RM"
    assert session["is_auto_extraction"] is True
    assert session["status"] == "processing"
    
    # Mock the RMDataExtractor's extract_buckets_with_ai method
    class MockExtractor:
        def __init__(self, *args, **kwargs):
            pass
        def extract_buckets_with_ai(self, buckets, model, **kwargs):
            # Check that unnecessary_file.pdf is NOT in any bucket
            for b_files in buckets.values():
                assert "unnecessary_file.pdf" not in [os.path.basename(f) for f in b_files]
            
            return {
                "bank": "Capri Global Capital Limited",
                "borrower_count": 2,
                "loan_count": 1,
                "properties_count": 1,
                "bs": [{"n": "Ankit Jain", "a": "32"}],
                "ls": [{"a": "5000000"}]
            }
            
    monkeypatch.setattr("modules.rm.extractor.RMDataExtractor", MockExtractor)
    
    # Mock smart_merge to return the extracted payload directly
    def mock_smart_merge(old, new, verified_fields, **kwargs):
        return new
    monkeypatch.setattr("services.file_service.smart_merge", mock_smart_merge)
    
    # Populate raw files and buckets (normally done in run_ingestion_pipeline)
    session["files"] = [
        os.path.join(case_folder_path, "1.jpeg"),
        os.path.join(case_folder_path, "L.pdf"),
        os.path.join(case_folder_path, "S.pdf"),
        os.path.join(case_folder_path, "unnecessary_file.pdf")
    ]
    session["buckets"] = {
        "kyc": [os.path.join(case_folder_path, "1.jpeg")],
        "legal": [os.path.join(case_folder_path, "L.pdf")],
        "ats": [os.path.join(case_folder_path, "S.pdf")],
        "title_chain": [],
        "ocr": []
    }
    
    # Re-save session with files/buckets populated
    from services.session_manager import save_case_session
    save_case_session(
        case_id=expected_case_id,
        data=session.get("data", {}),
        files=session["files"],
        verified_fields=set(),
        bank="ICICI",
        borrower_count="1",
        loan_count="1",
        properties_count="1",
        doc_type="RM",
        status="processing",
        is_auto_extraction=True,
        buckets=session["buckets"]
    )
    
    # Run the auto-extraction function synchronously
    run_auto_ai_extraction(expected_case_id)
    
    # Verify the updated session
    updated_session = load_case_session(expected_case_id)
    assert updated_session["status"] == "ready"
    assert updated_session["bank"] == "CAPRI"
    assert updated_session["borrower_count"] == "2"
    assert updated_session["loan_count"] == "1"
    assert updated_session["properties_count"] == "1"
    
    # Verify entity lists resized and padded
    data = updated_session["data"]
    assert len(data["bs"]) == 2
    assert len(data["ls"]) == 1
    assert len(data["ps"]) == 1
