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
                    
                # Skip duplicate
                if db.session.get(Case, case_id):
                    continue
                
                data_dict = sess.get("data", {})
                if "buckets" in sess:
                    data_dict["buckets"] = sess["buckets"]

                case = Case(
                    id=case_id,
                    doc_type=sess.get("doc_type", "RM"),
                    bank=sess.get("bank"),
                    borrower_count=int(sess.get("borrower_count")) if str(sess.get("borrower_count", "")).isdigit() else 1,
                    loan_count=int(sess.get("loan_count")) if str(sess.get("loan_count", "")).isdigit() else 1,
                    properties_count=int(sess.get("properties_count")) if str(sess.get("properties_count", "")).isdigit() else 1,
                    sellers_count=int(sess.get("sellers_count")) if str(sess.get("sellers_count", "")).isdigit() else 1,
                    buyers_count=int(sess.get("buyers_count")) if str(sess.get("buyers_count", "")).isdigit() else 1,
                    chain_scenario=sess.get("chain_scenario"),
                    selected_template=sess.get("selected_template"),
                    property_type=sess.get("property_type", "Plot"),
                    verified_fields=json.dumps(sess.get("verified_fields", [])),
                    processed_files=json.dumps(sess.get("processed_files", [])),
                    files=json.dumps(sess.get("files", [])),
                    legal_report_files=json.dumps(sess.get("legal_report_files", [])),
                    data=json.dumps(data_dict),
                    last_updated=float(sess.get("last_updated", 0.0))
                )
                db.session.add(case)
            except Exception as e:
                print(f"Error migrating {path}: {e}")
                
        db.session.commit()

if __name__ == "__main__":
    db_path = os.path.abspath(os.path.join("cases", "cases.db"))
    migrate_json_to_sqlite("cases", f"sqlite:///{db_path}")
