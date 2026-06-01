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
DEFAULT_GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    "AIzaSyBKkvXn_tTX2YVK_YzQPkm7FUDtYju43hc",
    "AIzaSyAXF1GYok40JQPkzg3rv2b_CGVJjDsaze8",
    "AQ.Ab8RN6LT45vwhXCygf42E1_cCExGjyFvD95qNo1vQ37hC3ZnBQ",
    "AIzaSyDs32YIJx35FDhb9qOa3vTcWDtU-RpL5_w"
]
DEFAULT_GEMINI_API_KEYS = list(dict.fromkeys([k for k in DEFAULT_GEMINI_API_KEYS if k]))
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
            m = re.match(r"RM_" + re.escape(bank_name) + r"_(\d+)B_(\d+)L", fname, re.IGNORECASE)
            if m:
                b_count = m.group(1)   # "1", "2", "3" etc.
                l_count = m.group(2)   # "1", "2", "3" etc.
                
                # Check if it specifies two properties in the filename
                is_two_props = "two properties" in fname.lower()
                p_count = "2" if is_two_props else "1"
                
                if b_count not in template_map[bank_name]:
                    template_map[bank_name][b_count] = {}
                if l_count not in template_map[bank_name][b_count]:
                    template_map[bank_name][b_count][l_count] = {}
                template_map[bank_name][b_count][l_count][p_count] = os.path.join(bank_dir, fname)

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

def save_case_session(case_id, data, files, verified_fields, bank, borrower_count, loan_count, properties_count="1", processed_files=None, doc_type="RM", sellers_count="1", buyers_count="1", chain_scenario=""):
    os.makedirs(os.path.join(CASES_DIR, case_id), exist_ok=True)
    
    if doc_type == "SD":
        sellers_list = data.get("sellers", [{}])
        buyer_name = data.get("buyers", [{}])[0].get("n", "New Case") if data.get("buyers") else "New Case"
        display_name = f"SD: {sellers_list[0].get('n', 'New Case')} -> {buyer_name}" if sellers_list else "New Sale Deed"
    else:
        display_name = data.get("bs", [{}])[0].get("n", "New Case") if data.get("bs") else "New Case"

    session = {
        "id": case_id,
        "borrower_name": display_name,
        "bank": bank,
        "borrower_count": borrower_count,
        "loan_count": loan_count,
        "properties_count": properties_count or "1",
        "last_updated": time.time(),
        "data": data,
        "verified_fields": list(verified_fields),
        "files": files,
        "processed_files": processed_files or [],
        "watch_folder": None, # Not applicable for web
        "doc_type": doc_type,
        "sellers_count": sellers_count or "1",
        "buyers_count": buyers_count or "1",
        "chain_scenario": chain_scenario or ""
    }
    path = os.path.join(CASES_DIR, case_id, "session.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False)

# --- Smart Merge Utility ---
def smart_merge(old, new, verified_fields, path=""):
    # If old is empty/falsy, take the new value (even if new is empty, this is correct for initialization)
    if not old:
        return new
        
    if isinstance(new, dict):
        merged = old.copy() if isinstance(old, dict) else {}
        for k, v in new.items():
            p = f"{path}.{k}" if path else k
            if p in verified_fields:
                continue
            merged[k] = smart_merge(merged.get(k), v, verified_fields, p)
        return merged
        
    elif isinstance(new, list):
        merged = list(old) if isinstance(old, list) else []
        
        # If it is one of our entity lists: 'ls' (loans), 'ps' (properties), or 'unassigned_aadhars'
        # We merge them by unique keys rather than index to prevent overwriting during incremental scans
        if path in ["ls", "ps", "unassigned_aadhars", "data.ls", "data.ps", "data.unassigned_aadhars"]:
            key_field = "n" if "ls" in path else ("id" if "unassigned" in path else "adr")
            
            # Start with existing items that actually contain values
            existing_entities = [item for item in merged if isinstance(item, dict) and any(item.values())]
            
            # Map existing entities by their unique normalized key
            existing_by_key = {}
            for item in existing_entities:
                val = str(item.get(key_field, "")).strip().casefold()
                if val:
                    existing_by_key[val] = item
                    
            for new_item in new:
                if not isinstance(new_item, dict) or not any(new_item.values()):
                    continue
                new_val = str(new_item.get(key_field, "")).strip().casefold()
                
                if new_val and new_val in existing_by_key:
                    # Key match found: merge recursively
                    merged_item = smart_merge(existing_by_key[new_val], new_item, verified_fields, f"{path}.MATCH")
                    idx = existing_entities.index(existing_by_key[new_val])
                    existing_entities[idx] = merged_item
                else:
                    # New unique key: append to active entities list
                    existing_entities.append(new_item)
                    
            return existing_entities
            
        # Standard merge by index for other lists (like 'bs', 'ws' where count is fixed)
        while len(merged) < len(new):
            merged.append({})
        
        result = []
        for i in range(max(len(merged), len(new))):
            old_item = merged[i] if i < len(merged) else None
            new_item = new[i] if i < len(new) else None
            result.append(smart_merge(old_item, new_item, verified_fields, f"{path}.{i}"))
        return result
        
    # For primitive values (strings, numbers, etc.)
    if new == "" or new is None:
        return old  # Keep old value if new is empty
    return new

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
    import datetime
    today_str = datetime.date.today().strftime("%d.%m.%Y")
    # Create a session with today's date initialized in rd
    save_case_session(case_id, {"rd": today_str}, [], set(), "", "", "")
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

    # Toggles between RM (Registered Mortgage) and SD (Sale Deed)
    doc_type = session.get("doc_type", "RM")
    selected_sellers = str(session.get("sellers_count") or "1")
    selected_buyers = str(session.get("buyers_count") or "1")
    selected_scenario = session.get("chain_scenario", "")

    selected_bank = session.get("bank", bank_folders[0] if bank_folders else "")
    if not selected_bank and bank_folders:
        selected_bank = bank_folders[0]

    selected_borrower = str(session.get("borrower_count") or "1")
    if not selected_borrower or selected_borrower == "None":
        selected_borrower = "1"

    selected_loan = str(session.get("loan_count") or "1")
    if not selected_loan or selected_loan == "None":
        selected_loan = "1"

    selected_properties = str(session.get("properties_count") or "1")
    if not selected_properties or selected_properties == "None":
        selected_properties = "1"

    if doc_type == "SD":
        # Force counts and padding of Hindi entity arrays for Sale Deed
        if "sellers" not in data or not isinstance(data["sellers"], list):
            data["sellers"] = []
        try: s_num = int(selected_sellers)
        except: s_num = 1
        data["sellers"] = data["sellers"][:s_num]
        while len(data["sellers"]) < s_num:
            data["sellers"].append({})

        if "buyers" not in data or not isinstance(data["buyers"], list):
            data["buyers"] = []
        try: by_num = int(selected_buyers)
        except: by_num = 1
        data["buyers"] = data["buyers"][:by_num]
        while len(data["buyers"]) < by_num:
            data["buyers"].append({})

        if "ps" not in data or not isinstance(data["ps"], list):
            data["ps"] = []
        data["ps"] = data["ps"][:1] # Typically 1 property for Sale Deed
        while len(data["ps"]) < 1:
            data["ps"].append({})

        if "ws" not in data or not isinstance(data["ws"], list):
            data["ws"] = []
        data["ws"] = data["ws"][:2] # 2 witnesses
        while len(data["ws"]) < 2:
            data["ws"].append({})

        if "chain" not in data or not isinstance(data["chain"], list):
            data["chain"] = []
        # Pad to 3 chain entries
        while len(data["chain"]) < 3:
            data["chain"].append({})
    else:
        # Force counts and padding of entity arrays inside data to align with dropdown choices
        if "bs" not in data or not isinstance(data["bs"], list):
            data["bs"] = []
        try: b_num = int(selected_borrower)
        except: b_num = 1
        data["bs"] = data["bs"][:b_num]
        while len(data["bs"]) < b_num:
            data["bs"].append({})

        if "ls" not in data or not isinstance(data["ls"], list):
            data["ls"] = []
        try: l_num = int(selected_loan)
        except: l_num = 1
        data["ls"] = data["ls"][:l_num]
        while len(data["ls"]) < l_num:
            data["ls"].append({})

        if "ps" not in data or not isinstance(data["ps"], list):
            data["ps"] = []
        try: p_num = int(selected_properties)
        except: p_num = 1
        data["ps"] = data["ps"][:p_num]
        while len(data["ps"]) < p_num:
            data["ps"].append({})

        if "ws" not in data or not isinstance(data["ws"], list):
            data["ws"] = []
        data["ws"] = data["ws"][:2]
        while len(data["ws"]) < 2:
            data["ws"].append({})

    return render_template("case.html",
                           case_id=case_id,
                           doc_type=doc_type,
                           selected_sellers=selected_sellers,
                           selected_buyers=selected_buyers,
                           selected_scenario=selected_scenario,
                           banks=bank_folders,
                           selected_bank=selected_bank,
                           selected_borrower=selected_borrower,
                           selected_loan=selected_loan,
                           selected_properties=selected_properties,
                           data=data,
                           files=files,
                           verified_fields=list(verified_fields))

@app.route("/get_models")
def get_models():
    try:
        extractor = DataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS, provider="gemini")
        models = extractor.get_available_models()
        return jsonify({"success": True, "models": models, "provider": "gemini"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/get_provider")
def get_provider():
    return jsonify({"provider": "gemini", "nim_key_set": False})

@app.route("/set_provider", methods=["POST"])
def set_provider():
    return jsonify({"success": True, "provider": "gemini"})

@app.route("/get_template_info")
def get_template_info():
    bank = request.args.get("bank")
    borrowers = request.args.get("borrowers")
    loans = request.args.get("loans")
    properties = request.args.get("properties", "1")
    
    sub_map = template_map.get(bank, {}).get(str(borrowers), {}).get(str(loans))
    if isinstance(sub_map, dict):
        template_path = sub_map.get(str(properties)) or sub_map.get("1")
    else:
        template_path = sub_map
        
    if template_path:
        return jsonify({"success": True, "filename": os.path.basename(template_path)})
    return jsonify({"success": False, "error": "No template found"})

@app.route("/case/<case_id>/save", methods=["POST"])
def save_case(case_id):
    session = load_case_session(case_id)
    if not session: return jsonify({"success": False, "error": "Case not found"}), 404

    req_data = request.json
    ui_data = req_data.get("data", {})
    doc_type = req_data.get("doc_type", "RM")
    
    bank = req_data.get("bank")
    borrowers = req_data.get("borrowers")
    loans = req_data.get("loans")
    properties = req_data.get("properties", "1")
    
    sellers_count = req_data.get("sellers_count", "1")
    buyers_count = req_data.get("buyers_count", "1")
    chain_scenario = req_data.get("chain_scenario", "")
    
    verified_fields = set(req_data.get("verified_fields", []))
    
    # Overwrite session data directly with user's manual UI choice,
    # but preserve unassigned_aadhars so they are not lost.
    current_extracted_data = session.get("data", {})
    merged_data = ui_data.copy()
    if "unassigned_aadhars" in current_extracted_data:
        merged_data["unassigned_aadhars"] = current_extracted_data["unassigned_aadhars"]

    session["data"] = merged_data
    session["bank"] = bank
    session["borrower_count"] = borrowers
    session["loan_count"] = loans
    session["properties_count"] = properties
    
    session["doc_type"] = doc_type
    session["sellers_count"] = sellers_count
    session["buyers_count"] = buyers_count
    session["chain_scenario"] = chain_scenario
    
    session["verified_fields"] = list(verified_fields)
    session["last_updated"] = time.time()

    save_case_session(case_id, 
                      session["data"],
                      session["files"],
                      set(session["verified_fields"]),
                      session["bank"],
                      session["borrower_count"],
                      session["loan_count"],
                      session["properties_count"],
                      session.get("processed_files", []),
                      doc_type=doc_type,
                      sellers_count=sellers_count,
                      buyers_count=buyers_count,
                      chain_scenario=chain_scenario)

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
                      session.get("processed_files", []))

    return jsonify({"success": True, "new_files": [os.path.basename(f) for f in new_file_paths]})

@app.route("/case/<case_id>/ai", methods=["POST"])
def run_ai(case_id):
    session = load_case_session(case_id)
    if not session: return jsonify({"success": False, "error": "Case not found"}), 404

    req_data = request.json
    doc_type = req_data.get("doc_type", "RM")
    
    bank = req_data.get("bank")
    borrowers = int(req_data.get("borrowers", 1))
    loans = int(req_data.get("loans", 1))
    properties = req_data.get("properties", "1")
    
    sellers_count = int(req_data.get("sellers_count", 1))
    buyers_count = int(req_data.get("buyers_count", 1))
    chain_scenario = req_data.get("chain_scenario", "")
    
    model = req_data.get("model")

    all_files = session.get("files", [])
    processed_files = session.get("processed_files", [])
    files_to_process = [f for f in all_files if f not in processed_files]

    if not files_to_process:
        if all_files:
            files_to_process = all_files
        else:
            return jsonify({"success": False, "error": "No new documents to process. Please upload a document first."}), 400

    try:
        current_data = session.get("data", {})
        verified_fields = set(session.get("verified_fields", []))

        # Instantiate extractor
        extractor = DataExtractor(
            api_keys=DEFAULT_GEMINI_API_KEYS,
            provider="gemini"
        )

        if doc_type == "SD":
            seller_hints = ", ".join([s.get("n", "") for s in current_data.get("sellers", []) if s.get("n")])
            buyer_hints = ", ".join([b.get("n", "") for b in current_data.get("buyers", []) if b.get("n")])
            witness_hints = ", ".join([w.get("n", "") for w in current_data.get("ws", []) if w.get("n")])
            
            extracted_data = extractor.extract_with_ai(
                files_to_process, model, doc_type="SD",
                expected_sellers=sellers_count, expected_buyers=buyers_count,
                expected_witnesses=2, seller_hints=seller_hints, buyer_hints=buyer_hints,
                witness_hints=witness_hints, current_data=current_data
            )
        else:
            borrower_hints = ", ".join([b.get("n", "") for b in current_data.get("bs", []) if b.get("n")])
            witness_hints = ", ".join([w.get("n", "") for w in current_data.get("ws", []) if w.get("n")])
            
            extracted_data = extractor.extract_with_ai(
                files_to_process, model, bank_name=bank,
                expected_borrowers=borrowers, expected_loans=loans,
                borrower_hints=borrower_hints, witness_hints=witness_hints,
                current_data=current_data
            )

        if extracted_data.get("error"):
            return jsonify({"success": False, "error": extracted_data["error"]}), 400

        session["data"] = smart_merge(current_data, extracted_data, verified_fields)
        
        # Mark files as processed only after successful AI run
        for f in files_to_process:
            if f not in processed_files:
                processed_files.append(f)
        session["processed_files"] = processed_files

        save_case_session(case_id, 
                          session["data"],
                          session["files"],
                          verified_fields,
                          bank,
                          borrowers,
                          loans,
                          properties,
                          session["processed_files"],
                          doc_type=doc_type,
                          sellers_count=sellers_count,
                          buyers_count=buyers_count,
                          chain_scenario=chain_scenario)
        
        return jsonify({"success": True, "data": session["data"]})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/case/<case_id>/generate", methods=["POST"])
def generate_rm(case_id):
    session = load_case_session(case_id)
    if not session: return jsonify({"success": False, "error": "Case not found"}), 404

    req_data = request.json
    doc_type = req_data.get("doc_type", "RM")
    
    bank = req_data.get("bank")
    borrowers = req_data.get("borrowers")
    loans = req_data.get("loans")
    properties = req_data.get("properties", "1")
    
    sellers_count = req_data.get("sellers_count", "1")
    buyers_count = req_data.get("buyers_count", "1")
    chain_scenario = req_data.get("chain_scenario", "")
    
    data = req_data.get("data", {})

    verified_fields = set(req_data.get("verified_fields", session.get("verified_fields", [])))

    # Ensure the latest UI data is saved before generating
    save_case_session(case_id, 
                      data, # Use incoming data directly for generation
                      session["files"],
                      verified_fields,
                      bank,
                      borrowers,
                      loans,
                      properties,
                      session.get("processed_files", []),
                      doc_type=doc_type,
                      sellers_count=sellers_count,
                      buyers_count=buyers_count,
                      chain_scenario=chain_scenario)

    if doc_type == "SD":
        # Resolve Sale Deed template
        san_scenario = re.sub(r'[^\w\-]', '_', chain_scenario or "JDA_2SD_Flat")
        template_filename = f"SD_{san_scenario}_{sellers_count}S_{buyers_count}B.docx"
        template_path = os.path.join(TEMPLATES_DIR, "SALE_DEED", template_filename)
        
        # Fallbacks
        if not os.path.exists(template_path):
            template_path = os.path.join(TEMPLATES_DIR, "SALE_DEED", f"SD_JDA_2SD_Flat_{sellers_count}S_{buyers_count}B.docx")
        if not os.path.exists(template_path):
            template_path = os.path.join(TEMPLATES_DIR, "SALE_DEED", "SD_JDA_2SD_Flat_2S_1B.docx")
    else:
        # Resolve RM template
        sub_map = template_map.get(bank, {}).get(str(borrowers), {}).get(str(loans))
        if isinstance(sub_map, dict):
            template_path = sub_map.get(str(properties)) or sub_map.get("1")
        else:
            template_path = sub_map

    if not template_path or not os.path.exists(template_path):
        return jsonify({"success": False, "error": "No valid template found."}), 400

    # Map the second_schedule string into the ds list for the templates.
    import re
    sec_sched_val = data.get("second_schedule", "")
    sec_sched_val = re.sub(r'(?<=\S)\s+(Original\b|Certified Copy\b)', r'\n\1', sec_sched_val, flags=re.IGNORECASE)
    sec_lines = [x.strip() for x in sec_sched_val.split("\n") if x.strip()]
    ds_list = [{"t": line} for line in sec_lines]
    
    while len(ds_list) < 10:
        ds_list.append({"t": ""})
    data["ds"] = ds_list

    # Ensure all required lists exist to prevent Jinja2 errors, and pad them to prevent out-of-bounds [MISSING]
    from collections import defaultdict
    for key in ["bs", "ls", "ps", "ws", "sellers", "buyers", "chain"]:
        if key not in data or not isinstance(data[key], list):
            data[key] = []
        while len(data[key]) < 10:
            data[key].append(defaultdict(str))

    # Provide 'd' as an alias for the entire data object. 
    context = data.copy()
    context['d'] = data 

    output_filename = f"{doc_type}_{case_id}.docx"
    output_filepath = os.path.join(CASES_DIR, case_id, output_filename)

    try:
        processor = TemplateProcessor(template_path)
        processor.generate(context, output_filepath, highlight_ai=True, highlight_missing=True, verified_fields=verified_fields)
        return send_file(output_filepath, as_attachment=True, download_name=output_filename)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/case/<case_id>/remove_unassigned_aadhar", methods=["POST"])
def remove_unassigned_aadhar(case_id):
    session = load_case_session(case_id)
    if not session:
        return jsonify({"success": False, "error": "Case not found"}), 404
        
    try:
        index = int(request.args.get("index", -1))
        data = session.get("data", {})
        unassigned = data.get("unassigned_aadhars", [])
        
        if 0 <= index < len(unassigned):
            unassigned.pop(index)
            data["unassigned_aadhars"] = unassigned
            
            # Save the updated session
            save_case_session(case_id, 
                              data, 
                              session["files"], 
                              set(session["verified_fields"]), 
                              session["bank"], 
                              session["borrower_count"], 
                              session["loan_count"], 
                              session.get("properties_count", "1"),
                              session.get("processed_files", []))
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Invalid index"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/case/<case_id>/remove_unassigned_aadhars", methods=["POST"])
def remove_unassigned_aadhars(case_id):
    session = load_case_session(case_id)
    if not session:
        return jsonify({"success": False, "error": "Case not found"}), 404
        
    try:
        req_data = request.json or {}
        indices = req_data.get("indices", [])
        
        data = session.get("data", {})
        unassigned = data.get("unassigned_aadhars", [])
        
        # Sort indices in descending order to avoid list-index shifting during pops
        sorted_indices = sorted([int(i) for i in indices], reverse=True)
        
        removed_count = 0
        for index in sorted_indices:
            if 0 <= index < len(unassigned):
                unassigned.pop(index)
                removed_count += 1
                
        data["unassigned_aadhars"] = unassigned
        
        save_case_session(case_id, 
                          data, 
                          session["files"], 
                          set(session["verified_fields"]), 
                          session["bank"], 
                          session["borrower_count"], 
                          session["loan_count"], 
                          session.get("properties_count", "1"),
                          session.get("processed_files", []))
        return jsonify({"success": True, "removed": removed_count})
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

@app.route("/transliterate", methods=["POST"])
def transliterate_text():
    try:
        req_data = request.json or {}
        text = req_data.get("text", "").strip()
        if not text:
            return jsonify({"success": True, "result": ""})

        hindi_result = _google_input_tools_transliterate(text)
        if hindi_result:
            return jsonify({"success": True, "result": hindi_result})

        # Fallback: Gemini API (if quota available)
        try:
            extractor = DataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS, provider="gemini")
            prompt = f"Transliterate the following English legal name or address into standard, clean Devanagari Hindi script. Return ONLY the transliterated Hindi text, absolutely no surrounding text or formatting: '{text}'"
            gemini_result = extractor.raw_generate(prompt, "gemini-2.0-flash-lite")
            if gemini_result:
                return jsonify({"success": True, "result": gemini_result.strip()})
        except Exception:
            pass

        return jsonify({"success": False, "error": "Transliteration failed — all methods exhausted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def _google_input_tools_transliterate(text):
    """
    Uses Google Input Tools API (free, no key) to phonetically transliterate
    English → Devanagari Hindi, word by word.
    Same engine as Google's Hindi keyboard / Input Tools Chrome extension.
    """
    import urllib.request
    import urllib.parse
    import json as _json

    words = text.strip().split()
    hindi_words = []
    for word in words:
        encoded = urllib.parse.quote(word)
        url = (
            f"https://inputtools.google.com/request"
            f"?text={encoded}&itc=hi-t-i0-und&num=1&cp=0&cs=1&ie=utf-8&oe=utf-8"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = _json.loads(resp.read().decode("utf-8"))
            # Response: ["SUCCESS", [["word", ["suggestion1", ...], ...]]]
            if data and data[0] == "SUCCESS" and len(data) > 1:
                suggestions = data[1]
                if suggestions and len(suggestions[0]) > 1 and suggestions[0][1]:
                    hindi_words.append(suggestions[0][1][0])
                else:
                    hindi_words.append(word)  # keep original if no suggestion
            else:
                hindi_words.append(word)
        except Exception as e:
            print(f"[InputTools] Failed for word '{word}': {e}")
            hindi_words.append(word)

    result = " ".join(hindi_words)
    # Return None if nothing actually got transliterated
    if result == text:
        return None
    return result



if __name__ == "__main__":
    app.run(debug=True, port=5000)
