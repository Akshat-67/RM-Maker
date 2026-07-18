import os
import json
import pytest
import shutil
from services.ingestion_pipeline import classify_file_type
from services.session_manager import list_cases, CASES_DIR

def test_local_pdf_classification(tmp_path):
    # Create mock PDF file
    pdf_path = os.path.join(tmp_path, "mock_sanction.pdf")
    
    # We can write simple dummy text, but pypdf requires a valid PDF format.
    # To mock PDF classification without generating binary PDFs, let's mock or verify
    # file type classification by filename keyword fallback:
    label = classify_file_type(os.path.join(tmp_path, "customer_sanction_letter.pdf"))
    assert label == "Sanction_Letter"
    
    label_legal = classify_file_type(os.path.join(tmp_path, "title_scrutiny_report.pdf"))
    assert label_legal == "Legal_Report"
    
    label_tech = classify_file_type(os.path.join(tmp_path, "technical_visit_valuation.pdf"))
    assert label_tech == "Technical_Report"

def test_exif_fallback_labeling(tmp_path):
    label_pan = classify_file_type(os.path.join(tmp_path, "pan_card_holder.jpg"))
    assert label_pan == "PAN"
    
    label_front = classify_file_type(os.path.join(tmp_path, "my_aadhar_card.png"))
    assert label_front == "Aadhaar_Front"

def test_manual_initialization_on_import(tmp_path, monkeypatch):
    # Set monitored folder environment variable mock
    inbox_dir = os.path.join(tmp_path, "monitored_inbox")
    os.makedirs(inbox_dir, exist_ok=True)
    
    # Create subfolder in monitored inbox
    case_folder_name = "Amit Kumar RM"
    case_folder_path = os.path.join(inbox_dir, case_folder_name)
    os.makedirs(case_folder_path, exist_ok=True)
    
    # Place a file inside it
    file_path = os.path.join(case_folder_path, "pan_card.jpg")
    with open(file_path, "w") as f:
        f.write("mock data")
        
    # Monkeypatch CASE_INBOX_DIR config
    monkeypatch.setenv("CASE_INBOX_DIR", inbox_dir)
    
    # Run list_cases() to trigger auto-initialization
    # Since background thread is spawned, we'll mock start_inbox_ingestion_thread
    # to run synchronously or do nothing during testing.
    thread_called = []
    def mock_start_thread(case_id):
        thread_called.append(case_id)
        
    import services.session_manager
    monkeypatch.setattr("services.ingestion_pipeline.start_inbox_ingestion_thread", mock_start_thread)
    
    from services.session_manager import list_unimported_inbox_folders
    unimported = list_unimported_inbox_folders()
    
    assert len(unimported) == 1
    assert unimported[0]["folder_name"] == case_folder_name
    
    # Use Flask test client to post to import endpoint
    from app import app
    with app.test_client() as client:
        res = client.post("/api/inbox/import", json={
            "folder_name": unimported[0]["folder_name"],
            "case_id": unimported[0]["case_id"],
            "path": unimported[0]["path"]
        })
        assert res.status_code == 200
        assert res.json["success"] is True
    
    # Verify case session was created
    expected_case_id = "inbox_amit_kumar_rm"
    assert len(thread_called) == 1
    assert thread_called[0] == expected_case_id
    
    session_file = os.path.join(CASES_DIR, expected_case_id, "session.json")
    assert os.path.exists(session_file)
    
    with open(session_file, "r") as f:
        sess = json.load(f)
    assert sess["case_name"] == case_folder_name
    assert sess["case_inbox_path"] == case_folder_path
    assert sess["status"] == "processing"
    
    # Clean up cases
    shutil.rmtree(os.path.join(CASES_DIR, expected_case_id), ignore_errors=True)


def test_nested_subfolder_classification(tmp_path, monkeypatch):
    # Set monitored folder environment variable mock
    inbox_dir = os.path.join(tmp_path, "monitored_inbox")
    os.makedirs(inbox_dir, exist_ok=True)
    
    # Create case folder
    case_folder_path = os.path.join(inbox_dir, "test_nested_case")
    os.makedirs(case_folder_path, exist_ok=True)
    
    # Create nested subfolders
    kyc_dir = os.path.join(case_folder_path, "kyc")
    legal_dir = os.path.join(case_folder_path, "legal")
    os.makedirs(kyc_dir, exist_ok=True)
    os.makedirs(legal_dir, exist_ok=True)
    
    # Place files with generic names inside the subfolders
    with open(os.path.join(kyc_dir, "document_1.png"), "w") as f:
        f.write("kyc data")
    with open(os.path.join(legal_dir, "document_2.pdf"), "w") as f:
        f.write("legal data")
        
    from services.ingestion_pipeline import run_ingestion_pipeline
    from services.session_manager import load_case_session, save_case_session
    
    # Clean cases dir location mock for testing
    cases_dir_mock = os.path.join(tmp_path, "cases")
    os.makedirs(cases_dir_mock, exist_ok=True)
    monkeypatch.setattr("services.session_manager.CASES_DIR", cases_dir_mock)
    monkeypatch.setattr("services.ingestion_pipeline.CASES_DIR", cases_dir_mock)
    
    # Save dummy session
    case_id = "inbox_test_nested"
    save_case_session(
        case_id=case_id,
        data={},
        files=[],
        verified_fields=set(),
        bank="ICICI",
        borrower_count="1",
        loan_count="1",
        properties_count="1",
        doc_type="RM",
        status="new",
        case_inbox_path=case_folder_path
    )
    
    # Run pipeline
    run_ingestion_pipeline(case_id)
    
    # Verify session contains files and classified buckets
    sess = load_case_session(case_id)
    assert sess is not None
    assert len(sess["files"]) == 2
    assert any("document_1.png" in f for f in sess["buckets"]["kyc"])
    assert any("document_2.pdf" in f for f in sess["buckets"]["legal"])


