from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import os
import json
import time
import shutil
import re
from extractor import DataExtractor
from processor import TemplateProcessor

app = Flask(__name__, template_folder="web_templates", static_folder="static")
app.secret_key = "your_secret_key_here"

# Configuration
CASES_DIR = "cases"
TEMPLATES_DIR = "templates"
DEFAULT_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDs32YIJx35FDhb9qOa3vTcWDtU-RpL5_w"
os.makedirs(CASES_DIR, exist_ok=True)

# --- Template Discovery (from old app.py) ---
def discover_templates():
    template_map = {}
    bank_folders = []

    if not os.path.exists(TEMPLATES_DIR):
        return {}, []

    for item in os.listdir(TEMPLATES_DIR):
        bank_dir = os.path.join(TEMPLATES_DIR, item)
        if not os.path.isdir(bank_dir):
            continue

        bank_name = item.upper()
        bank_folders.append(bank_name)
        template_map[bank_name] = {}

        for fname in os.listdir(bank_dir):
            if not fname.lower().endswith(".docx"):
                continue
            # Parse: RM_{BANK}_{#B}B_{#L}L_anything.docx
            m = re.match(r"RM_" + re.escape(bank_name) + r"_(\\d+)B_(\\d+)L", fname, re.IGNORECASE)
            if m:
                b_count = m.group(1)   # "1", "2", "3" etc.
                l_count = m.group(2)   # "1", "2", "3" etc.
                if b_count not in template_map[bank_name]:
                    template_map[bank_name][b_count] = {}
                template_map[bank_name][b_count][l_count] = os.path.join(bank_dir, fname)

    bank_folders.sort()
    if "ICICI" in bank_folders:
        bank_folders.remove("ICICI")
        bank_folders.insert(0, "ICICI")
    return template_map, bank_folders

template_map, bank_folders = discover_templates()

# --- Session Management ---
def list_cases():
    cases = []
    if not os.path.exists(CASES_DIR): return []
    for d in os.listdir(CASES_DIR):
        path = os.path.join(CASES_DIR, d, "session.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as f: cases.append(json.load(f))
            except: pass
    return sorted(cases, key=lambda x: x.get("last_updated", 0), reverse=True)

def load_case_session(case_id):
    path = os.path.join(CASES_DIR, case_id, "session.json")
    if not os.path.exists(path): return None
    with open(path, "r") as f: return json.load(f)

def save_case_session(case_id, data, files, verified_fields, bank, borrower_count, loan_count):
    os.makedirs(os.path.join(CASES_DIR, case_id), exist_ok=True)
    session = {
        "id": case_id,
        "borrower_name": data.get("bs", [{}])[0].get("n", "New Case") if data.get("bs") else "New Case",
        "bank": bank,
        "borrower_count": borrower_count,
        "loan_count": loan_count,
        "last_updated": time.time(),
        "data": data,
        "verified_fields": list(verified_fields),
        "files": files,
        "watch_folder": None # Not applicable for web
    }
    path = os.path.join(CASES_DIR, case_id, "session.json")
    with open(path, "w") as f: json.dump(session, f)

# --- Routes ---
@app.route("/")
def dashboard():
    cases_data = []
    for case in list_cases():
        case["updated"] = time.strftime("%d %b, %H:%M", time.localtime(case.get("last_updated", 0)))
        cases_data.append(case)
    return render_template("dashboard.html", cases=cases_data)

@app.route("/new_case")
def new_case():
    case_id = f"case_{int(time.time())}"
    # Create an empty session
    save_case_session(case_id, {}, [], set(), "", "", "")
    return redirect(url_for("view_case", case_id=case_id))

@app.route("/case/<case_id>")
def view_case(case_id):
    session = load_case_session(case_id)
    if not session:
        return redirect(url_for("dashboard"))

    # Prepare initial data for template
    data = session.get("data", {})
    files = session.get("files", [])
    verified_fields = set(session.get("verified_fields", []))

    selected_bank = session.get("bank", bank_folders[0] if bank_folders else "")
    selected_borrower = session.get("borrower_count", "1")
    selected_loan = session.get("loan_count", "1")

    return render_template("case.html",
                           case_id=case_id,
                           banks=bank_folders,
                           selected_bank=selected_bank,
                           selected_borrower=selected_borrower,
                           selected_loan=selected_loan,
                           data=data,
                           files=files,
                           verified_fields=list(verified_fields))

@app.route("/case/<case_id>/save", methods=["POST"])
def save_case(case_id):
    session = load_case_session(case_id)
    if not session: return jsonify({"success": False, "error": "Case not found"}), 404

    req_data = request.json
    ui_data = req_data.get("data", {})
    bank = req_data.get("bank")
    borrowers = req_data.get("borrowers")
    loans = req_data.get("loans")
    
    # Merge incoming UI data with existing data, respecting verified fields
    current_extracted_data = session.get("data", {})
    verified_fields = set(session.get("verified_fields", []))

    # Smart merge logic (from old app.py)
    def smart_merge(old, new, path=""):
        if not old: return new
        if isinstance(new, dict):
            merged = old.copy() if isinstance(old, dict) else {}
            for k, v in new.items():
                p = f"{path}.{k}" if path else k
                if p in verified_fields: continue
                merged[k] = smart_merge(merged.get(k), v, p)
            return merged
        elif isinstance(new, list):
            merged = list(old) if isinstance(old, list) else []
            while len(merged) < len(new): merged.append({})
            return [smart_merge(merged[i], item, f"{path}.{i}") for i, item in enumerate(new)]
        return new
    
    merged_data = smart_merge(current_extracted_data, ui_data) 

    session["data"] = merged_data
    session["bank"] = bank
    session["borrower_count"] = borrowers
    session["loan_count"] = loans
    session["last_updated"] = time.time()

    save_case_session(case_id, 
                      session["data"],
                      session["files"],
                      set(session["verified_fields"]),
                      session["bank"],
                      session["borrower_count"],
                      session["loan_count"])

    return jsonify({"success": True})


@app.route("/case/<case_id>/upload_files", methods=["POST"])
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
            new_file_paths.append(filepath)
            if filepath not in current_files:
                current_files.append(filepath)
    
    session["files"] = current_files
    save_case_session(case_id, 
                      session["data"],
                      session["files"],
                      set(session["verified_fields"]),
                      session["bank"],
                      session["borrower_count"],
                      session["loan_count"])

    return jsonify({"success": True, "new_files": [os.path.basename(f) for f in new_file_paths]})

@app.route("/case/<case_id>/ai", methods=["POST"])
def run_ai(case_id):
    session = load_case_session(case_id)
    if not session: return jsonify({"success": False, "error": "Case not found"}), 404

    req_data = request.json
    bank = req_data.get("bank")
    borrowers = int(req_data.get("borrowers", 1))
    loans = int(req_data.get("loans", 1))
    model = req_data.get("model")

    files_to_process = session.get("files", [])
    if not files_to_process:
        return jsonify({"success": False, "error": "No documents uploaded."}), 400

    try:
        extractor = DataExtractor(DEFAULT_GEMINI_API_KEY)
        extracted_data = extractor.extract_with_ai(
            files_to_process, model, bank_name=bank,
            expected_borrowers=borrowers, expected_loans=loans
        )

        if extracted_data.get("error"):
            return jsonify({"success": False, "error": extracted_data["error"]}), 400
        
        # Smart merge new AI data with existing data, respecting verified fields
        current_data = session.get("data", {})
        verified_fields = set(session.get("verified_fields", []))

        def smart_merge(old, new, path=""):
            if not old: return new
            if isinstance(new, dict):
                merged = old.copy() if isinstance(old, dict) else {}
                for k, v in new.items():
                    p = f"{path}.{k}" if path else k
                    if p in verified_fields: continue
                    merged[k] = smart_merge(merged.get(k), v, p)
                return merged
            elif isinstance(new, list):
                merged = list(old) if isinstance(old, list) else []
                while len(merged) < len(new): merged.append({})
                return [smart_merge(merged[i], item, f"{path}.{i}") for i, item in enumerate(new)]
            return new
        
        session["data"] = smart_merge(current_data, extracted_data)

        save_case_session(case_id, 
                          session["data"],
                          session["files"],
                          verified_fields,
                          bank,
                          borrowers,
                          loans)
        
        return jsonify({"success": True, "data": session["data"]})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/case/<case_id>/generate", methods=["POST"])
def generate_rm(case_id):
    session = load_case_session(case_id)
    if not session: return jsonify({"success": False, "error": "Case not found"}), 404

    req_data = request.json
    bank = req_data.get("bank")
    borrowers = req_data.get("borrowers")
    loans = req_data.get("loans")
    data = req_data.get("data", {})

    # Ensure the latest UI data is saved before generating
    save_case_session(case_id, 
                      data, # Use incoming data directly for generation
                      session["files"],
                      set(session["verified_fields"]),
                      bank,
                      borrowers,
                      loans)

    template_path = template_map.get(bank, {}).get(str(borrowers), {}).get(str(loans))
    if not template_path:
        return jsonify({"success": False, "error": f"No template found for {bank} - {borrowers} borrowers - {loans} loans."}), 400

    # Convert ds_text back to ds list for old template compatibility
    ds_text_val = data.get("ds_text", "")
    ds_lines = [x.strip() for x in ds_text_val.split("\n") if x.strip()]
    data["ds"] = [{"t": line} for line in ds_lines] if ds_lines else [{"t": ds_text_val}]

    output_filename = f"RM_{case_id}.docx"
    output_filepath = os.path.join(CASES_DIR, case_id, output_filename)

    try:
        processor = TemplateProcessor(template_path)
        processor.generate(data, output_filepath, highlight_ai=True, highlight_missing=True, verified_fields=set(session["verified_fields"]))
        return send_file(output_filepath, as_attachment=True, download_name=output_filename)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/delete_case/<case_id>")
def delete_case(case_id):
    case_path = os.path.join(CASES_DIR, case_id)
    if os.path.exists(case_path):
        shutil.rmtree(case_path)
    return redirect(url_for("dashboard"))

# @app.route("/static/<path:filename>")
# def static_files(filename):
#     # This is a placeholder for local development. In production, serve static files directly.
#     return send_from_directory("static", filename)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
