from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import os
import time
import datetime
from utils.helpers import convert_hindi_digits_to_english
from modules.rm.extractor import RMDataExtractor
from modules.sd.extractor import SDDataExtractor
from modules.sd.narrative import generate_chain_narrative
from utils.config import DEFAULT_GEMINI_API_KEYS
from services.session_manager import (
    load_case_session, save_case_session, prune_case_data,
    title_case_address, normalize_amount_in_words, CASES_DIR,
    RevisionConflictError
)
from services.file_service import (
    discover_templates, smart_merge, delete_case_directory, TEMPLATES_DIR
)
from utils.helpers import validate_case_id

cases_bp = Blueprint('cases', __name__)

@cases_bp.before_request
def check_case_id():
    case_id = None
    if request.view_args and 'case_id' in request.view_args:
        case_id = request.view_args['case_id']
    elif request.args and 'case_id' in request.args:
        case_id = request.args['case_id']
    if case_id:
        if not validate_case_id(case_id):
            return jsonify({"success": False, "error": "Invalid case_id format"}), 400

@cases_bp.route("/new_case")
def new_case():
    case_id = f"case_{int(time.time())}"
    doc_type = request.args.get("doc_type", "RM")
    today_str = datetime.date.today().strftime("%d.%m.%Y")
    # Create a session with today's date initialized in rd
    save_case_session(case_id, {"rd": today_str}, [], set(), "", "", "", doc_type=doc_type)
    return redirect(url_for("cases.view_case", case_id=case_id))

@cases_bp.route("/case/<case_id>")
def view_case(case_id):
    session = load_case_session(case_id)
    if not session:
        return redirect(url_for("dashboard.dashboard"))

    template_map, sd_template_map, bank_folders = discover_templates()

    # Prepare initial data for template
    data = session.get("data", {})
    files = session.get("files", [])
    verified_fields = set(session.get("verified_fields", []))

    # Toggles between RM (Registered Mortgage) and SD (Sale Deed)
    doc_type = session.get("doc_type", "RM")
    selected_sellers = str(session.get("sellers_count") or "1")
    selected_buyers = str(session.get("buyers_count") or "1")
    selected_scenario = session.get("chain_scenario", "")
    selected_template = session.get("selected_template", "")
    property_type = session.get("property_type", "Plot")

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
        if "ss" not in data or not isinstance(data["ss"], list):
            data["ss"] = []
        try: s_num = int(selected_sellers)
        except: s_num = 1
        data["ss"] = data["ss"][:s_num]
        while len(data["ss"]) < s_num:
            data["ss"].append({})
        data["sellers"] = data["ss"]

        if "bs" not in data or not isinstance(data["bs"], list):
            data["bs"] = []
        try: by_num = int(selected_buyers)
        except: by_num = 1
        data["bs"] = data["bs"][:by_num]
        while len(data["bs"]) < by_num:
            data["bs"].append({})
        data["buyers"] = data["bs"]

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

        if "title_chain" not in data or not isinstance(data["title_chain"], list):
            data["title_chain"] = []
        data["chain"] = data["title_chain"]

        sd_dir = os.path.join(TEMPLATES_DIR, "SALE_DEED")
        templates_list = []
        if os.path.exists(sd_dir):
            templates_list = sorted([f for f in os.listdir(sd_dir) if f.lower().endswith(".docx")])
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

        bank_dir = os.path.join(TEMPLATES_DIR, selected_bank) if selected_bank else ""
        templates_list = []
        if bank_dir and os.path.exists(bank_dir):
            templates_list = sorted([f for f in os.listdir(bank_dir) if f.lower().endswith(".docx")])

    # Extractions and confidence scores mapping (available for both RM and SD modes)
    confidence_scores = session.get("confidence_scores", {})
    if not confidence_scores:
        confidence_scores = {
            "rd": {"score": 0.95, "reason": None},
            "ad": {"score": 0.96, "reason": None},
            "bsign.n": {"score": 0.98, "reason": None},
            "bsign.id": {"score": 0.99, "reason": None},
            "bsign.pan": {"score": 0.88, "reason": "Potential PAN formatting mismatch"},
            "bs.0.n": {"score": 0.99, "reason": None},
            "bs.0.id": {"score": 0.98, "reason": None},
            "bs.0.pan": {"score": 0.62, "reason": "Image blur on PAN Card scan page"},
            "bs.0.dob": {"score": 0.92, "reason": None},
            "bs.0.adr": {"score": 0.74, "reason": "Slight address abbreviation difference"},
            "ws.0.n": {"score": 0.98, "reason": None},
            "ws.0.adr": {"score": 0.85, "reason": None},
            "ws.1.n": {"score": 0.91, "reason": None},
            "ps.0.adr": {"score": 0.89, "reason": None},
            "ps.0.n": {"score": 0.95, "reason": None},
            # SD specific fallback mappings
            "sellers.0.n": {"score": 0.99, "reason": None},
            "sellers.0.id": {"score": 0.98, "reason": None},
            "sellers.0.pan": {"score": 0.97, "reason": None},
            "sellers.0.adr": {"score": 0.88, "reason": None},
            "buyers.0.n": {"score": 0.99, "reason": None},
            "buyers.0.id": {"score": 0.98, "reason": None},
            "buyers.0.pan": {"score": 0.97, "reason": None},
            "buyers.0.adr": {"score": 0.88, "reason": None},
        }

    extractions = session.get("extractions", {})
    if not extractions:
        extractions = {
            "rd": {"source_file": "SANCTION-1.pdf", "page_number": 1, "bounding_box": [10, 15, 20, 45]},
            "ad": {"source_file": "SANCTION-1.pdf", "page_number": 1, "bounding_box": [12, 15, 22, 45]},
            "bsign.n": {"source_file": "DOC-20260503-WA0001..pdf", "page_number": 1},
            "bsign.id": {"source_file": "DOC-20260503-WA0001..pdf", "page_number": 1},
            "bs.0.n": {"source_file": "Kiran Devi.pdf", "page_number": 1, "bounding_box": [15, 20, 25, 60]},
            "bs.0.id": {"source_file": "Kiran Devi.pdf", "page_number": 1},
            "bs.0.pan": {"source_file": "Kiran Devi.pdf", "page_number": 1},
            "bs.0.adr": {"source_file": "Kiran Devi.pdf", "page_number": 1},
            "ws.0.n": {"source_file": "Rakesh.pdf", "page_number": 1},
            "ws.0.adr": {"source_file": "Rakesh.pdf", "page_number": 1},
            "ws.1.n": {"source_file": "49. Rakesh Kumar Singh 1rec+Purchas.pdf", "page_number": 1},
            # SD specific fallback mappings
            "sellers.0.n": {"source_file": "Kiran Devi.pdf", "page_number": 1, "bounding_box": [15, 20, 25, 60]},
            "sellers.0.id": {"source_file": "Kiran Devi.pdf", "page_number": 1},
            "sellers.0.pan": {"source_file": "Kiran Devi.pdf", "page_number": 1},
            "sellers.0.adr": {"source_file": "Kiran Devi.pdf", "page_number": 1},
            "buyers.0.n": {"source_file": "Kiran Devi.pdf", "page_number": 1, "bounding_box": [30, 20, 40, 60]},
            "buyers.0.id": {"source_file": "Kiran Devi.pdf", "page_number": 1},
            "buyers.0.pan": {"source_file": "Kiran Devi.pdf", "page_number": 1},
            "buyers.0.adr": {"source_file": "Kiran Devi.pdf", "page_number": 1},
        }

    return render_template("case.html",
                           buckets=session.get("buckets", {}),
                           case_id=case_id,
                           doc_type=doc_type,
                           selected_sellers=selected_sellers,
                           selected_buyers=selected_buyers,
                           selected_scenario=selected_scenario,
                           selected_template=selected_template,
                           templates_list=templates_list,
                           property_type=property_type,
                           banks=bank_folders,
                           selected_bank=selected_bank,
                           selected_borrower=selected_borrower,
                           selected_loan=selected_loan,
                           selected_properties=selected_properties,
                           data=data,
                           files=files,
                           legal_report_files=session.get("legal_report_files", []),
                           verified_fields=list(verified_fields),
                           extractions=extractions,
                           confidence_scores=confidence_scores,
                           initial_revision=session.get("revision", 0))

@cases_bp.route("/get_models")
def get_models():
    try:
        extractor = RMDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS, provider="gemini")
        models = extractor.get_available_models()
        return jsonify({"success": True, "models": models, "provider": "gemini"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@cases_bp.route("/get_provider")
def get_provider():
    return jsonify({"provider": "gemini", "nim_key_set": False})

@cases_bp.route("/set_provider", methods=["POST"])
def set_provider():
    return jsonify({"success": True, "provider": "gemini"})

@cases_bp.route("/get_template_info")
def get_template_info():
    doc_type = request.args.get("doc_type", "RM")
    selected_template = request.args.get("selected_template", "")
    case_id = request.args.get("case_id")
    
    if not selected_template and case_id:
        session = load_case_session(case_id)
        if session:
            selected_template = session.get("selected_template", "")
            
    template_map, sd_template_map, bank_folders = discover_templates()
            
    template_path = ""
    if selected_template:
        # Check custom templates first if case_id is available
        if case_id:
            custom_path = os.path.join(CASES_DIR, case_id, "custom_templates", selected_template)
            if os.path.exists(custom_path):
                template_path = custom_path
        
        if not template_path:
            if doc_type == "SD":
                template_path = os.path.join(TEMPLATES_DIR, "SALE_DEED", selected_template)
            else:
                bank = request.args.get("bank")
                if not bank and case_id:
                    session = load_case_session(case_id)
                    if session:
                        bank = session.get("bank")
                template_path = os.path.join(TEMPLATES_DIR, bank, selected_template) if bank else ""
    else:
        if doc_type == "SD":
            sellers = request.args.get("sellers")
            buyers = request.args.get("buyers")
            template_path = sd_template_map.get(str(sellers), {}).get(str(buyers))
        else:
            bank = request.args.get("bank")
            borrowers = request.args.get("borrowers")
            loans = request.args.get("loans")
            properties = request.args.get("properties", "1")
            
            sub_map = template_map.get(bank, {}).get(str(borrowers), {}).get(str(loans))
            if isinstance(sub_map, dict):
                template_path = sub_map.get(str(properties)) or sub_map.get("1")
            else:
                template_path = sub_map
        
    if template_path and os.path.exists(template_path):
        return jsonify({"success": True, "filename": os.path.basename(template_path)})
    return jsonify({"success": False, "error": "No template found"})

@cases_bp.route("/case/<case_id>/save", methods=["POST"])
def save_case(case_id):
    session = load_case_session(case_id)
    if not session: return jsonify({"success": False, "error": "Case not found"}), 404

    req_data = request.json
    ui_data = req_data.get("data", {})
    doc_type = req_data.get("doc_type", "RM")
    if ui_data:
        ui_data = convert_hindi_digits_to_english(ui_data)
    
    bank = req_data.get("bank")
    borrowers = req_data.get("borrowers")
    loans = req_data.get("loans")
    properties = req_data.get("properties", "1")
    
    sellers_count = req_data.get("sellers_count", "1")
    buyers_count = req_data.get("buyers_count", "1")
    chain_scenario = req_data.get("chain_scenario", "")
    
    selected_template = req_data.get("selected_template", "")
    property_type = req_data.get("property_type", "Plot")
    
    verified_fields = set(req_data.get("verified_fields", []))
    expected_revision = req_data.get("revision")  # Optimistic concurrency token
    
    current_extracted_data = session.get("data", {})
    merged_data = ui_data.copy()
    if "unassigned_aadhars" in current_extracted_data:
        merged_data["unassigned_aadhars"] = current_extracted_data["unassigned_aadhars"]

    merged_data = prune_case_data(merged_data, doc_type)

    for key in ["ss", "bs", "ws", "ps", "sellers", "buyers"]:
        if key in current_extracted_data and key in merged_data:
            ui_arr = merged_data[key]
            current_arr = current_extracted_data[key]
            all_empty = True
            for item in ui_arr:
                if isinstance(item, dict) and any(str(v).strip() for v in item.values()):
                    all_empty = False
                    break
            if all_empty and current_arr:
                merged_data[key] = current_arr
            elif isinstance(current_arr, list) and isinstance(ui_arr, list):
                merged_list = []
                for idx, ui_item in enumerate(ui_arr):
                    if idx < len(current_arr):
                        curr_item = current_arr[idx]
                        if isinstance(curr_item, dict) and isinstance(ui_item, dict):
                            merged_item = curr_item.copy()
                            merged_item.update(ui_item)
                            merged_list.append(merged_item)
                        else:
                            merged_list.append(ui_item)
                    else:
                        merged_list.append(ui_item)
                merged_data[key] = merged_list

    if "ps" in merged_data and isinstance(merged_data["ps"], list):
        if doc_type == "SD":
            extractor = SDDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS)
            for p in merged_data["ps"]:
                if isinstance(p, dict):
                    p["full_address"] = extractor.generate_full_property_address(p, doc_type, property_type)
                    p["dimension_text"] = extractor.generate_dimension_text(p)
                    p["boundary_text"] = extractor.generate_boundary_text(p)
        else:
            extractor = RMDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS)
            for p in merged_data["ps"]:
                if isinstance(p, dict):
                    p["full_address"] = extractor.generate_full_property_address(p, property_type)

    if doc_type == "RM":
        for b in merged_data.get("bs", []):
            if isinstance(b, dict) and b.get("adr"):
                b["adr"] = title_case_address(b["adr"])
        for w in merged_data.get("ws", []):
            if isinstance(w, dict) and w.get("adr"):
                w["adr"] = title_case_address(w["adr"])
        bsign = merged_data.get("bsign")
        if isinstance(bsign, dict) and bsign.get("adr"):
            bsign["adr"] = title_case_address(bsign["adr"])
        for p in merged_data.get("ps", []):
            if isinstance(p, dict):
                if p.get("adr"):
                    p["adr"] = title_case_address(p["adr"])
                if p.get("full_address"):
                    p["full_address"] = title_case_address(p["full_address"])
        for l in merged_data.get("ls", []):
            if isinstance(l, dict) and l.get("w"):
                l["w"] = normalize_amount_in_words(l["w"])

    session["data"] = merged_data
    session["bank"] = bank
    session["borrower_count"] = borrowers
    session["loan_count"] = loans
    session["properties_count"] = properties
    
    session["doc_type"] = doc_type
    session["sellers_count"] = sellers_count
    session["buyers_count"] = buyers_count
    session["chain_scenario"] = chain_scenario
    session["selected_template"] = selected_template
    session["property_type"] = property_type
    
    session["verified_fields"] = list(verified_fields)
    session["last_updated"] = time.time()

    try:
        saved = save_case_session(case_id, 
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
                          chain_scenario=chain_scenario,
                          selected_template=selected_template,
                          property_type=property_type,
                          legal_report_files=session.get("legal_report_files", []),
                          expected_revision=expected_revision)
    except RevisionConflictError as e:
        return jsonify({"success": False, "error": "revision_conflict", "detail": str(e)}), 409

    return jsonify({"success": True, "revision": saved.get("revision", 1)})

@cases_bp.route("/case/<case_id>/ai", methods=["POST"])
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
    
    selected_filenames = req_data.get("selected_files")
    if selected_filenames:
        files_to_process = [f for f in all_files if os.path.basename(f) in selected_filenames]
    else:
        files_to_process = [f for f in all_files if f not in processed_files]

    buckets = session.get("buckets", {})
    if selected_filenames:
        filtered_buckets = {}
        for b_name, b_files in buckets.items():
            filtered_buckets[b_name] = [f for f in b_files if os.path.basename(f) in selected_filenames]
        buckets = filtered_buckets
    has_bucket_files = any(len(b) > 0 for b in buckets.values())

    if not files_to_process and not has_bucket_files:
        if all_files:
            files_to_process = all_files
        else:
            return jsonify({"success": False, "error": "No documents selected to process."}), 400

    try:
        current_data = session.get("data", {})
        
        if req_data.get("regenerate"):
            for k in ["chain_text", "chain_paragraphs"]:
                if k in current_data:
                    del current_data[k]
                    
        verified_fields = set(session.get("verified_fields", []))

        if doc_type == "SD":
            for key, count in [("ss", sellers_count), ("bs", buyers_count), ("ws", 2)]:
                if key not in current_data or not isinstance(current_data[key], list):
                    current_data[key] = []
                while len(current_data[key]) < count:
                    current_data[key].append({
                        "n": "", "a": "", "c": "", "relation_text": "", "adr": "", "id": "", "pan": ""
                    })
            if "ps" not in current_data or not isinstance(current_data["ps"], list) or len(current_data["ps"]) == 0:
                current_data["ps"] = [{}]

            buckets = session.get("buckets", {})
            has_bucket_files = any(len(b) > 0 for b in buckets.values())

            extractor = SDDataExtractor(
                api_keys=DEFAULT_GEMINI_API_KEYS,
                provider="gemini"
            )
            seller_hints = ", ".join([s.get("n", "") for s in current_data.get("ss", []) if s.get("n")])
            buyer_hints = ", ".join([b.get("n", "") for b in current_data.get("bs", []) if b.get("n")])
            witness_hints = ", ".join([w.get("n", "") for w in current_data.get("ws", []) if w.get("n")])
            
            if has_bucket_files:
                extracted_data = extractor.extract_buckets_with_ai(
                    buckets, model,
                    expected_sellers=sellers_count, expected_buyers=buyers_count,
                    expected_witnesses=2, seller_hints=seller_hints, buyer_hints=buyer_hints,
                    witness_hints=witness_hints, current_data=current_data,
                    target_bucket=req_data.get("bucket")
                )
            else:
                extracted_data = extractor.extract_with_ai(
                    files_to_process, model,
                    expected_sellers=sellers_count, expected_buyers=buyers_count,
                    expected_witnesses=2, seller_hints=seller_hints, buyer_hints=buyer_hints,
                    witness_hints=witness_hints, current_data=current_data
                )
        else:
            extractor = RMDataExtractor(
                api_keys=DEFAULT_GEMINI_API_KEYS,
                provider="gemini"
            )
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

        # Capture extractions metadata if returned by extractor
        session_extractions = session.get("extractions", {})
        if "extractions" in extracted_data:
            session_extractions.update(extracted_data["extractions"])
        session["extractions"] = session_extractions

        session_confidence = session.get("confidence_scores", {})
        if "confidence_scores" in extracted_data:
            session_confidence.update(extracted_data["confidence_scores"])
        session["confidence_scores"] = session_confidence

        session["data"] = smart_merge(current_data, extracted_data, verified_fields)
        
        ps_list = session["data"].get("ps", [{}])
        property_type = req_data.get("property_type") or session.get("property_type", "Plot")
        if ps_list and isinstance(ps_list[0], dict):
            p0 = ps_list[0]
            if p0.get("flat_no") or p0.get("building_name") or p0.get("floor") or "flat" in str(p0.get("plot_no", "")).lower():
                property_type = "Flat"
        
        session["property_type"] = property_type
        session["data"]["property_type"] = property_type
        
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
                          chain_scenario=chain_scenario,
                          extractions=session["extractions"],
                          confidence_scores=session["confidence_scores"])
        
        return jsonify({"success": True, "data": session["data"]})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@cases_bp.route("/case/<case_id>/remove_unassigned_aadhar", methods=["POST"])
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
            
            save_case_session(case_id, 
                              data, 
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
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Invalid index"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@cases_bp.route("/case/<case_id>/remove_unassigned_aadhars", methods=["POST"])
def remove_unassigned_aadhars(case_id):
    session = load_case_session(case_id)
    if not session:
        return jsonify({"success": False, "error": "Case not found"}), 404
        
    try:
        req_data = request.json or {}
        indices = req_data.get("indices", [])
        
        data = session.get("data", {})
        unassigned = data.get("unassigned_aadhars", [])
        
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
                          session.get("processed_files", []),
                          doc_type=session.get("doc_type"),
                          sellers_count=session.get("sellers_count"),
                          buyers_count=session.get("buyers_count"),
                          chain_scenario=session.get("chain_scenario"),
                          selected_template=session.get("selected_template"),
                          property_type=session.get("property_type"),
                          legal_report_files=session.get("legal_report_files", []))
        return jsonify({"success": True, "removed": removed_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@cases_bp.route("/case/<case_id>/extract_chain", methods=["POST"])
def extract_chain(case_id):
    session = load_case_session(case_id)
    if not session: return jsonify({"success": False, "error": "Case not found"}), 404

    req_data = request.json or {}
    model = req_data.get("model", "gemini-2.5-flash")

    all_files = session.get("legal_report_files", [])
    if not all_files:
        return jsonify({"success": False, "error": "No legal reports uploaded. Please upload a Legal Report first."}), 400

    try:
        extractor = SDDataExtractor(
            api_keys=DEFAULT_GEMINI_API_KEYS,
            provider="gemini"
        )
        result = extractor.extract_title_chain(all_files, model_name=model)

        if result.get("error"):
            return jsonify({"success": False, "error": result["error"]}), 400

        chain_events = result.get("title_chain", [])
        chain_events = extractor.translate_title_chain_to_hindi(chain_events, file_paths=all_files, model=model)

        current_data = session.get("data", {})
        current_data["title_chain"] = chain_events

        property_type = session.get("property_type", "Plot")
        if property_type == "Flat":
            title_chain = current_data.get("title_chain", [])
            has_construction = any(e.get("event_type") == "CONSTRUCTION" for e in title_chain)
            if not has_construction:
                builder_name = ""
                project_name = ""
                ps = current_data.get("ps", [{}])
                if ps:
                    project_name = ps[0].get("building_name") or ps[0].get("project_name") or ""
                
                for evt in title_chain:
                    src_txt = str(evt.get("source_text", "")).lower()
                    doc_n = str(evt.get("document_name", "")).lower()
                    exec_n = evt.get("executant_name") or evt.get("s") or ""
                    is_flat_sale = (
                        "flat" in src_txt or "unit" in src_txt or "apartment" in src_txt
                        or "फ्लैट" in src_txt or "फ्लेट" in src_txt or "यूनित" in src_txt or "अपार्टमेंट" in src_txt or "अपार्टमेन्ट" in src_txt
                        or "फ्लेट" in doc_n or "फ्लैट" in doc_n
                    )
                    if is_flat_sale and exec_n:
                        builder_name = exec_n
                        break
                
                if builder_name:
                    injected_const = {
                        "template_key": "CONSTRUCTION_FLAT",
                        "event_type": "CONSTRUCTION",
                        "executant_name": builder_name,
                        "s": builder_name,
                        "claimant_name": project_name or "बहुमंजिला इमारत",
                        "b": project_name or "बहुमंजिला इमारत",
                        "document_name": "CONSTRUCTION",
                        "is_registered": "false",
                        "d": "",
                        "date": "",
                        "b_no": "",
                        "v_no": "",
                        "p_no": "",
                        "r_no": ""
                    }
                    title_chain.append(injected_const)
                    current_data["title_chain"] = title_chain
                    current_data["chain"] = title_chain
                    chain_events = title_chain

        ps0 = current_data.get("ps", [{}])[0]
        chain_paras = generate_chain_narrative(chain_events, property_details=ps0, context=current_data)
        current_data["chain_text"] = "\n\n\t".join(chain_paras)

        session["data"] = current_data

        verified_fields = set(session.get("verified_fields", []))
        save_case_session(case_id,
                          session["data"],
                          session["files"],
                          verified_fields,
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
                          legal_report_files=session.get("legal_report_files", []))

        return jsonify({"success": True, "title_chain": chain_events})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@cases_bp.route("/case/<case_id>/preview_chain", methods=["POST"])
def preview_chain(case_id):
    req_data = request.json or {}
    events = req_data.get("events", [])

    if not events:
        return jsonify({"success": True, "preview_text": ""})

    try:
        preview_text = generate_chain_narrative(events)
        if isinstance(preview_text, list):
            preview_text = "\n\n\t".join(preview_text)
        return jsonify({"success": True, "preview_text": preview_text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@cases_bp.route("/delete_case/<case_id>", methods=["POST"])
def delete_case(case_id):
    delete_case_directory(case_id)
    return redirect(url_for("dashboard.dashboard"))

@cases_bp.route("/api/cases/bulk_delete", methods=["POST"])
def bulk_delete_cases():
    req_data = request.json or {}
    case_ids = req_data.get("case_ids", [])
    deleted = 0
    for case_id in case_ids:
        safe_case_id = os.path.basename(case_id)
        if safe_case_id and delete_case_directory(safe_case_id):
            deleted += 1
    return jsonify({"success": True, "deleted": deleted})

def classify_case_pdfs(case_id: str, session: dict):
    import pypdf
    import os
    from services.session_manager import CASES_DIR
    
    # Collect all unique PDF file paths from files lists and directories
    pdf_paths = set()
    for filepath in session.get("files", []):
        if filepath.lower().endswith(".pdf"):
            pdf_paths.add(filepath)
    for filepath in session.get("legal_report_files", []):
        if filepath.lower().endswith(".pdf"):
            pdf_paths.add(filepath)
            
    for folder in ["files", "legal_reports"]:
        folder_dir = os.path.join(CASES_DIR, case_id, folder)
        if os.path.exists(folder_dir):
            for f in os.listdir(folder_dir):
                if f.lower().endswith(".pdf"):
                    pdf_paths.add(os.path.join(folder_dir, f))
                    
    legal_files = []
    technical_files = []
    
    for filepath in pdf_paths:
        if not os.path.exists(filepath):
            continue
        try:
            reader = pypdf.PdfReader(filepath)
            # Scan first 3 pages to extract structural markers
            first_pages_text = ""
            for idx in range(min(3, len(reader.pages))):
                first_pages_text += (reader.pages[idx].extract_text() or "")
            
            text_lower = first_pages_text.lower()
            
            # Technical Scrutiny / Valuation Report markers
            if "3. visit details" in text_lower or "visit details" in text_lower or "nearby landmark" in text_lower or "technical scrutiny" in text_lower:
                technical_files.append(filepath)
            # Legal Search / Scrutiny Report markers
            elif any(marker in text_lower for marker in ["legal scrutiny", "scrutiny report", "title search", "search report", "flow of title", "history of title", "legal search"]):
                legal_files.append(filepath)
        except Exception:
            pass
            
    return list(legal_files), list(technical_files)


def get_classified_report_texts(case_id: str, session: dict):
    import pypdf
    import os
    from utils.helpers import select_relevant_pdf_pages, extract_pdf_pages_text
    
    legal_files, technical_files = classify_case_pdfs(case_id, session)
    
    # 1. Compile Legal Scrutiny Report text (optimized page selection)
    legal_texts = []
    legal_keywords = [
        "flow of title", "history of title", "scrutiny report", 
        "owner", "proposed owner", "present owner", 
        "purchased by", "belonging to", "mortgagor", 
        "agreement to sale", "allotment letter", "sale deed"
    ]
    for filepath in legal_files:
        try:
            page_indices = select_relevant_pdf_pages(filepath, keywords=legal_keywords)
            if page_indices:
                pdf_text = extract_pdf_pages_text(filepath, page_indices)
                if pdf_text.strip():
                    legal_texts.append(f"=== Legal Report File: {os.path.basename(filepath)} (Selected Pages) ===\n{pdf_text}")
        except Exception:
            pass
            
    # 2. Compile Technical Valuation Report text (optimized page selection)
    technical_texts = []
    tech_keywords = ["visit details", "3. visit details", "address of property", "address as per legal document"]
    for filepath in technical_files:
        try:
            reader = pypdf.PdfReader(filepath)
            total_pages = len(reader.pages)
            selected_pages = []
            for idx in range(total_pages):
                txt_lower = (reader.pages[idx].extract_text() or "").lower()
                if any(kw in txt_lower for kw in tech_keywords):
                    selected_pages.append(idx)
            if not selected_pages:
                selected_pages = [idx for idx in [0, 1] if idx < total_pages]
                
            pdf_text = extract_pdf_pages_text(filepath, selected_pages)
            if pdf_text.strip():
                technical_texts.append(f"=== Technical Report File: {os.path.basename(filepath)} (Visit/Address Details) ===\n{pdf_text}")
        except Exception:
            pass
            
    return "\n\n".join(legal_texts), "\n\n".join(technical_texts)


@cases_bp.route("/api/case/<case_id>/validation", methods=["GET"])
def get_case_validation(case_id):
    session = load_case_session(case_id)
    if not session:
        return jsonify({"error": "Case session not found"}), 404
        
    from services.validation.engine import ValidationEngine
    doc_type = session.get("doc_type", "RM")
    case_data = session.get("data", {})
    
    # Merge doc_type, id, bank, borrowers count, loans count for validation checks
    case_data_copy = dict(case_data)
    case_data_copy["doc_type"] = doc_type
    case_data_copy["id"] = case_id
    case_data_copy["bank"] = session.get("bank", "")
    case_data_copy["selected_template"] = session.get("selected_template", "")
    
    res = ValidationEngine.validate(doc_type, case_data_copy)
    res_dict = res.to_dict()
    
    run_proofreader = request.args.get("run_proofreader", "false").lower() == "true"
    if run_proofreader and doc_type == "RM":
        try:
            from services.generation_service import compile_and_render_document
            from docx import Document
            from services.validation.nim_proofreader import NIMProofreader
            
            # Render temporary docx for proofreading
            output_filepath, _ = compile_and_render_document(
                case_id=case_id,
                session=session,
                doc_type=doc_type,
                bank=session.get("bank"),
                borrowers=session.get("borrower_count"),
                loans=session.get("loan_count"),
                properties=session.get("properties_count"),
                sellers_count=session.get("sellers_count"),
                buyers_count=session.get("buyers_count"),
                chain_scenario=session.get("chain_scenario"),
                selected_template=session.get("selected_template"),
                property_type=session.get("property_type"),
                verified_fields=set(session.get("verified_fields", []))
            )
            
            doc = Document(output_filepath)
            docx_text_parts = []
            for p in doc.paragraphs:
                if p.text.strip():
                    docx_text_parts.append(p.text)
            for t in doc.tables:
                for row in t.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            docx_text_parts.append(cell.text)
            full_text = "\n".join(docx_text_parts)
            
            # Get cached OCR corpus from raw documents (Aadhaar/PAN scans etc.)
            ocr_corpus = ""
            case_dir = os.path.join(CASES_DIR, case_id)
            ocr_cache_dir = os.path.join(case_dir, "buckets", "ocr")
            if os.path.exists(ocr_cache_dir):
                corpus_parts = []
                for f in os.listdir(ocr_cache_dir):
                    if f.lower().endswith(".txt"):
                        try:
                            with open(os.path.join(ocr_cache_dir, f), "r", encoding="utf-8") as file:
                                corpus_parts.append(file.read())
                        except Exception:
                            pass
                if corpus_parts:
                    ocr_corpus = "\n\n".join(corpus_parts)
            
            # Classify and extract text from Legal and Technical Reports by content
            legal_text, technical_text = get_classified_report_texts(case_id, session)
            
            proofreader_findings = NIMProofreader.proofread(full_text, case_data_copy, ocr_corpus, legal_text, technical_text)
            for f in proofreader_findings:
                res_dict["discrepancies"].append(f.to_dict())
                
            res_dict["is_valid"] = not any(d["severity"] in ["high", "medium"] for d in res_dict["discrepancies"])
        except Exception as e:
            res_dict["discrepancies"].append({
                "category": "proofreader",
                "severity": "medium",
                "explanation": f"Proofreader compilation failed: {str(e)}",
                "suggested_fix": "Verify that all required fields are filled."
            })
            
    return jsonify(res_dict)


