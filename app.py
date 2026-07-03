from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import os
import json
import time
import shutil
import re
from utils.helpers import parse_relation_text, normalize_relation_prefix, convert_hindi_digits_to_english
from modules.rm.extractor import RMDataExtractor
from modules.sd.extractor import SDDataExtractor
from modules.rm.processor import RMTemplateProcessor
from modules.sd.processor import SDTemplateProcessor
from modules.sd.narrative import generate_chain_narrative
from utils.config import DEFAULT_GEMINI_API_KEYS

app = Flask(__name__, template_folder="web_templates", static_folder="static")

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.template_filter('basename')
def basename_filter(s):
    if not s:
        return ""
    return str(s).replace('\\', '/').split('/')[-1]

CASES_DIR = "cases"
TEMPLATES_DIR = "templates"

os.makedirs(CASES_DIR, exist_ok=True)
# --- MODERN DESIGN CONSTANTS ---
BG_MAIN = "#F8FAFC"
SURFACE_CARD = "#FFFFFF"
PRIMARY_NAV = "#0F172A"
ACCENT_BLUE = "#2563EB"
BTN_SUCCESS = "#10B981"
BTN_DANGER = "#EF4444"
BORDER_COLOR = "#E2E8F0"
TEXT_PRIMARY = "#1E293B"
TEXT_SECONDARY = "#64748B"

# --- Template Discovery (from old app.py) ---
def discover_templates():
    template_map = {}
    sd_template_map = {}
    bank_folders = []

    if not os.path.exists(TEMPLATES_DIR):
        return {}, {}, []

    for item in os.listdir(TEMPLATES_DIR):
        bank_dir = os.path.join(TEMPLATES_DIR, item)
        if not os.path.isdir(bank_dir):
            continue

        bank_name = item.upper()
        if bank_name == "SALE_DEED":
            for fname in os.listdir(bank_dir):
                if not fname.lower().endswith(".docx"):
                    continue
                # Parse: SD_{NAME}_{#S}S_{#B}B.docx or similar, or map via fallbacks
                m = re.search(r"(\d+)S_(\d+)B", fname, re.IGNORECASE)
                if m:
                    s_count = m.group(1)
                    b_count = m.group(2)
                else:
                    fname_lower = fname.lower()
                    if "vivek" in fname_lower or "saxena" in fname_lower:
                        s_count, b_count = "2", "1"
                    elif "manoj" in fname_lower or "monu" in fname_lower:
                        s_count, b_count = "1", "1"
                    elif "ganesh" in fname_lower or "pareek" in fname_lower:
                        s_count, b_count = "2", "1"
                    elif "balkishan" in fname_lower or "gurjar" in fname_lower:
                        s_count, b_count = "2", "1"
                    else:
                        s_count, b_count = "1", "1"
                if s_count not in sd_template_map:
                    sd_template_map[s_count] = {}
                sd_template_map[s_count][b_count] = os.path.join(bank_dir, fname)
            continue

        bank_folders.append(bank_name)
        template_map[bank_name] = {}

        for fname in os.listdir(bank_dir):
            if not fname.lower().endswith(".docx"):
                continue
            # Parse: RM_{BANK}_{#B}B_{#L}L_anything.docx, with looser fallbacks
            m = re.match(r"RM_" + re.escape(bank_name) + r"_(\d+)B_(\d+)L", fname, re.IGNORECASE)
            if not m:
                # Fallback to RM_(\d+)B_(\d+)L without bank name
                m = re.match(r"RM_(\d+)B_(\d+)L", fname, re.IGNORECASE)
            if not m:
                # Fallback to (\d+)B_(\d+)L without RM_ and bank name
                m = re.match(r"(\d+)B_(\d+)L", fname, re.IGNORECASE)
                
            if m:
                b_count = m.group(1)   # "1", "2", "3" etc.
                l_count = m.group(2)   # "1", "2", "3" etc.
                
                # Check if it specifies two properties in the filename (e.g. "two properties", "2p", or "2_properties")
                fname_lower = fname.lower()
                is_two_props = "two properties" in fname_lower or "2p" in fname_lower or "2_properties" in fname_lower
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
    return template_map, sd_template_map, bank_folders

template_map, sd_template_map, bank_folders = discover_templates()

# --- Session Management ---
def list_cases():
    cases = []
    if not os.path.exists(CASES_DIR): return []
    for d in os.listdir(CASES_DIR):
        path = os.path.join(CASES_DIR, d, "session.json")
        try:
            with open(path, "r") as f: cases.append(json.load(f))
        except: pass
    return sorted(cases, key=lambda x: x.get("last_updated", 0), reverse=True)

def sync_template_keys_to_property_type(chain_list, property_type):
    if not chain_list or not isinstance(chain_list, list):
        return
        
    plot_to_flat_map = {
        "ALLOTMENT_PLOT": "ALLOTMENT_FLAT",
        "ALLOTMENT_PLOT_NO_DEPOSIT": "ALLOTMENT_FLAT_NO_DEPOSIT",
        "ALLOTMENT_MUNICIPAL_PLOT": "ALLOTMENT_MUNICIPAL_FLAT",
        "SALE_DEED_PLOT": "SALE_DEED_FLAT",
        "TRANSFER_PLOT": "TRANSFER_FLAT"
    }
    
    flat_to_plot_map = {
        "ALLOTMENT_FLAT": "ALLOTMENT_PLOT",
        "ALLOTMENT_FLAT_NO_DEPOSIT": "ALLOTMENT_PLOT_NO_DEPOSIT",
        "ALLOTMENT_MUNICIPAL_FLAT": "ALLOTMENT_MUNICIPAL_PLOT",
        "SALE_DEED_FLAT": "SALE_DEED_PLOT",
        "TRANSFER_FLAT": "TRANSFER_PLOT"
    }
    
    key_map = plot_to_flat_map if property_type == "Flat" else flat_to_plot_map
    
    for evt in chain_list:
        if isinstance(evt, dict):
            old_key = evt.get("template_key")
            if old_key in key_map:
                evt["template_key"] = key_map[old_key]

def load_case_session(case_id):
    path = os.path.join(CASES_DIR, case_id, "session.json")
    if not os.path.exists(path): return None
    with open(path, "r", encoding="utf-8") as f:
        sess = json.load(f)
    # Auto-correct doc_type if it was incorrectly mutated or set to RM
    if sess.get("doc_type") == "RM":
        sel_temp = sess.get("selected_template", "")
        if "SD-" in sel_temp or "sale_deed" in sel_temp.lower():
            sess["doc_type"] = "SD"
    if "data" in sess:
        sess["data"] = convert_hindi_digits_to_english(sess["data"])
        if isinstance(sess["data"], dict):
            property_type = sess.get("property_type", "Plot")
            sess["data"]["property_type"] = property_type
            
            # Universal bidirectional synchronization between long and short keys for title chain

            
            # Property details key synchronization
            for p in sess["data"].get("ps", []):
                if isinstance(p, dict):
                    if "land_area" in p and not p.get("area"):
                        p["area"] = p["land_area"]
                    if "unit" in p and not p.get("area_unit"):
                        p["area_unit"] = p["unit"]
                        
                    # Reverse sync
                    if p.get("area") and not p.get("land_area"):
                        p["land_area"] = p["area"]
                    if p.get("area_unit") and not p.get("unit"):
                        p["unit"] = p["area_unit"]
    return sess

def prune_case_data(data, doc_type):
    if doc_type == "SD":
        from modules.sd.schema import prune_sd_data
        return prune_sd_data(data)
    else:
        from modules.rm.schema import prune_rm_data
        return prune_rm_data(data)

def save_case_session(case_id, data, files, verified_fields, bank, borrower_count, loan_count, properties_count="1", processed_files=None, doc_type=None, sellers_count=None, buyers_count=None, chain_scenario=None, selected_template=None, property_type=None, legal_report_files=None, buckets=None):
    os.makedirs(os.path.join(CASES_DIR, case_id), exist_ok=True)
    
    # Load existing to preserve fields if not explicitly passed
    existing = load_case_session(case_id) or {}
    if doc_type is None:
        doc_type = existing.get("doc_type", "RM")
    if sellers_count is None:
        sellers_count = existing.get("sellers_count", "1")
    if buyers_count is None:
        buyers_count = existing.get("buyers_count", "1")
    if chain_scenario is None:
        chain_scenario = existing.get("chain_scenario", "")
    if selected_template is None:
        selected_template = existing.get("selected_template", "")
    if property_type is None:
        property_type = existing.get("property_type", "Plot")

    # Merge incoming data with existing session data to preserve rich AI-extracted fields
    existing_data = existing.get("data", {})
    merged_data = data.copy()
    
    if "unassigned_aadhars" in existing_data and "unassigned_aadhars" not in merged_data:
        merged_data["unassigned_aadhars"] = existing_data["unassigned_aadhars"]
        
    for key in ["ps", "sellers", "buyers", "ss", "bs", "ws", "chain", "title_chain"]:
        if key in existing_data and key in merged_data:
            existing_list = existing_data[key]
            incoming_list = merged_data[key]
            
            if isinstance(existing_list, list) and isinstance(incoming_list, list):
                merged_list = []
                for idx, incoming_item in enumerate(incoming_list):
                    if idx < len(existing_list):
                        existing_item = existing_list[idx]
                        if isinstance(existing_item, dict) and isinstance(incoming_item, dict):
                            merged_item = existing_item.copy()
                            merged_item.update(incoming_item)
                            merged_list.append(merged_item)
                        else:
                            merged_list.append(incoming_item)
                    else:
                        merged_list.append(incoming_item)
                merged_data[key] = merged_list
            elif not incoming_list and existing_list:
                merged_data[key] = existing_list
                

                 
    pruned_data = prune_case_data(merged_data, doc_type)

    if doc_type == "SD":
        sellers_list = pruned_data.get("ss", [{}])
        s_name = sellers_list[0].get("n") if sellers_list else ""
        s_name = s_name.strip() if s_name and s_name.strip() else "New Case"
        
        b_name = pruned_data.get("bs", [{}])[0].get("n") if pruned_data.get("bs") else ""
        b_name = b_name.strip() if b_name and b_name.strip() else "New Case"
        
        display_name = f"SD: {s_name} -> {b_name}"
    else:
        display_name = pruned_data.get("bs", [{}])[0].get("n", "New Case") if pruned_data.get("bs") else "New Case"

    session = {
        "id": case_id,
        "borrower_name": display_name,
        "bank": bank,
        "borrower_count": borrower_count,
        "loan_count": loan_count,
        "properties_count": properties_count or "1",
        "last_updated": time.time(),
        "data": pruned_data,
        "verified_fields": list(verified_fields),
        "files": files,
        "processed_files": processed_files or [],
        "watch_folder": None, # Not applicable for web
        "doc_type": doc_type,
        "sellers_count": sellers_count or "1",
        "buyers_count": buyers_count or "1",
        "chain_scenario": chain_scenario or "",
        "selected_template": selected_template or "",
        "property_type": property_type or "Plot",
        "legal_report_files": legal_report_files if legal_report_files is not None else existing.get("legal_report_files", []),
        "buckets": buckets if buckets is not None else existing.get("buckets", {})
    }
    if "data" in session and session["data"]:
        session["data"] = convert_hindi_digits_to_english(session["data"])
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
        
        # If it is one of our entity lists: 'ls', 'ps', 'unassigned_aadhars', 'sellers', 'buyers', 'ss', 'bs', 'ws', 'title_chain'
        # We merge them by unique keys rather than index to prevent overwriting during incremental scans
        if path in ["ls", "ps", "unassigned_aadhars", "sellers", "buyers", "ss", "bs", "ws", "title_chain",
                    "data.ls", "data.ps", "data.unassigned_aadhars", "data.sellers", "data.buyers", "data.ss", "data.bs", "data.ws", "data.title_chain"]:
            if "ls" in path: key_field = "n"
            elif "unassigned" in path: key_field = "id"
            elif "sellers" in path or "buyers" in path or "ss" in path or "bs" in path or "ws" in path: key_field = "n"
            elif "title_chain" in path: key_field = "date"
            else: key_field = "adr"
            
            # Start with existing items that actually contain values
            existing_entities = [item for item in merged if isinstance(item, dict) and any(item.values())]
            
            # Map existing entities by their unique normalized key
            existing_by_key = {}
            empty_existing_indices = []
            for i, item in enumerate(existing_entities):
                val = str(item.get(key_field, "")).strip().casefold()
                if val:
                    existing_by_key[val] = i
                else:
                    empty_existing_indices.append(i)
                    
            for idx, new_item in enumerate(new):
                if not isinstance(new_item, dict) or not any(new_item.values()):
                    continue
                new_val = str(new_item.get(key_field, "")).strip().casefold()
                
                if new_val and new_val in existing_by_key:
                    # Key match found: merge recursively
                    match_idx = existing_by_key[new_val]
                    merged_item = smart_merge(existing_entities[match_idx], new_item, verified_fields, f"{path}.MATCH")
                    existing_entities[match_idx] = merged_item
                elif new_val and empty_existing_indices:
                    # Merge extracted item into an empty UI slot
                    empty_idx = empty_existing_indices.pop(0)
                    merged_item = smart_merge(existing_entities[empty_idx], new_item, verified_fields, f"{path}.{empty_idx}")
                    existing_entities[empty_idx] = merged_item
                    existing_by_key[new_val] = empty_idx
                elif not new_val and len(existing_entities) > idx and ("ps" in path or "ss" in path or "bs" in path or "ws" in path):
                    # Same index fallback for items if key is missing but we're updating the same position
                    merged_item = smart_merge(existing_entities[idx], new_item, verified_fields, f"{path}.{idx}")
                    existing_entities[idx] = merged_item
                else:
                    # New unique key or safely appending
                    existing_entities.append(new_item)
                    if new_val:
                        existing_by_key[new_val] = len(existing_entities) - 1
                    else:
                        empty_existing_indices.append(len(existing_entities) - 1)
                    
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
    doc_type = request.args.get("doc_type", "RM")
    import datetime
    today_str = datetime.date.today().strftime("%d.%m.%Y")
    # Create a session with today's date initialized in rd
    save_case_session(case_id, {"rd": today_str}, [], set(), "", "", "", doc_type=doc_type)
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
                           verified_fields=list(verified_fields))

@app.route("/get_models")
def get_models():
    try:
        extractor = RMDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS, provider="gemini")
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
    doc_type = request.args.get("doc_type", "RM")
    selected_template = request.args.get("selected_template", "")
    case_id = request.args.get("case_id")
    
    if not selected_template and case_id:
        session = load_case_session(case_id)
        if session:
            selected_template = session.get("selected_template", "")
            
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

@app.route("/case/<case_id>/upload_custom_template", methods=["POST"])
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

    # Save to cases/<case_id>/custom_templates/
    custom_dir = os.path.join(CASES_DIR, case_id, "custom_templates")
    os.makedirs(custom_dir, exist_ok=True)
    
    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)
    if not filename:
        filename = "custom_template.docx"
        
    filepath = os.path.join(custom_dir, filename)
    file.save(filepath)

    # Save to session
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

@app.route("/case/<case_id>/clear_custom_template", methods=["POST"])
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

@app.route("/case/<case_id>/save", methods=["POST"])
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
    
    # Overwrite session data directly with user's manual UI choice,
    # but preserve unassigned_aadhars so they are not lost.
    current_extracted_data = session.get("data", {})
    merged_data = ui_data.copy()
    if "unassigned_aadhars" in current_extracted_data:
        merged_data["unassigned_aadhars"] = current_extracted_data["unassigned_aadhars"]

    # Prune and synchronize frontend/backend aliases to prevent data loss
    merged_data = prune_case_data(merged_data, doc_type)

    for key in ["ss", "bs", "ws", "ps", "sellers", "buyers"]:
        if key in current_extracted_data and key in merged_data:
            ui_arr = merged_data[key]
            current_arr = current_extracted_data[key]
            # If the UI sent an array where ALL items are completely empty, but we already have valid data, keep ours
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
                      chain_scenario=chain_scenario,
                      selected_template=selected_template,
                      property_type=property_type,
                      legal_report_files=session.get("legal_report_files", []))

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
                      session.get("processed_files", []),
                      doc_type=session.get("doc_type"),
                      sellers_count=session.get("sellers_count"),
                      buyers_count=session.get("buyers_count"),
                      chain_scenario=session.get("chain_scenario"),
                      selected_template=session.get("selected_template"),
                      property_type=session.get("property_type"),
                      legal_report_files=session.get("legal_report_files", []))

    return jsonify({"success": True, "new_files": [os.path.basename(f) for f in new_file_paths]})


@app.route("/case/<case_id>/upload_bucket/<bucket_name>", methods=["POST"])
def upload_bucket(case_id, bucket_name):
    import os
    from werkzeug.utils import secure_filename
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

@app.route("/case/<case_id>/upload_legal_report", methods=["POST"])
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
    
    # Check if user specified a subset of files to process
    selected_filenames = req_data.get("selected_files")
    if selected_filenames:
        files_to_process = [f for f in all_files if os.path.basename(f) in selected_filenames]
    else:
        files_to_process = [f for f in all_files if f not in processed_files]

    buckets = session.get("buckets", {})
    has_bucket_files = any(len(b) > 0 for b in buckets.values())

    if not files_to_process and not has_bucket_files:
        if all_files:
            files_to_process = all_files
        else:
            return jsonify({"success": False, "error": "No documents selected to process."}), 400

    try:
        current_data = session.get("data", {})
        
        # If regenerate is requested, clear the old title chain data to start fresh
        if req_data.get("regenerate"):
            for k in ["chain_text", "chain_paragraphs"]:
                if k in current_data:
                    del current_data[k]
                    
        verified_fields = set(session.get("verified_fields", []))

        if doc_type == "SD":
            # Pre-pad ss, bs, and ws lists in current_data to the expected count so that smart_merge
            # and bucket-merging functions can successfully merge the extracted fields.
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

        session["data"] = smart_merge(current_data, extracted_data, verified_fields)
        
        # Auto-detect if the extracted property is a Flat
        ps_list = session["data"].get("ps", [{}])
        property_type = req_data.get("property_type") or session.get("property_type", "Plot")
        if ps_list and isinstance(ps_list[0], dict):
            p0 = ps_list[0]
            if p0.get("flat_no") or p0.get("building_name") or p0.get("floor") or "flat" in str(p0.get("plot_no", "")).lower():
                property_type = "Flat"
        
        session["property_type"] = property_type
        session["data"]["property_type"] = property_type
        

        
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
    
    selected_template = req_data.get("selected_template", "")
    property_type = req_data.get("property_type", "Plot")
    
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
                      chain_scenario=chain_scenario,
                      selected_template=selected_template,
                      property_type=property_type)

    # Reload from session to get the fully merged data (retains flat_no, executant_name, etc.)
    session = load_case_session(case_id)
    data = session["data"]

    if selected_template:
        # Check custom templates first
        custom_path = os.path.join(CASES_DIR, case_id, "custom_templates", selected_template)
        if os.path.exists(custom_path):
            template_path = custom_path
        elif doc_type == "SD":
            template_path = os.path.join(TEMPLATES_DIR, "SALE_DEED", selected_template)
        else:
            template_path = os.path.join(TEMPLATES_DIR, bank, selected_template) if bank else ""
    else:
        if doc_type == "SD":
            # Resolve Sale Deed template
            template_path = sd_template_map.get(str(sellers_count), {}).get(str(buyers_count))
            if not template_path or not os.path.exists(template_path):
                san_scenario = re.sub(r'[^\w\-]', '_', chain_scenario or "JDA_2SD_Flat")
                template_filename = f"SD_{san_scenario}_{sellers_count}S_{buyers_count}B.docx"
                template_path = os.path.join(TEMPLATES_DIR, "SALE_DEED", template_filename)
                
                # Fallbacks
                if not os.path.exists(template_path):
                    template_path = os.path.join(TEMPLATES_DIR, "SALE_DEED", f"SD_JDA_2SD_Flat_{sellers_count}S_{buyers_count}B.docx")
                if not os.path.exists(template_path):
                    template_path = os.path.join(TEMPLATES_DIR, "SALE_DEED", "SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat_unicode (1)_devlys.docx")
        else:
            # Resolve RM template
            sub_map = template_map.get(bank, {}).get(str(borrowers), {}).get(str(loans))
            if isinstance(sub_map, dict):
                template_path = sub_map.get(str(properties)) or sub_map.get("1")
            else:
                template_path = sub_map

    if doc_type == "SD" and (not template_path or not os.path.exists(template_path)):
        sd_dir = os.path.join(TEMPLATES_DIR, "SALE_DEED")
        if os.path.exists(sd_dir):
            docx_files = [os.path.join(sd_dir, f) for f in os.listdir(sd_dir) if f.lower().endswith(".docx")]
            if docx_files:
                template_path = docx_files[0]

    if not template_path or not os.path.exists(template_path):
        return jsonify({"success": False, "error": "No valid template found."}), 400

    # Map the second_schedule string into the ds list for the templates.
    sec_sched_val = data.get("second_schedule", "")
    sec_sched_val = re.sub(r'(?<=\S)\s+(Original\b|Certified Copy\b)', r'\n\1', sec_sched_val, flags=re.IGNORECASE)
    sec_lines = [x.strip() for x in sec_sched_val.split("\n") if x.strip()]
    ds_list = [{"t": line} for line in sec_lines]
    
    while len(ds_list) < 10:
        ds_list.append({"t": ""})
    data["ds"] = ds_list

    # Ensure all required lists exist to prevent Jinja2 errors, and pad them to prevent out-of-bounds [MISSING]
    from collections import defaultdict
    for key in ["bs", "ls", "ps", "ws", "ss", "sellers", "buyers", "chain"]:
        if key not in data or not isinstance(data[key], list):
            data[key] = []
        while len(data[key]) < 10:
            data[key].append(defaultdict(str))

    # Provide 'd' as an alias for the entire data object. 
    context = data.copy()
    context["w1"] = data["ws"][0]
    context["w2"] = data["ws"][1]
    
    # (Chain text/paragraphs logic moved down to use computed ps fields)

    # SD-specific field aliasing: the SD template uses .address and .aadhaar
    # but the extractor stores .adr and .id. Inject aliases for compatibility.
    if doc_type == "SD":
        for list_key in ["ss", "bs", "ws"]:
            for person in context.get(list_key, []):
                if isinstance(person, dict):
                    if "address" not in person or not person["address"]:
                        person["address"] = person.get("adr", "")
                    if "aadhaar" not in person or not person["aadhaar"]:
                        person["aadhaar"] = person.get("id", "")
                    # PRIORITY: Alias age and caste for SD parity
                    if "age" not in person or not person["age"]:
                        person["age"] = person.get("a", "")
                    if "caste" not in person or not person["caste"]:
                        person["caste"] = person.get("c", "")
        # Also alias w1, w2
        for w in [context.get("w1"), context.get("w2")]:
            if isinstance(w, dict):
                if "address" not in w or not w["address"]:
                    w["address"] = w.get("adr", "")
                if "aadhaar" not in w or not w["aadhaar"]:
                    w["aadhaar"] = w.get("id", "")


        # Format Consideration Amount (Indian numbering system)
        raw_amount = str(context.get("amount", "")).strip()
        if raw_amount and raw_amount.isdigit():
            try:
                amt_int = int(raw_amount)
                s = str(amt_int)
                if len(s) > 3:
                    last_three = s[-3:]
                    other = s[:-3][::-1]
                    parts = [other[i:i+2] for i in range(0, len(other), 2)]
                    res = ",".join(parts)[::-1]
                    context["amount"] = res + "," + last_three + "/-"
                else:
                    context["amount"] = s + "/-"
            except:
                pass
        elif raw_amount and not raw_amount.endswith("/-"):
            context["amount"] = raw_amount + "/-"

        # Clean up amount_words to prevent duplicate "मात्र"
        if context.get("amount_words"):
            context["amount_words"] = context["amount_words"].replace("मात्र", "").strip()

        # Build payment_details if not present
        if "sale" not in context:
            context["sale"] = {}

        # Format Consideration Amount (Indian numbering system)
        raw_amount = str(context.get("amount", "")).strip()
        formatted_amount = ""
        if raw_amount and raw_amount.isdigit():
            try:
                amt_int = int(raw_amount)
                s = str(amt_int)
                if len(s) > 3:
                    last_three = s[-3:]
                    other = s[:-3][::-1]
                    parts = [other[i:i+2] for i in range(0, len(other), 2)]
                    formatted_amount = ",".join(parts)[::-1] + "," + last_three + "/-"
                else:
                    formatted_amount = s + "/-"
            except:
                formatted_amount = raw_amount + "/-"
        elif raw_amount:
            formatted_amount = raw_amount if raw_amount.endswith("/-") else raw_amount + "/-"

        context["sale"]["amount"] = formatted_amount
        context["amount"] = formatted_amount # keep original for compatibility

        # Clean up amount_words to prevent duplicate "मात्र"
        words = context.get("amount_words", "")
        if words:
            words = words.replace("मात्र", "").strip()
            # Prepend firm standard prefix for SD
            if doc_type == "SD" and "अक्षरे" not in words:
                words = "अक्षरे " + words
            context["sale"]["amount_words"] = words
            context["amount_words"] = words

        # If no payments/instruments exist, set to empty string.
        # Do not generate fallback narration.
        if not context.get("payments") and not context.get("sale", {}).get("payment_details"):
            context["sale"]["payment_details"] = ""

        # Heal missing entities from title_chain
        if doc_type == "SD":
            ss_list = context.get("ss", [])
            if len(ss_list) < 2:
                # Need to pad it first
                while len(ss_list) < 2:
                    ss_list.append({})
            
            s1 = ss_list[1]
            if not s1.get("n") and "title_chain" in context:
                # Look for second executant in the most recent chain event
                for evt in reversed(context["title_chain"]):
                    executant = evt.get("executant_name", "")
                    if "एवं" in executant or "व" in executant or "," in executant:
                        # Likely multi-party
                        parts = re.split(r'\s+एवं\s+|\s+व\s+|,', executant)
                        if len(parts) > 1:
                            name2 = parts[1].strip()
                            s1["n"] = name2
                            break
            
            context["ss"] = ss_list

        # Recompute ps computed fields at generation time for SD
        if doc_type == "SD":
            _sd_extractor = SDDataExtractor()
            # Dynamic property type detection
            ps0 = context.get("ps", [{}])[0]
            is_flat_property = _sd_extractor.is_flat_property(ps0)
            property_type = "Flat" if is_flat_property else "Plot"

            # Heal flat_no from title_chain if missing in ps[0]
            if "ps" in context and context["ps"] and isinstance(context["ps"][0], dict):
                p0 = context["ps"][0]
                if not p0.get("flat_no") and "title_chain" in context:
                    for evt in context["title_chain"]:
                        if evt.get("unit_number"):
                            p0["flat_no"] = evt["unit_number"]
                            break

            for p in context.get("ps", []):
                if isinstance(p, dict) and any(p.values()):
                    p["full_address"] = _sd_extractor.generate_full_property_address(p, "SD", property_type)
                    p["plot_address"] = _sd_extractor.generate_plot_address(p)

                    # PRIORITY 2: Use plot_address before dimension_text
                    dim = _sd_extractor.generate_dimension_text(p)
                    if p.get("plot_address"):
                        p["dimension_text"] = f"{p['plot_address']} में स्थित है, {dim}"
                    else:
                        p["dimension_text"] = dim

                    if not p.get("boundary_text"):
                        p["boundary_text"] = _sd_extractor.generate_boundary_text(p)

    if "title_chain" in context and isinstance(context["title_chain"], list):
        for evt in context["title_chain"]:
            if evt.get("date"):
                evt["date"] = str(evt["date"]).replace(".", "-")
            if evt.get("reg_date"):
                evt["reg_date"] = str(evt["reg_date"]).replace(".", "-")
                
    # Normalize execution date for SD
    if doc_type == "SD" and context.get("rd"):
        normalized_rd = str(context["rd"]).replace(".", "-")
        context["rd"] = normalized_rd
        if "deed" not in context:
            context["deed"] = {}
        context["deed"]["execution_date"] = normalized_rd

    # Now generate chain paragraphs since we have computed ps fields
    if doc_type == "SD":
        if context.get("chain_is_manual") in ["true", True]:
            # Bypass template compilation, respect user's manual edits
            if context.get("chain_text"):
                context["chain_paragraphs"] = [p.strip() for p in context["chain_text"].split("\n\n") if p.strip()]
            else:
                context["chain_paragraphs"] = []
        elif "title_chain" in context and isinstance(context["title_chain"], list) and len(context["title_chain"]) > 0:
            ps0 = context.get("ps", [{}])[0]
            chain_paras = generate_chain_narrative(context["title_chain"], property_details=ps0, context=context)
            context["chain_paragraphs"] = chain_paras
            context["chain_text"] = "\n\n\t".join(chain_paras)
        elif context.get("chain_text"):
            context["chain_paragraphs"] = [p.strip() for p in context["chain_text"].split("\n\n") if p.strip()]
        else:
            context["chain_paragraphs"] = []
            context["chain_text"] = ""
    else:
        # For RM, keep old logic
        if "title_chain" in context and isinstance(context["title_chain"], list):
            context["chain_text"] = generate_chain_narrative(context["title_chain"])
        else:
            context["chain_text"] = ""

        
    context['d'] = context.copy()  

    output_filename = f"{doc_type}_{case_id}.docx"
    output_filepath = os.path.join(CASES_DIR, case_id, output_filename)

    try:
        if doc_type == "SD":
            processor = SDTemplateProcessor(template_path)
        else:
            processor = RMTemplateProcessor(template_path)
        processor.generate(context, output_filepath, highlight_ai=True, highlight_missing=True, verified_fields=verified_fields)
        return send_file(output_filepath, as_attachment=True, download_name=output_filename)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/case/<case_id>/preview_draft", methods=["POST"])
def preview_draft(case_id):
    session = load_case_session(case_id)
    if not session: return jsonify({"success": False, "error": "Case not found"}), 404

    req_data = request.json or {}
    doc_type = req_data.get("doc_type", "RM")
    
    bank = req_data.get("bank")
    borrowers = req_data.get("borrowers")
    loans = req_data.get("loans")
    properties = req_data.get("properties", "1")
    
    sellers_count = req_data.get("sellers_count", "1")
    buyers_count = req_data.get("buyers_count", "1")
    chain_scenario = req_data.get("chain_scenario", "")
    
    selected_template = req_data.get("selected_template", "")
    property_type = req_data.get("property_type", "Plot")
    
    data = req_data.get("data", {})
    verified_fields = set(req_data.get("verified_fields", session.get("verified_fields", [])))

    template_path = ""
    if selected_template:
        custom_path = os.path.join(CASES_DIR, case_id, "custom_templates", selected_template)
        if os.path.exists(custom_path):
            template_path = custom_path
        elif doc_type == "SD":
            template_path = os.path.join(TEMPLATES_DIR, "SALE_DEED", selected_template)
        else:
            template_path = os.path.join(TEMPLATES_DIR, bank, selected_template) if bank else ""
    else:
        if doc_type == "SD":
            template_path = sd_template_map.get(str(sellers_count), {}).get(str(buyers_count))
            if not template_path or not os.path.exists(template_path):
                san_scenario = re.sub(r'[^\w\-]', '_', chain_scenario or "JDA_2SD_Flat")
                template_filename = f"SD_{san_scenario}_{sellers_count}S_{buyers_count}B.docx"
                template_path = os.path.join(TEMPLATES_DIR, "SALE_DEED", template_filename)
                if not os.path.exists(template_path):
                    template_path = os.path.join(TEMPLATES_DIR, "SALE_DEED", f"SD_JDA_2SD_Flat_{sellers_count}S_{buyers_count}B.docx")
                if not os.path.exists(template_path):
                    template_path = os.path.join(TEMPLATES_DIR, "SALE_DEED", "SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat_unicode (1)_devlys.docx")
        else:
            sub_map = template_map.get(bank, {}).get(str(borrowers), {}).get(str(loans))
            if isinstance(sub_map, dict):
                template_path = sub_map.get(str(properties)) or sub_map.get("1")
            else:
                template_path = sub_map

    if doc_type == "SD" and (not template_path or not os.path.exists(template_path)):
        sd_dir = os.path.join(TEMPLATES_DIR, "SALE_DEED")
        if os.path.exists(sd_dir):
            docx_files = [os.path.join(sd_dir, f) for f in os.listdir(sd_dir) if f.lower().endswith(".docx")]
            if docx_files:
                template_path = docx_files[0]

    if not template_path or not os.path.exists(template_path):
        return jsonify({"success": False, "error": "No valid template found."}), 400

    sec_sched_val = data.get("second_schedule", "")
    sec_sched_val = re.sub(r'(?<=\S)\s+(Original\b|Certified Copy\b)', r'\n\1', sec_sched_val, flags=re.IGNORECASE)
    sec_lines = [x.strip() for x in sec_sched_val.split("\n") if x.strip()]
    ds_list = [{"t": line} for line in sec_lines]
    while len(ds_list) < 10:
        ds_list.append({"t": ""})
    data["ds"] = ds_list

    from collections import defaultdict
    for key in ["bs", "ls", "ps", "ws", "ss", "sellers", "buyers", "chain"]:
        if key not in data or not isinstance(data[key], list):
            data[key] = []
        while len(data[key]) < 10:
            data[key].append(defaultdict(str))

    context = data.copy()
    context["w1"] = data["ws"][0]
    context["w2"] = data["ws"][1]

    if doc_type == "SD":
        for list_key in ["ss", "bs", "ws"]:
            for person in context.get(list_key, []):
                if isinstance(person, dict):
                    if "address" not in person or not person["address"]:
                        person["address"] = person.get("adr", "")
                    if "aadhaar" not in person or not person["aadhaar"]:
                        person["aadhaar"] = person.get("id", "")
                    if "age" not in person or not person["age"]:
                        person["age"] = person.get("a", "")
                    if "caste" not in person or not person["caste"]:
                        person["caste"] = person.get("c", "")
        for w in [context.get("w1"), context.get("w2")]:
            if isinstance(w, dict):
                if "address" not in w or not w["address"]:
                    w["address"] = w.get("adr", "")
                if "aadhaar" not in w or not w["aadhaar"]:
                    w["aadhaar"] = w.get("id", "")

        raw_amount = str(context.get("amount", "")).strip()
        if raw_amount and raw_amount.isdigit():
            try:
                amt_int = int(raw_amount)
                s = str(amt_int)
                if len(s) > 3:
                    last_three = s[-3:]
                    other = s[:-3][::-1]
                    parts = [other[i:i+2] for i in range(0, len(other), 2)]
                    res = ",".join(parts)[::-1]
                    context["amount"] = res + "," + last_three + "/-"
                else:
                    context["amount"] = s + "/-"
            except:
                pass
        elif raw_amount and not raw_amount.endswith("/-"):
            context["amount"] = raw_amount + "/-"

        if context.get("amount_words"):
            context["amount_words"] = context["amount_words"].replace("मात्र", "").strip()

        if "sale" not in context:
            context["sale"] = {}

        raw_amount = str(context.get("amount", "")).strip()
        formatted_amount = ""
        if raw_amount and raw_amount.isdigit():
            try:
                amt_int = int(raw_amount)
                s = str(amt_int)
                if len(s) > 3:
                    last_three = s[-3:]
                    other = s[:-3][::-1]
                    parts = [other[i:i+2] for i in range(0, len(other), 2)]
                    formatted_amount = ",".join(parts)[::-1] + "," + last_three + "/-"
                else:
                    formatted_amount = s + "/-"
            except:
                formatted_amount = raw_amount + "/-"
        elif raw_amount:
            formatted_amount = raw_amount if raw_amount.endswith("/-") else raw_amount + "/-"

        context["sale"]["amount"] = formatted_amount
        context["amount"] = formatted_amount

        words = context.get("amount_words", "")
        if words:
            words = words.replace("मात्र", "").strip()
            if "अक्षरे" not in words:
                words = "अक्षरे " + words
            context["sale"]["amount_words"] = words
            context["amount_words"] = words

        if not context.get("payments") and not context.get("sale", {}).get("payment_details"):
            context["sale"]["payment_details"] = ""

        ss_list = context.get("ss", [])
        if len(ss_list) < 2:
            while len(ss_list) < 2:
                ss_list.append({})
        s1 = ss_list[1]
        if not s1.get("n") and "title_chain" in context:
            for evt in reversed(context["title_chain"]):
                executant = evt.get("executant_name", "")
                if "एवं" in executant or "व" in executant or "," in executant:
                    parts = re.split(r'\s+एवं\s+|\s+व\s+|,', executant)
                    if len(parts) > 1:
                        name2 = parts[1].strip()
                        s1["n"] = name2
                        break
        context["ss"] = ss_list

        _sd_extractor = SDDataExtractor()
        ps0 = context.get("ps", [{}])[0]
        is_flat_property = _sd_extractor.is_flat_property(ps0)
        property_type_val = "Flat" if is_flat_property else "Plot"

        if "ps" in context and context["ps"] and isinstance(context["ps"][0], dict):
            p0 = context["ps"][0]
            if not p0.get("flat_no") and "title_chain" in context:
                for evt in context["title_chain"]:
                    if evt.get("unit_number"):
                        p0["flat_no"] = evt["unit_number"]
                        break

        for p in context.get("ps", []):
            if isinstance(p, dict) and any(p.values()):
                p["full_address"] = _sd_extractor.generate_full_property_address(p, "SD", property_type_val)
                p["plot_address"] = _sd_extractor.generate_plot_address(p)
                dim = _sd_extractor.generate_dimension_text(p)
                if p.get("plot_address"):
                    p["dimension_text"] = f"{p['plot_address']} में स्थित है, {dim}"
                else:
                    p["dimension_text"] = dim
                if not p.get("boundary_text"):
                    p["boundary_text"] = _sd_extractor.generate_boundary_text(p)

    if "title_chain" in context and isinstance(context["title_chain"], list):
        for evt in context["title_chain"]:
            if evt.get("date"):
                evt["date"] = str(evt["date"]).replace(".", "-")
            if evt.get("reg_date"):
                evt["reg_date"] = str(evt["reg_date"]).replace(".", "-")
                
    if doc_type == "SD" and context.get("rd"):
        normalized_rd = str(context["rd"]).replace(".", "-")
        context["rd"] = normalized_rd
        if "deed" not in context:
            context["deed"] = {}
        context["deed"]["execution_date"] = normalized_rd

    if doc_type == "SD":
        if context.get("chain_is_manual") in ["true", True]:
            if context.get("chain_text"):
                context["chain_paragraphs"] = [p.strip() for p in context["chain_text"].split("\n\n") if p.strip()]
            else:
                context["chain_paragraphs"] = []
        elif "title_chain" in context and isinstance(context["title_chain"], list) and len(context["title_chain"]) > 0:
            ps0 = context.get("ps", [{}])[0]
            chain_paras = generate_chain_narrative(context["title_chain"], property_details=ps0, context=context)
            context["chain_paragraphs"] = chain_paras
            context["chain_text"] = "\n\n\t".join(chain_paras)
        elif context.get("chain_text"):
            context["chain_paragraphs"] = [p.strip() for p in context["chain_text"].split("\n\n") if p.strip()]
        else:
            context["chain_paragraphs"] = []
            context["chain_text"] = ""
    else:
        if "title_chain" in context and isinstance(context["title_chain"], list):
            context["chain_text"] = generate_chain_narrative(context["title_chain"])
        else:
            context["chain_text"] = ""

    context['d'] = context.copy()

    try:
        import docx
        import html
        from docxtpl import DocxTemplate
        from docx.text.paragraph import Paragraph
        from docx.table import Table

        doc = DocxTemplate(template_path)
        doc.render(context)

        html_parts = []
        for element in doc.element.body:
            if element.tag.endswith('p'):
                p = Paragraph(element, doc)
                txt = p.text.strip()
                if txt:
                    escaped = html.escape(txt)
                    escaped = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', escaped)
                    html_parts.append(f"<p style='margin-bottom: 0.8rem; line-height: 1.5; text-align: justify; font-family: Segoe UI, Mangal; font-size: 0.92rem;'>{escaped}</p>")
            elif element.tag.endswith('tbl'):
                t = Table(element, doc)
                table_html = ["<table class='table table-sm table-bordered shadow-sm bg-white' style='margin-bottom: 1.2rem; font-size: 0.82rem; font-family: Segoe UI, Mangal;'>"]
                for row in t.rows:
                    table_html.append("<tr>")
                    for cell in row.cells:
                        table_html.append(f"<td style='padding: 6px 10px; border: 1px solid #dee2e6; vertical-align: middle;'>{html.escape(cell.text.strip())}</td>")
                    table_html.append("</tr>")
                table_html.append("</table>")
                html_parts.append("".join(table_html))

        preview_html = "".join(html_parts)
        if not preview_html:
            preview_html = "<p class='text-muted text-center py-4'>Template loaded but contained no readable text elements.</p>"
            
        return jsonify({"success": True, "preview_html": preview_html})
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

@app.route("/case/<case_id>/extract_chain", methods=["POST"])
def extract_chain(case_id):
    """Dedicated AI extraction for Title Chain from legal reports."""
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

        # Translate the title chain to Hindi!
        chain_events = extractor.translate_title_chain_to_hindi(chain_events, file_paths=all_files, model=model)

        # Merge extracted chain into session data
        current_data = session.get("data", {})
        current_data["title_chain"] = chain_events

        # Auto-inject CONSTRUCTION event into title_chain for Flat properties so it shows in the verification UI
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

        # Generate the Hindi narrative text!
        from modules.sd.narrative import generate_chain_narrative
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



@app.route("/case/<case_id>/preview_chain", methods=["POST"])
def preview_chain(case_id):
    """Generate a Hindi narrative preview from title chain events."""
    req_data = request.json or {}
    events = req_data.get("events", [])

    if not events:
        return jsonify({"success": True, "preview_text": ""})

    try:
        preview_text = generate_chain_narrative(events)
        return jsonify({"success": True, "preview_text": preview_text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/devlys-to-unicode")
def devlys_to_unicode_route():
    return render_template("devlys_to_unicode.html")

@app.route("/api/devlys-to-unicode/convert", methods=["POST"])
def devlys_to_unicode_convert():
    try:
        from utils.devlys_to_unicode import DevLysToUnicodeConverter
        from utils.devlys_converter import UnicodeToDevLysConverter
        
        file = request.files.get("file")
        if not file or not file.filename.endswith(".docx"):
            return jsonify({"success": False, "error": "Invalid file format. Please upload a .docx file."}), 400
            
        font_name = request.form.get("font_name", "Mangal")
        direction = request.form.get("direction", "dev_to_uni")
        
        temp_dir = os.path.join(os.getcwd(), "temp_builder")
        os.makedirs(temp_dir, exist_ok=True)
        
        input_filename = f"conv_in_{int(time.time())}.docx"
        output_filename = f"conv_out_{int(time.time())}.docx"
        input_path = os.path.join(temp_dir, input_filename)
        output_path = os.path.join(temp_dir, output_filename)
        
        file.save(input_path)
        
        if direction == "dev_to_uni":
            DevLysToUnicodeConverter.convert_docx(input_path, output_path, font_name)
        else:
            UnicodeToDevLysConverter.convert_docx(input_path, output_path, font_name)
            
        return send_file(output_path, as_attachment=True, download_name=file.filename)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/template-builder")
def template_builder():
    try:
        extractor = RMDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS, provider="gemini")
        models = extractor.get_available_models()
    except Exception:
        models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-lite"]
    rm_fields = []
    sd_fields = []
    sd_generated_fields = []
    try:
        with open("CHAIN_SCHEMA.md", "r") as f:
            for line in f:
                if line.startswith("- `") and "`:" in line:
                    parts = line.split("`:")
                    key = parts[0].replace("- `", "").strip()
                    desc = parts[1].strip()
                    rm_fields.append((desc, key))
    except Exception:
        pass
    try:
        with open("SD_SCHEMA.md", "r") as f:
            for line in f:
                if line.startswith("- `") and "`:" in line:
                    parts = line.split("`:")
                    key = parts[0].replace("- `", "").strip()
                    desc = parts[1].strip()
                    sd_fields.append((desc, key))
    except Exception:
        pass
    return render_template("template_builder.html", models=models, rm_fields=rm_fields, sd_fields=sd_fields, sd_generated_fields=sd_generated_fields)

@app.route("/api/builder/upload", methods=["POST"])
def builder_upload():
    try:
        file = request.files.get("file")
        if not file or not file.filename.endswith(".docx"):
            return jsonify({"success": False, "error": "Invalid file format. Please upload a .docx file."}), 400
            
        temp_dir = os.path.join(os.getcwd(), "temp_builder")
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = f"uploaded_{int(time.time())}.docx"
        filepath = os.path.join(temp_dir, filename)
        file.save(filepath)
        
        return jsonify({"success": True, "filepath": filepath, "filename": file.filename})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/builder/discover", methods=["POST"])
def builder_discover():
    try:
        from template_tools.builder_core import DocManipulator, get_discovery_prompt, clean_mapping
        req_data = request.json
        filepath = req_data.get("filepath")
        mode = req_data.get("mode", "RM")
        model = req_data.get("model", "gemini-2.0-flash-lite")
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({"success": False, "error": "Invalid or missing file path."}), 400
            
        from docx import Document
        doc = Document(filepath)
        content = DocManipulator.get_doc_content(doc)
        
        prompt = get_discovery_prompt(content, mode)
        
        if mode == "SD":
            extractor = SDDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS, provider="gemini")
        else:
            extractor = RMDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS, provider="gemini")
        raw = extractor.raw_generate(prompt, model)
        
        match = re.search(r'\{.*\}', raw or "", re.DOTALL)
        mapping = {}
        if match:
            mapping_str = match.group(0)
            cleaned_lines = []
            for line in mapping_str.splitlines():
                line_stripped = line.strip()
                if line_stripped in ('{', '}', '[', ']', '') or not line_stripped.startswith('"'):
                    cleaned_lines.append(line)
                    continue
                match_val = re.search(r':\s*(("(.*)"|null|true|false|\d+)\s*(,?)\s*)$', line_stripped)
                if not match_val:
                    cleaned_lines.append(line)
                    continue
                key_part = line_stripped[:match_val.start()].strip()
                val_part = match_val.group(1).strip()
                if key_part.startswith('"') and key_part.endswith('"'):
                    raw_key = key_part[1:-1]
                    escaped_key = raw_key.replace('\\"', '"').replace('"', '\\"')
                    key_part = f'"{escaped_key}"'
                raw_val_match = re.match(r'^"(.*)"(,?)$', val_part)
                if raw_val_match:
                    raw_val = raw_val_match.group(1)
                    comma = raw_val_match.group(2)
                    escaped_val = raw_val.replace('\\"', '"').replace('"', '\\"')
                    val_part = f'"{escaped_val}"{comma}'
                indent = line[:len(line) - len(line.lstrip())]
                cleaned_lines.append(f'{indent}{key_part}: {val_part}')
            cleaned_mapping_str = "\n".join(cleaned_lines)
            
            try:
                mapping = json.loads(cleaned_mapping_str)
            except Exception:
                mapping = json.loads(mapping_str)
                
        cleaned = clean_mapping(mapping)
        return jsonify({"success": True, "mapping": cleaned, "doc_text": content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/builder/generate", methods=["POST"])
def builder_generate():
    try:
        from template_tools.builder_core import generate_master_template
        req_data = request.json
        filepath = req_data.get("filepath")
        mapping = req_data.get("mapping", {})
        mode = req_data.get("mode", "RM")
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({"success": False, "error": "Invalid or missing file path."}), 400
            
        temp_dir = os.path.dirname(filepath)
        output_filename = f"generated_master_{int(time.time())}.docx"
        output_path = os.path.join(temp_dir, output_filename)
        
        generate_master_template(filepath, mapping, output_path)
        
        return send_file(output_path, as_attachment=True, download_name="MASTER_TEMPLATE_READY.docx")
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/delete_case/<case_id>")
def delete_case(case_id):
    case_path = os.path.join(CASES_DIR, case_id)
    if os.path.exists(case_path):
        shutil.rmtree(case_path)
    return redirect(url_for("dashboard"))

@app.route("/case/<case_id>/file/<path:filename>")
def serve_case_file(case_id, filename):
    from flask import send_from_directory
    safe_case_id = os.path.basename(case_id)
    case_dir = os.path.abspath(os.path.join(CASES_DIR, safe_case_id))
    search_dirs = [
        os.path.join(case_dir, "buckets", "kyc"),
        os.path.join(case_dir, "buckets", "legal"),
        os.path.join(case_dir, "buckets", "ats"),
        os.path.join(case_dir, "buckets", "title_chain"),
        os.path.join(case_dir, "buckets", "ocr"),
        os.path.join(case_dir, "files"),
        os.path.join(case_dir, "legal_reports"),
        case_dir
    ]
    for directory in search_dirs:
        file_path = os.path.join(directory, os.path.basename(filename))
        if os.path.exists(file_path):
            return send_from_directory(directory, os.path.basename(filename))
    return "File not found", 404

@app.route("/case/<case_id>/delete_file", methods=["POST"])
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

# @app.route("/static/<path:filename>")
# def static_files(filename):
#     # This is a placeholder for local development. In production, serve static files directly.
#     return send_from_directory("static", filename)



@app.route("/devlys_keymap")
def devlys_keymap():
    # Use the definitive DevLys 040 to Unicode mapping
    from utils.devlys_to_unicode import MAPPING_PAIRS
    array_one = [pair[0] for pair in MAPPING_PAIRS]
    array_two = [pair[1] for pair in MAPPING_PAIRS]
    return jsonify({"success": True, "map_from": array_one, "map_to": array_two})

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
            extractor = RMDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS, provider="gemini")
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
    import re

    original_text = text.strip()

    # Smart pre-transliteration replacements (case-insensitive)
    smart_replacements = [
        (r'\bs/o\b\.?', 'पुत्र श्री'),
        (r'\bd/o\b\.?', 'पुत्री श्री'),
        (r'\bw/o\b\.?', 'पत्नी श्री'),
        (r'\bc/o\b\.?', 'मार्फत'),
        (r'\bno\.', 'नं.'),
        (r'\bno\b(?=\s*\d+)', 'नं.'),
        (r'\bmr\.', 'श्री'),
        (r'\bmr\b(?=\s)', 'श्री'),
        (r'\bmrs\.', 'श्रीमती'),
        (r'\bmrs\b(?=\s)', 'श्रीमती'),
        (r'\bms\.', 'सुश्री'),
        (r'\bms\b(?=\s)', 'सुश्री'),
        (r'\bsh\.', 'श्री'),
        (r'\bsh\b(?=\s)', 'श्री'),
        (r'\bsmt\.', 'श्रीमती'),
        (r'\bsmt\b(?=\s)', 'श्रीमती'),
        (r'\bdr\.', 'डॉ.'),
        (r'\blate\b', 'स्वर्गीय'),
        (r'\bflat\b', 'फ्लैट'),
        (r'\bplot\b', 'प्लॉट'),
        (r'\bshop\b', 'दुकान'),
        (r'\bh\.\s*no\.?', 'मकान नं.'),
        (r'\bhouse\s+no\.?', 'मकान नं.'),
        (r'\bward\s+no\.?', 'वार्ड नं.'),
        (r'\bsector\b', 'सेक्टर'),
        (r'\bphase\b', 'फेज'),
        (r'\bblock\b', 'ब्लॉक'),
        (r'\bpocket\b', 'पॉकेट')
    ]
    
    for pat, repl in smart_replacements:
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)

    words = text.strip().split()
    hindi_words = []
    for word in words:
        # Skip if the word contains no English alphabet characters (e.g. it's just numbers/punctuation)
        if not re.search(r'[a-zA-Z]', word):
            hindi_words.append(word)
            continue

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
    if result == original_text:
        return None
    return result



# --- e-Panjiyan Automation Endpoints ---

@app.route("/api/cases/recent")
def get_recent_cases():
    try:
        cases = list_cases()
        recent = []
        for case in cases[:10]:
            case_id = case.get("id", "")
            doc_type = case.get("doc_type", "RM")
            data = case.get("data", {})
            
            name = "Unnamed Case"
            if doc_type == "RM":
                bs = data.get("bs", [])
                if bs and bs[0].get("n"):
                    name = bs[0]["n"]
                else:
                    sig = data.get("bsign", {})
                    if sig.get("n"):
                        name = sig["n"]
            else:
                es = data.get("es", [])
                if es and es[0].get("n"):
                    name = es[0]["n"]
                else:
                    name = data.get("purchaser_name", "Unnamed SD Case")
                    
            recent.append({
                "case_id": case_id,
                "doc_type": doc_type,
                "name": name.upper(),
                "updated": time.strftime("%Y-%m-%d %H:%M", time.localtime(case.get("last_updated", 0)))
            })
        return jsonify(recent)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def split_address(address_str):
    if not address_str:
        return {
            "house_no": "00",
            "colony": "",
            "area": "",
            "city": "JAIPUR",
            "pincode": ""
        }
    
    address_str = address_str.strip()
    
    pincode_match = re.search(r'\b\d{6}\b', address_str)
    pincode = pincode_match.group(0) if pincode_match else ""
    if pincode:
        address_str = address_str.replace(pincode, "").strip()
        
    address_str = re.sub(r'[\s,\.]+$', '', address_str)
    
    city = "JAIPUR"
    city_match = re.search(r'\b(jaipur|sanganer|amer|bagru)\b', address_str, re.IGNORECASE)
    if city_match:
        city = city_match.group(0).upper()
        address_str = re.sub(r'\b' + city_match.group(0) + r'\b', '', address_str, flags=re.IGNORECASE).strip()
        
    address_str = re.sub(r'\b(rajasthan|rj)\b', '', address_str, flags=re.IGNORECASE).strip()
    address_str = re.sub(r'[\s,\.]+$', '', address_str)
    
    house_no = "00"
    house_match = re.search(r'\b(?:plot|p\.?|h\.?|flat|shop|house|ward)\s*(?:no\.?|num\.?)?\s*([a-zA-Z0-9\-/]+)\b', address_str, re.IGNORECASE)
    if house_match:
        house_no = house_match.group(1).upper()
        address_str = address_str.replace(house_match.group(0), "").strip()
    else:
        start_match = re.match(r'^([a-zA-Z0-9\-/]+)\b', address_str)
        if start_match and start_match.group(1).isdigit():
            house_no = start_match.group(1)
            address_str = address_str.replace(house_no, "", 1).strip()
            
    address_str = re.sub(r'^[\s,\.]+', '', address_str)
    address_str = re.sub(r'[\s,\.]+$', '', address_str)
    
    common_areas = [
        "Jhotwara", "Mansarovar", "Sodala", "Malviya Nagar", "Vaishali Nagar", 
        "C-Scheme", "Raja Park", "Adarsh Nagar", "Bani Park", "Shastri Nagar", 
        "Vidhyadhar Nagar", "Pratap Nagar", "Sanganer", "Gopalpura", "Tonk Road", 
        "Jagatpura", "Patrakar Colony", "Nirman Nagar", "Civil Lines", "Ajmer Road", 
        "Sirsi Road", "Kalwar Road", "Agra Road", "Delhi Road", "Amer", "Chomu",
        "Prithviraj Nagar", "PRN", "Muhana", "Bhakrota", "Bindayaka"
    ]
    
    area = ""
    for a in common_areas:
        if re.search(r'\b' + re.escape(a) + r'\b', address_str, re.IGNORECASE):
            area = a.upper()
            address_str = re.sub(r'\b' + re.escape(a) + r'\b', '', address_str, flags=re.IGNORECASE).strip()
            break
            
    address_str = re.sub(r'^[\s,\.\-]+', '', address_str)
    address_str = re.sub(r'[\s,\.\-]+$', '', address_str)
    
    if not area:
        parts = [p.strip() for p in address_str.split(",") if p.strip()]
        if parts:
            area = parts[-1].upper()
            address_str = ",".join(parts[:-1]).strip()
            
    colony = address_str.upper() if address_str else "JAIPUR"
    if not colony:
        colony = area
        
    return {
        "house_no": house_no,
        "colony": colony,
        "area": area,
        "city": city,
        "pincode": pincode
    }


@app.route("/api/case/<case_id>/epanjiyan_data")
def get_epanjiyan_data(case_id):
    try:
        session = load_case_session(case_id)
        if not session:
            return jsonify({"error": "Case not found"}), 404
            
        data = session.get("data", {})
        doc_type = session.get("doc_type", "RM")
        
        sro = "JAIPUR-VII"
        tehsil = "JAIPUR"
        
        face_value = 0
        r_rate = "12.00%"
        emi = ""
        emi_w = ""
        ls = data.get("ls", [])
        if ls:
            for loan in ls:
                try:
                    amt_str = str(loan.get("a", "0")).replace(",", "").replace("/-", "").strip()
                    face_value += int(float(amt_str))
                except:
                    pass
            first_loan = ls[0]
            r_rate = first_loan.get("r_rate", "12.00%")
            if r_rate and "%" not in r_rate:
                r_rate = f"{r_rate}%"
            emi = str(first_loan.get("emi", "")).replace(",", "").replace("/-", "").strip()
            emi_w = first_loan.get("emi_w", "")
            
        def clean_val(val):
            if val is None:
                return ""
            return str(val).strip().upper()
            
        executants = []
        for b in data.get("bs", []):
            name_en = clean_val(b.get("n", ""))
            rel_name_en = clean_val(b.get("rn", ""))
            
            sal = clean_val(b.get("s", ""))
            gender = "MALE"
            if "MRS" in sal or "MS" in sal or "FEMALE" in sal:
                gender = "FEMALE"
                
            addr_str = b.get("adr", "")
            addr_split = split_address(addr_str)
            
            rel_type = clean_val(b.get("r", "S/O"))
            if "W/O" in rel_type or "WIFE" in rel_type:
                rel_type = "HUSBAND"
            else:
                rel_type = "FATHER"
                
            executants.append({
                "name_en": name_en,
                "relation_type": rel_type,
                "relation_name_en": rel_name_en,
                "gender": gender,
                "age": clean_val(b.get("a", "")),
                "dob": clean_val(b.get("dob", "")),
                "aadhaar": clean_val(b.get("id", "")).replace(" ", ""),
                "pan": clean_val(b.get("pan", "")).replace(" ", ""),
                "address": {
                    "house_no": clean_val(addr_split["house_no"]),
                    "colony": clean_val(addr_split["colony"]),
                    "area": clean_val(addr_split["area"]),
                    "city": clean_val(addr_split["city"]),
                    "pincode": clean_val(addr_split["pincode"])
                }
            })
            
        claimant = {}
        bank_map = {
            "CHOLA": {
                "en": "CHOLAMANDALAM INVESTMENT AND FINANCE COMPANY LIMITED"
            },
            "ICICI": {
                "en": "ICICI BANK LIMITED"
            }
        }
        
        bank_folder = session.get("bank", "CHOLA")
        bank_names = bank_map.get(bank_folder, bank_map["CHOLA"])
        
        sig = data.get("bsign", {})
        sig_name_en = clean_val(sig.get("n", ""))
        sig_rel_name_en = clean_val(sig.get("rn", ""))
        
        sig_sal = clean_val(sig.get("s", ""))
        sig_gender = "MALE"
        if "MRS" in sig_sal or "MS" in sig_sal or "FEMALE" in sig_sal:
            sig_gender = "FEMALE"
            
        sig_addr_str = sig.get("adr", "")
        if not sig_addr_str:
            sig_addr_str = "JAIPUR"
        sig_addr_split = split_address(sig_addr_str)
        
        sig_rel_type = clean_val(sig.get("r", "S/O"))
        if "W/O" in sig_rel_type or "WIFE" in sig_rel_type:
            sig_rel_type = "HUSBAND"
        else:
            sig_rel_type = "FATHER"
            
        bank_composite_en = f"{bank_names['en']} THROUGH AUTHORISED SIGNATORY {sig_name_en}"
        
        claimant = {
            "name_en": clean_val(bank_composite_en),
            "relation_type": sig_rel_type,
            "relation_name_en": sig_rel_name_en,
            "gender": sig_gender,
            "age": clean_val(sig.get("a", "")),
            "dob": clean_val(sig.get("dob", "")),
            "aadhaar": clean_val(sig.get("id", "")).replace(" ", ""),
            "pan": clean_val(sig.get("pan", "")).replace(" ", ""),
            "address": {
                "house_no": clean_val(sig_addr_split["house_no"]),
                "colony": clean_val(sig_addr_split["colony"]),
                "area": clean_val(sig_addr_split["area"]),
                "city": clean_val(sig_addr_split["city"]),
                "pincode": clean_val(sig_addr_split["pincode"])
            }
        }
        
        witnesses = []
        for w in data.get("ws", []):
            w_name_en = clean_val(w.get("n", ""))
            w_rel_name_en = clean_val(w.get("rn", ""))
            
            w_rel_type = clean_val(w.get("r", "S/O"))
            if "W/O" in w_rel_type or "WIFE" in w_rel_type:
                w_rel_type = "HUSBAND"
            else:
                w_rel_type = "FATHER"
                
            w_addr_str = w.get("adr", "")
            w_addr_split = split_address(w_addr_str)
            
            w_age = clean_val(w.get("a", ""))
            if not w_age:
                w_age = "35"
                
            witnesses.append({
                "name_en": w_name_en,
                "relation_type": w_rel_type,
                "relation_name_en": w_rel_name_en,
                "gender": "MALE",
                "age": w_age,
                "dob": clean_val(w.get("dob", "")),
                "aadhaar": clean_val(w.get("id", "")),
                "address": {
                    "house_no": clean_val(w_addr_split["house_no"]),
                    "colony": clean_val(w_addr_split["colony"]),
                    "area": clean_val(w_addr_split["area"]),
                    "city": clean_val(w_addr_split["city"]),
                    "pincode": clean_val(w_addr_split["pincode"])
                }
            })
            
        properties = []
        for p in data.get("ps", []):
            p_addr_str = p.get("adr", "")
            p_addr_split = split_address(p_addr_str)
            properties.append({
                "address": {
                    "house_no": clean_val(p_addr_split["house_no"]),
                    "colony": clean_val(p_addr_split["colony"]),
                    "area": clean_val(p_addr_split["area"]),
                    "city": clean_val(p_addr_split["city"]),
                    "pincode": clean_val(p_addr_split["pincode"])
                },
                "lat": clean_val(p.get("lat", "")),
                "lng": clean_val(p.get("lng", ""))
            })
            
        import datetime
        today_date = datetime.date.today().strftime("%d-%m-%Y")
        
        response_data = {
            "case_id": case_id,
            "doc_type": doc_type,
            "sro": sro,
            "tehsil": tehsil,
            "face_value": face_value,
            "execution_date": today_date,
            "r_rate": r_rate,
            "emi": emi,
            "emi_w": clean_val(emi_w),
            "executants": executants,
            "claimant": claimant,
            "witnesses": witnesses,
            "properties": properties
        }
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
