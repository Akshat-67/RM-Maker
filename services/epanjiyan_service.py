import re
import time
import datetime

# --- Address Splitting Helper ---
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
    
    # 1. Extract pincode (6 digits)
    pincode_match = re.search(r'\b\d{6}\b', address_str)
    pincode = pincode_match.group(0) if pincode_match else ""
    if pincode:
        address_str = address_str.replace(pincode, "").strip()
        
    address_str = re.sub(r'[\s,\.]+$', '', address_str)
    
    # 2. Extract and remove state name (case-insensitive)
    states = [
        "RAJASTHAN", "MAHARASHTRA", "GUJARAT", "MADHYA PRADESH", "UTTAR PRADESH", 
        "HARYANA", "PUNJAB", "DELHI", "KARNATAKA", "TAMIL NADU", "BIHAR", 
        "WEST BENGAL", "ANDHRA PRADESH", "TELANGANA", "GOA", "KERALA"
    ]
    detected_state = ""
    for state in states:
        pattern = r'\b' + re.escape(state) + r'\b'
        match = re.search(pattern, address_str, re.IGNORECASE)
        if match:
            detected_state = match.group(0).upper()
            address_str = re.sub(pattern, '', address_str, flags=re.IGNORECASE).strip()
            break
            
    # Clean state abbreviations
    address_str = re.sub(r'\b(rj|mh|gj|mp|up|hr|pb|dl|ka|tn|ap|ts)\b', '', address_str, flags=re.IGNORECASE).strip()
    address_str = re.sub(r'[\s,\.\-]+$', '', address_str)
    
    # Replace dots, colons, semicolons with spaces to clean special characters
    address_str = address_str.replace(".", " ").replace(":", " ").replace(";", " ")
    address_str = re.sub(r'\s+', ' ', address_str).strip()
    
    # 3. Extract house/flat number
    house_no = "00"
    
    # Check if address starts with a direct plot/house number (like "F N 115-A", "T-28", "101", "PLOT 12")
    start_match = re.match(r'^(?:FLAT|PLOT|HOUSE|SHOP|WARD|FN|NO|[A-Z](?=\s)|\s)*\s*([a-zA-Z0-9\-/]+)\b', address_str, re.IGNORECASE)
    if start_match and re.search(r'\d', start_match.group(0)) and len(start_match.group(1)) <= 8:
        house_no = start_match.group(1).upper()
        # Remove the matched prefix (including flat/plot keyword)
        address_str = address_str.replace(start_match.group(0), "", 1).strip()
    else:
        # Fallback keyword search
        house_match = re.search(r'\b(?:plot|p|h|flat|shop|house|ward)\b\.?\s*(?:no\.?|num\.?)?\s*([a-zA-Z0-9\-/]+)\b', address_str, re.IGNORECASE)
        if house_match:
            house_no = house_match.group(1).upper()
            address_str = address_str.replace(house_match.group(0), "").strip()
            
    # Clean up leading/trailing symbols in remaining address
    address_str = re.sub(r'^[\s,\.\-]+', '', address_str)
    address_str = re.sub(r'[\s,\.\-]+$', '', address_str)
    
    # 4. Extract common areas first to handle known localities
    common_areas = [
        "Jhotwara", "Mansarovar", "Sodala", "Malviya Nagar", "Vaishali Nagar", 
        "C-Scheme", "Raja Park", "Adarsh Nagar", "Bani Park", "Shastri Nagar", 
        "Vidhyadhar Nagar", "Pratap Nagar", "Sanganer", "Gopalpura", "Tonk Road", 
        "Jagatpura", "Patrakar Colony", "Nirman Nagar", "Civil Lines", "Ajmer Road", 
        "Sirsi Road", "Kalwar Road", "Agra Road", "Delhi Road", "Amer", "Chomu",
        "Prithviraj Nagar", "PRN", "Muhana", "Bhakrota", "Bindayaka"
    ]
    
    area = ""
    # Sort by length descending to match longer multi-word names first
    for a in sorted(common_areas, key=len, reverse=True):
        if re.search(r'\b' + re.escape(a) + r'\b', address_str, re.IGNORECASE):
            area = a.upper()
            address_str = re.sub(r'\b' + re.escape(a) + r'\b', '', address_str, flags=re.IGNORECASE).strip()
            break
            
    address_str = re.sub(r'^[\s,\.\-]+', '', address_str)
    address_str = re.sub(r'[\s,\.\-]+$', '', address_str)
    
    # 5. Split remaining address by commas to resolve city and colony
    parts = [p.strip() for p in address_str.split(",") if p.strip()]
    
    if not parts or len(parts) == 1:
        # Fallback split on space if no commas
        space_parts = [p.strip() for p in address_str.split() if p.strip()]
        if len(space_parts) >= 2:
            last_sp = space_parts[-1].upper()
            if last_sp in ["JAIPUR", "JODHPUR", "AJMER", "KOTA", "RAJASTHAN"]:
                parts = space_parts
    
    city = "JAIPUR"
    colony = ""
    
    if parts:
        last_part = parts[-1].upper()
        # Look for "DIST DISTRICT" patterns (e.g. "DIST JAIPUR" -> "JAIPUR")
        dist_match = re.search(r'\b(?:DIST|DISTRICT)\b\s*([A-Z\s]+)', last_part)
        if dist_match:
            city = dist_match.group(1).strip()
            parts = parts[:-1]
        else:
            city = last_part
            parts = parts[:-1]
            
    # Discard duplicate city/district names at the end
    while parts and (parts[-1].upper() == city or parts[-1].upper().replace("DIST", "").strip() == city):
        parts = parts[:-1]
        
    if not area:
        if len(parts) >= 1:
            area = parts[-1].upper()
            parts = parts[:-1]
        else:
            area = city
        
    if parts:
        # The remaining parts form the colony
        colony = ", ".join(parts).upper()
    else:
        colony = area
        
    if not colony:
        colony = city
        
    # Helper to clean up final returned fields from extra spaces/punctuation
    def clean_val(val):
        if not val:
            return ""
        # Remove any character that is NOT letter, number, space, dash, slash
        val = re.sub(r'[^a-zA-Z0-9\s\-/]', ' ', val)
        return re.sub(r'\s+', ' ', val).strip().upper()
        
    return {
        "house_no": clean_val(house_no),
        "colony": clean_val(colony),
        "area": clean_val(area),
        "city": clean_val(city),
        "pincode": pincode
    }


# --- Recent Cases Formatter ---
def format_recent_cases(cases):
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
    return recent


# --- E-Panjiyan Payload Generator ---
def generate_epanjiyan_payload(session):
    data = session.get("data", {})
    doc_type = session.get("doc_type", "RM")
    case_id = session.get("id", "")
    
    # Dynamically resolve SRO and Tehsil based on title chain or property details
    sro = "JAIPUR-VII"
    tehsil = "JAIPUR"
    
    # Override SRO/Tehsil with publicly matched SRO if available
    public_dlc = data.get("public_dlc_profile", {})
    if public_dlc and isinstance(public_dlc, dict) and public_dlc.get("sro"):
        sro = public_dlc.get("sro")
        if "-" in sro:
            tehsil = sro.split("-")[0]
        else:
            tehsil = sro
    
    city_map = {
        "जयपुर": "JAIPUR",
        "जोधपुर": "JODHPUR",
        "उदयपुर": "UDAIPUR",
        "कोटा": "KOTA",
        "बीकानेर": "BIKANER",
        "अजमेर": "AJMER",
        "अलवर": "ALWAR",
        "भरतपुर": "BHARATPUR",
        "भीलवाड़ा": "BHILWARA",
        "सीकर": "SIKAR",
        "झुंझुनू": "JHUNJHUNU"
    }
    
    chain = data.get("chain", []) or data.get("title_chain", [])
    resolved = False
    if chain and isinstance(chain, list):
        for event in reversed(chain):
            if not isinstance(event, dict): continue
            office = event.get("reg_office") or event.get("reg_office_en")
            if office:
                office_str = str(office).upper()
                detected_city = None
                for h_city, e_city in city_map.items():
                    if h_city in office_str or e_city in office_str:
                        detected_city = e_city
                        break
                
                detected_num = None
                roman_numerals = ["VIII", "VII", "III", "II", "IX", "VI", "IV", "V", "I", "X"]
                for rom in roman_numerals:
                    if re.search(r'\b' + rom + r'\b', office_str) or f"-{rom}" in office_str or f" {rom}" in office_str or f"_{rom}" in office_str or f"({rom})" in office_str:
                        detected_num = rom
                        break
                        
                if detected_city:
                    tehsil = detected_city
                    if detected_num:
                        sro = f"{detected_city}-{detected_num}"
                    else:
                        sro = detected_city
                    resolved = True
                    break
                    
    if not resolved:
        ps = data.get("ps", [])
        if ps and isinstance(ps, list) and isinstance(ps[0], dict):
            p_tehsil = ps[0].get("tehsil")
            p_dist = ps[0].get("dist")
            if p_dist:
                dist_clean = str(p_dist).strip().upper()
                for h_city, e_city in city_map.items():
                    if h_city in dist_clean or e_city in dist_clean:
                        tehsil = e_city
                        sro = e_city
                        break
            if p_tehsil:
                tehsil_clean = str(p_tehsil).strip().upper()
                for h_city, e_city in city_map.items():
                    if h_city in tehsil_clean or e_city in tehsil_clean:
                        tehsil = e_city
                        break
    
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
        
    is_sd = doc_type == "SD"
    
    executants_source = data.get("ss", []) if is_sd else data.get("bs", [])
    executants = []
    for b in executants_source:
        name_en = clean_val(b.get("n_en", "")) or clean_val(b.get("n", ""))
        rel_name_en = clean_val(b.get("rn_en", "")) or clean_val(b.get("rn", ""))
        
        sal = clean_val(b.get("s", ""))
        gender = "MALE"
        rel_type_val = clean_val(b.get("r", ""))
        is_female_rel = "पुत्री" in rel_type_val or "पत्नी" in rel_type_val or "W/O" in rel_type_val or "D/O" in rel_type_val or "WIFE" in rel_type_val or "DAUGHTER" in rel_type_val or "MOTHER" in rel_type_val or "WIDOW" in rel_type_val
        is_female_sal = "MRS" in sal or "MS" in sal or "FEMALE" in sal or "SMT" in sal or "KUMARI" in sal
        if is_female_sal or is_female_rel or clean_val(b.get("gender", "")) == "FEMALE":
            gender = "FEMALE"
            
        addr_str = clean_val(b.get("adr_en", "")) or clean_val(b.get("adr", ""))
        addr_split = split_address(addr_str)
        
        rel_type = clean_val(b.get("r", "S/O"))
        if "W/O" in rel_type or "WIFE" in rel_type:
            rel_type = "HUSBAND"
        else:
            rel_type = "FATHER"
            
        caste = clean_val(b.get("c", "General"))
        is_bpl = b.get("is_bpl") == "true" or b.get("is_bpl") is True
            
        executants.append({
            "name_en": name_en,
            "relation_type": rel_type,
            "relation_name_en": rel_name_en,
            "gender": gender,
            "caste": caste,
            "is_bpl": is_bpl,
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
    claimants = []
    if is_sd:
        buyers = data.get("bs", [])
        for b in buyers:
            buyer_name_en = clean_val(b.get("n_en", "")) or clean_val(b.get("n", ""))
            buyer_rel_name_en = clean_val(b.get("rn_en", "")) or clean_val(b.get("rn", ""))
            
            buyer_sal = clean_val(b.get("s", ""))
            buyer_gender = "MALE"
            buyer_rel_type_val = clean_val(b.get("r", ""))
            buyer_is_female_rel = "पुत्री" in buyer_rel_type_val or "पत्नी" in buyer_rel_type_val or "W/O" in buyer_rel_type_val or "D/O" in buyer_rel_type_val or "WIFE" in buyer_rel_type_val or "DAUGHTER" in buyer_rel_type_val or "MOTHER" in buyer_rel_type_val or "WIDOW" in buyer_rel_type_val
            buyer_is_female_sal = "MRS" in buyer_sal or "MS" in buyer_sal or "FEMALE" in buyer_sal or "SMT" in buyer_sal or "KUMARI" in buyer_sal
            if buyer_is_female_sal or buyer_is_female_rel or clean_val(b.get("gender", "")) == "FEMALE":
                buyer_gender = "FEMALE"
                
            buyer_addr_str = clean_val(b.get("adr_en", "")) or clean_val(b.get("adr", ""))
            buyer_addr_split = split_address(buyer_addr_str)
            
            buyer_rel_type = clean_val(b.get("r", "S/O"))
            if "W/O" in buyer_rel_type or "WIFE" in buyer_rel_type:
                buyer_rel_type = "HUSBAND"
            else:
                buyer_rel_type = "FATHER"
                
            c_data = {
                "name_en": buyer_name_en,
                "relation_type": buyer_rel_type,
                "relation_name_en": buyer_rel_name_en,
                "gender": buyer_gender,
                "age": clean_val(b.get("a", "")),
                "dob": clean_val(b.get("dob", "")),
                "aadhaar": clean_val(b.get("id", "")).replace(" ", ""),
                "pan": clean_val(b.get("pan", "")).replace(" ", ""),
                "address": {
                    "house_no": clean_val(buyer_addr_split["house_no"]),
                    "colony": clean_val(buyer_addr_split["colony"]),
                    "area": clean_val(buyer_addr_split["area"]),
                    "city": clean_val(buyer_addr_split["city"]),
                    "pincode": clean_val(buyer_addr_split["pincode"])
                }
            }
            claimants.append(c_data)
            
        if claimants:
            claimant = claimants[0]
    else:
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
        sig_name_en = clean_val(sig.get("n_en", "")) or clean_val(sig.get("n", ""))
        sig_rel_name_en = clean_val(sig.get("rn_en", "")) or clean_val(sig.get("rn", ""))
        
        sig_sal = clean_val(sig.get("s", ""))
        sig_gender = "MALE"
        if "MRS" in sig_sal or "MS" in sig_sal or "FEMALE" in sig_sal:
            sig_gender = "FEMALE"
            
        sig_addr_str = sig.get("adr_en", "") or sig.get("adr", "")
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
        w_name_en = clean_val(w.get("n_en", "")) or clean_val(w.get("n", ""))
        w_rel_name_en = clean_val(w.get("rn_en", "")) or clean_val(w.get("rn", ""))
        
        w_rel_type = clean_val(w.get("r", "S/O"))
        if "W/O" in w_rel_type or "WIFE" in w_rel_type:
            w_rel_type = "HUSBAND"
        else:
            w_rel_type = "FATHER"
            
        w_addr_str = clean_val(w.get("adr_en", "")) or clean_val(w.get("adr", ""))
        w_addr_split = split_address(w_addr_str)
        
        w_age = clean_val(w.get("a", ""))
        if not w_age:
            w_age = "35"
            
        w_sal = clean_val(w.get("s", ""))
        w_gender = "MALE"
        w_rel_type_val = clean_val(w.get("r", ""))
        w_is_female_rel = "पुत्री" in w_rel_type_val or "पत्नी" in w_rel_type_val or "W/O" in w_rel_type_val or "D/O" in w_rel_type_val or "WIFE" in w_rel_type_val or "DAUGHTER" in w_rel_type_val or "MOTHER" in w_rel_type_val or "WIDOW" in w_rel_type_val
        w_is_female_sal = "MRS" in w_sal or "MS" in w_sal or "FEMALE" in w_sal or "SMT" in w_sal or "KUMARI" in w_sal
        if w_is_female_sal or w_is_female_rel or clean_val(w.get("gender", "")) == "FEMALE":
            w_gender = "FEMALE"
            
        witnesses.append({
            "name_en": w_name_en,
            "relation_type": w_rel_type,
            "relation_name_en": w_rel_name_en,
            "gender": w_gender,
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
        p_addr_str = p.get("adr_en", "") or p.get("adr", "")
        p_addr_split = split_address(p_addr_str)
        properties.append({
            "address": {
                "house_no": clean_val(p_addr_split["house_no"]),
                "colony": clean_val(p_addr_split["colony"]),
                "area": clean_val(p_addr_split["area"]),
                "city": clean_val(p_addr_split["city"]),
                "pincode": clean_val(p_addr_split["pincode"])
            },
            "area": p.get("area") or p.get("land_area") or 0,
            "road_width": p.get("road_width", 30),
            "latitude": clean_val(p.get("lat") or "0"),
            "longitude": clean_val(p.get("lng") or "0"),
            "east": p.get("e_en") or p.get("e") or "",
            "west": p.get("w_en") or p.get("w") or "",
            "north": p.get("n_en") or p.get("n") or "",
            "south": p.get("s_en") or p.get("s") or ""
        })
        
    today_date = datetime.date.today().strftime("%d-%m-%Y")
    
    return {
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
        "claimants": claimants,
        "witnesses": witnesses,
        "properties": properties
    }
