import pytest
import os
import shutil
from app import app, save_case_session, load_case_session, list_cases
from models.case import Case, db

def test_buckets_preservation():
    case_id = "test_buckets_case_1"
    
    with app.app_context():
        # Clean any pre-existing test data
        case = db.session.get(Case, case_id)
        if case:
            db.session.delete(case)
            db.session.commit()
            
        test_case_dir = os.path.join("cases", case_id)
        if os.path.exists(test_case_dir):
            shutil.rmtree(test_case_dir)
            
        try:
            # 1. Save case session with buckets
            test_data = {"bs": [{"n": "John Doe"}]}
            test_files = ["uploaded_doc.pdf"]
            test_verified = ["bs.0.n"]
            test_buckets = {
                "aadhaar": ["uploaded_doc.pdf"],
                "pan": []
            }
            
            save_case_session(
                case_id=case_id,
                data=test_data,
                files=test_files,
                verified_fields=test_verified,
                bank="ICICI",
                borrower_count="1",
                loan_count="1",
                buckets=test_buckets
            )
            
            # 2. Load case session and verify buckets are loaded
            sess = load_case_session(case_id)
            assert sess is not None
            assert sess["buckets"] == test_buckets
            assert sess["data"]["buckets"] == test_buckets
            
            # 3. List cases and verify buckets are populated
            cases = list_cases()
            found_case = next((c for c in cases if c["id"] == case_id), None)
            assert found_case is not None
            assert found_case["buckets"] == test_buckets
            
            # 4. Save case session with buckets=None, and verify it defaults to existing
            save_case_session(
                case_id=case_id,
                data=test_data,
                files=test_files,
                verified_fields=test_verified,
                bank="ICICI",
                borrower_count="1",
                loan_count="1",
                buckets=None
            )
            
            sess_after = load_case_session(case_id)
            assert sess_after is not None
            assert sess_after["buckets"] == test_buckets
            assert sess_after["data"]["buckets"] == test_buckets
            
        finally:
            # Cleanup
            case = db.session.get(Case, case_id)
            if case:
                db.session.delete(case)
                db.session.commit()
                
            if os.path.exists(test_case_dir):
                shutil.rmtree(test_case_dir)
