import os
import json
import time
import re
from utils.helpers import parse_relation_text, normalize_relation_prefix, convert_hindi_digits_to_english

CASES_DIR = "cases"

def title_case_address(text):
    if not text:
        return ""
    words = str(text).strip().split()
    if not words:
        return ""
        
    lowercase_words = {"and", "or", "of", "in", "at", "by", "for", "with", "from", "on", "the", "a", "an", "to", "its"}
    
    title_words = []
    for idx, w in enumerate(words):
        w_lower = w.lower()
        
        # Strip trailing punctuation for exact match checks on connecting words/relations
        w_clean = re.sub(r'[^a-zA-Z0-9/]', '', w_lower)
        
        if w_clean in ["s/o", "w/o", "d/o", "h/o", "c/o"]:
            suffix = w[len(w_clean):]
            title_words.append(w_clean[0].upper() + "/" + w_clean[2].lower() + suffix)
        elif w_clean in ["m/s"]:
            suffix = w[len(w_clean):]
            title_words.append("M/s" + suffix)
        elif w_clean in lowercase_words and idx > 0:
            suffix = w[len(w_clean):]
            title_words.append(w_clean + suffix)
        else:
            def replace_alpha(match):
                part = match.group(0)
                part_lower = part.lower()
                if part_lower in lowercase_words:
                    return part_lower
                if re.match(r'^[ivx]+$', part_lower):
                    return part.upper()
                if len(part) == 1:
                    return part.upper()
                return part.capitalize()
                
            title_words.append(re.sub(r'[a-zA-Z\u0900-\u097F]+', replace_alpha, w))
            
    return " ".join(title_words)

def normalize_amount_in_words(w):
    if not w:
        return ""
    s = str(w).strip().strip('.')
    
    # Remove prefix "Rs.", "Rs", "Rupees", "Rupee" (case-insensitive)
    s = re.sub(r'^(?:Rs\.?|Rupees|Rupee)\s*', '', s, flags=re.IGNORECASE).strip()
    
    # Remove suffix "only", "rupees", "rupee" (case-insensitive)
    s = re.sub(r'\s*(?:only|rupees|rupee)\.?$', '', s, flags=re.IGNORECASE).strip()
    
    # Clean up double spaces or commas
    s = re.sub(r'\s+', ' ', s)
    
    if not s:
        return ""
        
    words = s.split()
    title_words = []
    for word in words:
        parts = word.split('-')
        title_parts = [p.capitalize() for p in parts]
        title_words.append('-'.join(title_parts))
    
    cleaned_words = " ".join(title_words)
    return f"Rupees {cleaned_words} Only"

def list_cases():
    cases = []
    if not os.path.exists(CASES_DIR): return []
    for d in os.listdir(CASES_DIR):
        path = os.path.join(CASES_DIR, d, "session.json")
        try:
            with open(path, "r", encoding="utf-8") as f: cases.append(json.load(f))
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

def prune_case_data(data, doc_type):
    if doc_type == "SD":
        from modules.sd.schema import prune_sd_data
        return prune_sd_data(data)
    else:
        from modules.rm.schema import prune_rm_data
        return prune_rm_data(data)

def load_case_session(case_id):
    path = os.path.join(CASES_DIR, case_id, "session.json")
    if not os.path.exists(path): return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            sess = json.load(f)
    except Exception:
        return None
    # Auto-correct doc_type if it was incorrectly mutated or set to RM
    doc_type = sess.get("doc_type", "RM")
    if doc_type == "RM":
        sel_temp = sess.get("selected_template", "")
        if "SD-" in sel_temp or "sale_deed" in sel_temp.lower():
            sess["doc_type"] = "SD"
            doc_type = "SD"
            
    if "data" in sess:
        sess["data"] = convert_hindi_digits_to_english(sess["data"])
        if isinstance(sess["data"], dict):
            property_type = sess.get("property_type", "Plot")
            sess["data"]["property_type"] = property_type
            
            # Clean up duplicate and embedded salutations for RM mode
            if doc_type == "RM":
                from modules.rm.processor import robust_extract_salutation_and_name
                
                def clean_duplicate_salutation(s, n):
                    if not s or not n: return n
                    s_clean = s.strip().lower().rstrip('.')
                    n_clean = n.strip()
                    pattern = rf'^{re.escape(s_clean)}\.?\s*'
                    match_prefix = re.match(pattern, n_clean, re.IGNORECASE)
                    if match_prefix:
                        return n_clean[match_prefix.end():].strip()
                    return n_clean

                # Clean Borrowers
                for b in sess["data"].get("bs", []):
                    if isinstance(b, dict):
                        raw_n = b.get("n", "").strip()
                        raw_s = b.get("s", "").strip()
                        if raw_s and raw_n:
                            cleaned_n = clean_duplicate_salutation(raw_s, raw_n)
                            b["n"] = cleaned_n
                            raw_n = cleaned_n
                        if raw_n:
                            ext_sal, ext_name = robust_extract_salutation_and_name(raw_n)
                            if ext_sal:
                                b["n"] = ext_name
                                if not b.get("s"):
                                    b["s"] = ext_sal

                # Clean Bank Signatory
                bsign = sess["data"].get("bsign")
                if isinstance(bsign, dict):
                    raw_n = bsign.get("n", "").strip()
                    raw_s = bsign.get("s", "").strip()
                    if raw_s and raw_n:
                        cleaned_n = clean_duplicate_salutation(raw_s, raw_n)
                        bsign["n"] = cleaned_n
                        raw_n = cleaned_n
                    if raw_n:
                        ext_sal, ext_name = robust_extract_salutation_and_name(raw_n)
                        if ext_sal:
                            bsign["n"] = ext_name
                            if not bsign.get("s"):
                                bsign["s"] = ext_sal
                
                # Clean Addresses to Title Case
                for b in sess["data"].get("bs", []):
                    if isinstance(b, dict) and b.get("adr"):
                        b["adr"] = title_case_address(b["adr"])
                for w in sess["data"].get("ws", []):
                    if isinstance(w, dict) and w.get("adr"):
                        w["adr"] = title_case_address(w["adr"])
                bsign = sess["data"].get("bsign")
                if isinstance(bsign, dict) and bsign.get("adr"):
                    bsign["adr"] = title_case_address(bsign["adr"])
                for p in sess["data"].get("ps", []):
                    if isinstance(p, dict):
                        if p.get("adr"):
                            p["adr"] = title_case_address(p["adr"])
                        if p.get("full_address"):
                            p["full_address"] = title_case_address(p["full_address"])

                # Normalize RM loan amount in words
                for l in sess["data"].get("ls", []):
                    if isinstance(l, dict) and l.get("w"):
                        l["w"] = normalize_amount_in_words(l["w"])
            
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

def save_case_session(case_id, data, files, verified_fields, bank, borrower_count, loan_count, properties_count="1", processed_files=None, doc_type=None, sellers_count=None, buyers_count=None, chain_scenario=None, selected_template=None, property_type=None, legal_report_files=None, buckets=None, **kwargs):
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
    
    # Preserve any unknown future/extra top-level keys from existing session
    for k, v in existing.items():
        if k not in session:
            session[k] = v

    # Store any extra kwargs passed to the save call
    for k, v in kwargs.items():
        session[k] = v

    if "data" in session and session["data"]:
        session["data"] = convert_hindi_digits_to_english(session["data"])
    path = os.path.join(CASES_DIR, case_id, "session.json")
    temp_path = path + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(session, f, ensure_ascii=False)
        os.replace(temp_path, path)
    except Exception as e:
        # Fallback to direct write if replace fails
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session, f, ensure_ascii=False)
    return session
