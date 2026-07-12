from flask import Blueprint, request, jsonify, send_from_directory
import os
import time
from werkzeug.utils import secure_filename
from services.session_manager import load_case_session, save_case_session, CASES_DIR
from services.file_service import resolve_case_file_path

upload_bp = Blueprint('upload', __name__)

@upload_bp.route("/case/<case_id>/upload_custom_template", methods=["POST"])
def upload_custom_template(case_id):
    session = load_case_session(case_id)
    if not session:
        return jsonify({"success": False, "error": "Case not found"}), 404

    if "template" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["template"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "Invalid file"}), 400

    if not file.filename.lower().endswith(".docx"):
        return jsonify({"success": False, "error": "Only .docx files are allowed as templates"}), 400

    custom_dir = os.path.join(CASES_DIR, case_id, "custom_templates")
    os.makedirs(custom_dir, exist_ok=True)
    
    filename = secure_filename(file.filename)
    if not filename:
        filename = "custom_template.docx"
        
    filepath = os.path.join(custom_dir, filename)
    file.save(filepath)

    session["selected_template"] = filename
    save_case_session(case_id, 
                      session["data"],
                      session["files"],
                      set(session["verified_fields"]),
                      session.get("bank", ""),
                      session.get("borrower_count", "1"),
                      session.get("loan_count", "1"),
                      session.get("properties_count", "1"),
                      session.get("processed_files", []),
                      doc_type=session.get("doc_type", "RM"),
                      sellers_count=session.get("sellers_count", "1"),
                      buyers_count=session.get("buyers_count", "1"),
                      chain_scenario=session.get("chain_scenario", ""),
                      selected_template=filename,
                      property_type=session.get("property_type", "Plot"),
                      legal_report_files=session.get("legal_report_files", []))

    return jsonify({"success": True, "filename": filename})

@upload_bp.route("/case/<case_id>/clear_custom_template", methods=["POST"])
def clear_custom_template(case_id):
    session = load_case_session(case_id)
    if not session:
        return jsonify({"success": False, "error": "Case not found"}), 404

    session["selected_template"] = ""
    save_case_session(case_id, 
                      session["data"],
                      session["files"],
                      set(session["verified_fields"]),
                      session.get("bank", ""),
                      session.get("borrower_count", "1"),
                      session.get("loan_count", "1"),
                      session.get("properties_count", "1"),
                      session.get("processed_files", []),
                      doc_type=session.get("doc_type", "RM"),
                      sellers_count=session.get("sellers_count", "1"),
                      buyers_count=session.get("buyers_count", "1"),
                      chain_scenario=session.get("chain_scenario", ""),
                      selected_template="",
                      property_type=session.get("property_type", "Plot"),
                      legal_report_files=session.get("legal_report_files", []))

    return jsonify({"success": True})

@upload_bp.route("/case/<case_id>/upload_files", methods=["POST"])
def upload_files(case_id):
    session = load_case_session(case_id)
    if not session: return jsonify({"success": False, "error": "Case not found"}), 404

    uploaded_files = request.files.getlist("files")
    case_files_dir = os.path.join(CASES_DIR, case_id, "files")
    os.makedirs(case_files_dir, exist_ok=True)

    current_files = session.get("files", [])
    new_file_paths = []

    for file in uploaded_files:
        if file.filename:
            filepath = os.path.join(case_files_dir, file.filename)
            file.save(filepath)
            if filepath not in current_files:
                current_files.append(filepath)
                new_file_paths.append(filepath)
    
    session["files"] = current_files
    save_case_session(case_id, 
                      session["data"],
                      session["files"],
                      set(session["verified_fields"]),
                      session["bank"],
                      session["borrower_count"],
                      session["loan_count"],
                      session.get("properties_count", "1"),
                      session.get("processed_files", []),
                      doc_type=session.get("doc_type"),
                      sellers_count=session.get("sellers_count"),
                      buyers_count=session.get("buyers_count"),
                      chain_scenario=session.get("chain_scenario"),
                      selected_template=session.get("selected_template"),
                      property_type=session.get("property_type"),
                      legal_report_files=session.get("legal_report_files", []))

    return jsonify({"success": True, "new_files": [os.path.basename(f) for f in new_file_paths]})

@upload_bp.route("/case/<case_id>/upload_bucket/<bucket_name>", methods=["POST"])
def upload_bucket(case_id, bucket_name):
    session = load_case_session(case_id)
    if not session:
        session = {
            "data": {}, "files": [], "verified_fields": [], "doc_type": "SD",
            "sellers_count": "1", "buyers_count": "1", "properties_count": "1"
        }

    uploaded_files = request.files.getlist("files")
    case_bucket_dir = os.path.join(CASES_DIR, case_id, "buckets", bucket_name)
    os.makedirs(case_bucket_dir, exist_ok=True)

    buckets = session.get("buckets", {})
    current_files = buckets.get(bucket_name, [])
    new_file_paths = []

    for file in uploaded_files:
        if file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(case_bucket_dir, filename)
            file.save(filepath)
            if filepath not in current_files:
                current_files.append(filepath)
                new_file_paths.append(filepath)

    buckets[bucket_name] = current_files

    save_case_session(case_id,
                      session.get("data", {}),
                      session.get("files", []),
                      set(session.get("verified_fields", [])),
                      session.get("bank"),
                      session.get("borrower_count"),
                      session.get("loan_count"),
                      session.get("properties_count", "1"),
                      session.get("processed_files", []),
                      doc_type=session.get("doc_type", "SD"),
                      sellers_count=session.get("sellers_count", "1"),
                      buyers_count=session.get("buyers_count", "1"),
                      chain_scenario=session.get("chain_scenario", ""),
                      selected_template=session.get("selected_template", ""),
                      property_type=session.get("property_type", "Plot"),
                      legal_report_files=session.get("legal_report_files", []),
                      buckets=buckets)

    return jsonify({"success": True, "new_files": [os.path.basename(f) for f in new_file_paths]})

@upload_bp.route("/case/<case_id>/upload_legal_report", methods=["POST"])
def upload_legal_report(case_id):
    session = load_case_session(case_id)
    if not session: return jsonify({"success": False, "error": "Case not found"}), 404

    uploaded_files = request.files.getlist("files")
    case_files_dir = os.path.join(CASES_DIR, case_id, "legal_reports")
    os.makedirs(case_files_dir, exist_ok=True)

    current_files = session.get("legal_report_files", [])
    new_file_paths = []

    for file in uploaded_files:
        if file.filename:
            filepath = os.path.join(case_files_dir, file.filename)
            file.save(filepath)
            if filepath not in current_files:
                current_files.append(filepath)
                new_file_paths.append(filepath)
    
    session["legal_report_files"] = current_files
    save_case_session(case_id, 
                      session["data"],
                      session["files"],
                      set(session["verified_fields"]),
                      session["bank"],
                      session["borrower_count"],
                      session["loan_count"],
                      session.get("properties_count", "1"),
                      session.get("processed_files", []),
                      doc_type=session.get("doc_type"),
                      sellers_count=session.get("sellers_count"),
                      buyers_count=session.get("buyers_count"),
                      chain_scenario=session.get("chain_scenario"),
                      selected_template=session.get("selected_template"),
                      property_type=session.get("property_type"),
                      legal_report_files=session["legal_report_files"])

    return jsonify({"success": True, "new_files": [os.path.basename(f) for f in new_file_paths]})

@upload_bp.route("/case/<case_id>/file/<path:filename>")
def serve_case_file(case_id, filename):
    directory, safe_filename = resolve_case_file_path(case_id, filename)
    if directory:
        return send_from_directory(directory, safe_filename)
    return "File not found", 404

@upload_bp.route("/case/<case_id>/delete_file", methods=["POST"])
def delete_case_file(case_id):
    session = load_case_session(case_id)
    if not session:
        return jsonify({"success": False, "error": "Case not found"}), 404

    req_data = request.json or {}
    filename = req_data.get("filename")
    bucket = req_data.get("bucket")

    if not filename:
        return jsonify({"success": False, "error": "Filename is required"}), 400

    filename = os.path.basename(filename)
    success = False
    error_msg = ""

    if bucket:
        bucket_dir = os.path.join(CASES_DIR, case_id, "buckets", bucket)
        file_path = os.path.join(bucket_dir, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                success = True
            except Exception as e:
                error_msg = str(e)
        
        buckets = session.get("buckets", {})
        if bucket in buckets:
            old_list = buckets[bucket]
            new_list = [f for f in old_list if os.path.basename(f) != filename]
            buckets[bucket] = new_list
            session["buckets"] = buckets
    else:
        case_files_dir = os.path.join(CASES_DIR, case_id, "files")
        file_path = os.path.join(case_files_dir, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                success = True
            except Exception as e:
                error_msg = str(e)

        if not success:
            legal_dir = os.path.join(CASES_DIR, case_id, "legal_reports")
            file_path = os.path.join(legal_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    success = True
                except Exception as e:
                    error_msg = str(e)
                
                legal_report_files = session.get("legal_report_files", [])
                new_legal = [f for f in legal_report_files if os.path.basename(f) != filename]
                session["legal_report_files"] = new_legal

        files = session.get("files", [])
        new_files = [f for f in files if os.path.basename(f) != filename]
        session["files"] = new_files

        processed = session.get("processed_files", [])
        new_processed = [f for f in processed if os.path.basename(f) != filename]
        session["processed_files"] = new_processed

    if success:
        save_case_session(case_id,
                          session.get("data", {}),
                          session.get("files", []),
                          set(session.get("verified_fields", [])),
                          session.get("bank"),
                          session.get("borrower_count"),
                          session.get("loan_count"),
                          session.get("properties_count", "1"),
                          session.get("processed_files", []),
                          doc_type=session.get("doc_type"),
                          sellers_count=session.get("sellers_count"),
                          buyers_count=session.get("buyers_count"),
                          chain_scenario=session.get("chain_scenario"),
                          selected_template=session.get("selected_template"),
                          property_type=session.get("property_type"),
                          legal_report_files=session.get("legal_report_files", []),
                          buckets=session.get("buckets", {}))
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": error_msg or "File not found on server"})
