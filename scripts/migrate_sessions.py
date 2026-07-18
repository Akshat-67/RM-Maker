# scripts/migrate_sessions.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from flask import Flask
from models.case import Case, db

def migrate_json_to_sqlite(cases_dir, db_uri):
    app = Flask("migration_app")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        if not os.path.exists(cases_dir):
            return
            
        for d in os.listdir(cases_dir):
            path = os.path.join(cases_dir, d, "session.json")
            if not os.path.exists(path):
                continue
                
            try:
                with open(path, "r", encoding="utf-8") as f:
                    sess = json.load(f)
                
                case_id = sess.get("id") or d
                if not case_id:
                    continue
                    
                case = db.session.get(Case, case_id)
                if not case:
                    case = Case(id=case_id)
                    db.session.add(case)
                
                data_dict = sess.get("data", {})
                if "buckets" in sess:
                    data_dict["buckets"] = sess["buckets"]

                case.doc_type = sess.get("doc_type", "RM")
                case.bank = sess.get("bank")
                case.borrower_count = int(sess.get("borrower_count")) if str(sess.get("borrower_count", "")).isdigit() else 1
                case.loan_count = int(sess.get("loan_count")) if str(sess.get("loan_count", "")).isdigit() else 1
                case.properties_count = int(sess.get("properties_count")) if str(sess.get("properties_count", "")).isdigit() else 1
                case.sellers_count = int(sess.get("sellers_count")) if str(sess.get("sellers_count", "")).isdigit() else 1
                case.buyers_count = int(sess.get("buyers_count")) if str(sess.get("buyers_count", "")).isdigit() else 1
                case.chain_scenario = sess.get("chain_scenario")
                case.selected_template = sess.get("selected_template")
                case.property_type = sess.get("property_type", "Plot")
                case.verified_fields = json.dumps(sess.get("verified_fields", []))
                case.processed_files = json.dumps(sess.get("processed_files", []))
                case.files = json.dumps(sess.get("files", []))
                case.legal_report_files = json.dumps(sess.get("legal_report_files", []))
                case.data = json.dumps(data_dict)
                case.last_updated = float(sess.get("last_updated", 0.0))
            except Exception as e:
                print(f"Error migrating {path}: {e}")
                
        db.session.commit()

if __name__ == "__main__":
    db_path = os.path.abspath(os.path.join("cases", "cases.db"))
    migrate_json_to_sqlite("cases", f"sqlite:///{db_path}")
