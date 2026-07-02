import os
import json
import tempfile
from models.case import Case, db
from scripts.migrate_sessions import migrate_json_to_sqlite
from flask import Flask

def test_migration():
    temp_dir = tempfile.mkdtemp()
    case_dir = os.path.join(temp_dir, "case_test123")
    os.makedirs(case_dir)
    
    session_data = {
        "id": "case_test123",
        "doc_type": "SD",
        "bank": "ICICI",
        "borrower_count": "2",
        "loan_count": "1",
        "properties_count": "1",
        "sellers_count": "1",
        "buyers_count": "1",
        "chain_scenario": "ScenarioA",
        "selected_template": "template.docx",
        "property_type": "Flat",
        "verified_fields": ["field1"],
        "processed_files": ["file1.pdf"],
        "files": ["file1.pdf"],
        "legal_report_files": ["report.pdf"],
        "data": {"name": "Test Customer"},
        "last_updated": 123456789.0
    }
    
    with open(os.path.join(case_dir, "session.json"), "w") as f:
        json.dump(session_data, f)
        
    app = Flask("test_migrate_app")
    db_path = os.path.join(temp_dir, "test.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
    migrate_json_to_sqlite(temp_dir, f"sqlite:///{db_path}")
    
    with app.app_context():
        case = db.session.get(Case, "case_test123")
        assert case is not None
        assert case.doc_type == "SD"
        assert case.bank == "ICICI"
        assert json.loads(case.data) == {"name": "Test Customer"}
        assert case.last_updated == 123456789.0
