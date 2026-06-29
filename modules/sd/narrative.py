# modules/sd/narrative.py

import re
from modules.sd.chain_templates import CHAIN_TEMPLATES, REGISTRATION_TEMPLATES
from modules.sd.extractor import SDDataExtractor

def deduplicate_chain(title_chain):
    """
    Remove duplicate events from title chain.
    Compare:
    * Registration Number (reg_no)
    * Parties (Executant and Claimant)
    * Property details
    * Deed Type (event_type or document_name)
    """
    unique_chain = []
    for evt in title_chain:
        is_dup = False
        reg_no = str(evt.get("reg_no", "")).strip()
        exec_name = str(evt.get("executant_name", "")).strip().lower()
        claim_name = str(evt.get("claimant_name", "")).strip().lower()
        event_type = str(evt.get("event_type", "")).strip().lower()
        doc_name = str(evt.get("document_name", "")).strip().lower()
        
        # Check against existing unique events
        for u_evt in unique_chain:
            u_reg_no = str(u_evt.get("reg_no", "")).strip()
            u_exec_name = str(u_evt.get("executant_name", "")).strip().lower()
            u_claim_name = str(u_evt.get("claimant_name", "")).strip().lower()
            u_event_type = str(u_evt.get("event_type", "")).strip().lower()
            u_doc_name = str(u_evt.get("document_name", "")).strip().lower()
            
            # 1. Registration Number Match (if non-empty)
            if reg_no and u_reg_no and reg_no == u_reg_no:
                is_dup = True
                break
                
            # 2. Parties and Deed Type Match
            type_matches = (event_type == u_event_type) or (doc_name and u_doc_name and doc_name == u_doc_name)
            
            parties_match = (
                (exec_name == u_exec_name or exec_name in u_exec_name or u_exec_name in exec_name) and
                (claim_name == u_claim_name or claim_name in u_claim_name or u_claim_name in claim_name)
            )
            
            if type_matches and parties_match:
                is_dup = True
                break
                
        if not is_dup:
            unique_chain.append(evt)
    return unique_chain

def generate_chain_narrative(title_chain, property_details=None, context=None):
    """
    Generate a formal Hindi title-chain narrative matching firm (ACTUAL.docx) style
    using a strict template engine.
    Returns a list of paragraphs.
    """
    # Normalize input title_chain so both database keys and UI keys are fully populated on each event
    normalized_chain = []
    if title_chain and isinstance(title_chain, list):
        for evt in title_chain:
            if not isinstance(evt, dict):
                normalized_chain.append(evt)
                continue
            
            c = evt.copy()
            # Aliasing UI keys to DB keys
            if "s" in c and (not c.get("executant_name") or not str(c["executant_name"]).strip()):
                c["executant_name"] = c["s"]
            if "b" in c and (not c.get("claimant_name") or not str(c["claimant_name"]).strip()):
                c["claimant_name"] = c["b"]
            if "d" in c and (not c.get("date") or not str(c["date"]).strip()):
                c["date"] = c["d"]
            if "b_no" in c and (not c.get("reg_book") or not str(c["reg_book"]).strip()):
                c["reg_book"] = c["b_no"]
            if "v_no" in c and (not c.get("reg_vol") or not str(c["reg_vol"]).strip()):
                c["reg_vol"] = c["v_no"]
            if "p_no" in c and (not c.get("reg_page") or not str(c["reg_page"]).strip()):
                c["reg_page"] = c["p_no"]
            if "r_no" in c and (not c.get("reg_no") or not str(c["reg_no"]).strip()):
                c["reg_no"] = c["r_no"]
            if "add_book" in c and (not c.get("reg_add_book") or not str(c["reg_add_book"]).strip()):
                c["reg_add_book"] = c["add_book"]
            
            # Reverse aliasing DB keys to UI keys (just in case)
            if "executant_name" in c and (not c.get("s") or not str(c["s"]).strip()):
                c["s"] = c["executant_name"]
            if "claimant_name" in c and (not c.get("b") or not str(c["b"]).strip()):
                c["b"] = c["claimant_name"]
            if "date" in c and (not c.get("d") or not str(c["d"]).strip()):
                c["d"] = c["date"]
            if "reg_book" in c and (not c.get("b_no") or not str(c["b_no"]).strip()):
                c["b_no"] = c["reg_book"]
            if "reg_vol" in c and (not c.get("v_no") or not str(c["v_no"]).strip()):
                c["v_no"] = c["reg_vol"]
            if "reg_page" in c and (not c.get("p_no") or not str(c["p_no"]).strip()):
                c["p_no"] = c["reg_page"]
            if "reg_no" in c and (not c.get("r_no") or not str(c["r_no"]).strip()):
                c["r_no"] = c["reg_no"]
            if "reg_add_book" in c and (not c.get("add_book") or not str(c["add_book"]).strip()):
                c["add_book"] = c["reg_add_book"]
            
            # Fallbacks for document_name / deed_type
            if "deed_type" in c and "document_name" not in c: c["document_name"] = c["deed_type"]
            if "document_name" in c and "deed_type" not in c: c["deed_type"] = c["document_name"]
            
            # Fallbacks for consideration_amount / amount
            if "amount" in c and "consideration_amount" not in c: c["consideration_amount"] = c["amount"]
            if "consideration_amount" in c and "amount" not in c: c["amount"] = c["consideration_amount"]

            normalized_chain.append(c)
        title_chain = normalized_chain

    # 1. Name cleaning helper for robust claimant/deceased matching
    def clean_name_for_matching(name):
        if not name:
            return ""
        n = str(name).lower()
        # Remove common prefixes and suffixes
        n = re.sub(r"\b(mr|mrs|miss|dr|shri|smt|late|स्व|स्वर्गीय|श्रीमती|श्री|मि|मिस्टर|मुसम्मात|मु|पत्नी|पुत्र|पुत्री)\b", "", n)
        # Remove parentheses, dots, commas, spaces
        n = re.sub(r"[\(\)\.\,\-\s]", "", n)
        return n

    # Determine if the main property is a flat or plot at the top
    is_flat = False
    if context and isinstance(context, dict) and context.get("property_type"):
        is_flat = (context.get("property_type") == "Flat")
    elif property_details:
        is_flat = bool(
            property_details.get("flat_no") 
            or property_details.get("building_name") 
            or property_details.get("floor")
            or "Unit" in str(property_details.get("property_portion", ""))
            or "फ्लैट" in str(property_details.get("plot_no", ""))
            or "Flat" in str(property_details.get("plot_no", ""))
        )

    # Universal helper to calculate chronological date key with undated death placement heuristic
    def get_event_date_key_universal(e, full_chain_list):
        evt_type = str(e.get("event_type") or "").strip().upper()
        doc_n = str(e.get("document_name") or e.get("deed_type") or "").strip().lower()
        
        is_death = (
            evt_type == "DEATH"
            or "उत्तराधिकार" in doc_n
            or "मृत्यु" in doc_n
            or "death" in doc_n
            or "succession" in doc_n
            or "heir" in doc_n
            or "वारिस" in doc_n
        )
        
        d_str = str(e.get("reg_date") or e.get("date") or "").replace("-", ".")
        
        if is_death and not d_str:
            # Undated succession/death event - run placement heuristic
            # Find the acquisition event where the deceased acquired the property
            deceased_name = str(e.get("executant_name") or "").strip()
            clean_dec = clean_name_for_matching(deceased_name)
            
            if clean_dec:
                latest_acq_key = None
                for other in full_chain_list:
                    # Skip other death/unregistered events to avoid cycles
                    other_type = str(other.get("event_type") or "").strip().upper()
                    other_doc = str(other.get("document_name") or other.get("deed_type") or "").strip().lower()
                    other_is_death = (
                        other_type == "DEATH"
                        or "उत्तराधिकार" in other_doc
                        or "मृत्यु" in other_doc
                        or "death" in other_doc
                    )
                    if other_is_death:
                        continue
                        
                    # Clean claimant name of the other event
                    clean_claimant = clean_name_for_matching(other.get("claimant_name"))
                    if clean_claimant and (clean_dec in clean_claimant or clean_claimant in clean_dec):
                        # Found an acquisition event! Get its date key
                        other_key = str(other.get("reg_date") or other.get("date") or "").replace("-", ".")
                        if other_key:
                            parts = other_key.split(".")
                            if len(parts) == 3:
                                day = parts[0].zfill(2)
                                month = parts[1].zfill(2)
                                year = parts[2]
                                key_val = f"{year}{month}{day}"
                                if not latest_acq_key or key_val > latest_acq_key:
                                    latest_acq_key = key_val
                                    
                if latest_acq_key:
                    # Sort immediately after the acquisition event (e.g. 19830907.1)
                    return f"{latest_acq_key}.1"
                    
            return "99.99.9999"

        if not d_str:
            return "99.99.9999"
            
        parts = d_str.split(".")
        if len(parts) == 3:
            day = parts[0].zfill(2)
            month = parts[1].zfill(2)
            year = parts[2]
            return f"{year}{month}{day}"
        return "99.99.9999"

    # 1. Filter out the current transaction and redundant deeds from the chain
    filtered_chain = []
    
    # Extract buyer names from context if available
    buyer_names = []
    if context and context.get("bs"):
        buyer_names = [b.get("n", "").strip().lower() for b in context["bs"] if b.get("n")]

    # Helper to calculate a temp date key for identifying the latest unregistered events
    def get_temp_date_key(e):
        return get_event_date_key_universal(e, title_chain)

    # Identify unregistered events at the end of the chronological chain
    unregistered_current_ids = set()
    if title_chain:
        sorted_temp = sorted(title_chain, key=get_temp_date_key)
        for evt in reversed(sorted_temp):
            is_reg = str(evt.get("is_registered") or "").strip().lower()
            evt_type = str(evt.get("event_type") or "").strip().upper()
            doc_n = str(evt.get("document_name") or evt.get("deed_type") or "").strip().lower()
            
            # Identify physical or non-transactional events (succession, construction)
            is_death_or_succession = (
                evt_type in ("DEATH", "CONSTRUCTION")
                or "उत्तराधिकार" in doc_n
                or "मृत्यु" in doc_n
                or "death" in doc_n
                or "succession" in doc_n
                or "heir" in doc_n
                or "वारिस" in doc_n
            )
            
            # If we hit a registered event, stop scanning backwards
            if is_reg == "true":
                break
                
            # If unregistered and not death/succession/construction, it is the current transaction under process
            if is_reg == "false" or not is_reg:
                if not is_death_or_succession:
                    unregistered_current_ids.add(id(evt))

    # Perform the filtering
    for evt in title_chain:
        claimant = evt.get("claimant_name", "").strip().lower()
        doc_name = str(evt.get("document_name") or evt.get("deed_type") or "").strip().lower()
        evt_type = str(evt.get("event_type") or "").strip().upper()
        
        is_current = False
        
        # Heuristic A: Claimant matches current buyer
        if claimant and buyer_names:
            for bn in buyer_names:
                if bn and (bn in claimant or claimant in bn):
                    is_current = True
                    break
                    
        # Heuristic B: Document name explicitly contains proposed/draft/agreement terms
        proposed_terms = ["proposed", "प्रस्तावित", "draft", "विक्रय समझौता", "agreement to sale", "इकरारनामा", "अनुबंध"]
        if not is_current:
            for term in proposed_terms:
                if term in doc_name:
                    is_current = True
                    break
                    
        # Heuristic C: Chronological end-of-chain unregistered event
        if not is_current and id(evt) in unregistered_current_ids:
            is_current = True
            
        if is_current:
            continue  # Filter out current transaction
            
        # Heuristic D: Redundant possession letters (always filter out)
        is_possession = (
            "possession" in doc_name 
            or "कब्जा" in doc_name 
            or "कब्ज़ा" in doc_name
            or "दखल" in doc_name
        )
        if is_possession:
            continue  # Filter out possession deeds
            
        # Heuristic E: Physical construction events on plots (filter out if not flat)
        is_construction_event = (
            evt_type == "CONSTRUCTION"
            or "construction" in doc_name
            or "निर्माण" in doc_name
        )
        if is_construction_event and not is_flat:
            continue  # Filter out construction events for plots
            
        filtered_chain.append(evt)

    # 2. Deduplicate events
    filtered_chain = deduplicate_chain(filtered_chain)

    # Auto-inject CONSTRUCTION event if missing for flat properties
    has_construction = any(e.get("event_type") == "CONSTRUCTION" for e in filtered_chain)
    if is_flat and not has_construction:
        # Sort other events chronologically first to find the first flat sale
        temp_other_evts = [e for e in filtered_chain if e.get("event_type") != "CONSTRUCTION"]
        
        def get_event_date_key_temp(e):
            return get_event_date_key_universal(e, filtered_chain)
            
        temp_other_evts.sort(key=get_event_date_key_temp)
        
        # Find the first event that is a flat sale (which has the builder as executant)
        builder_name = ""
        project_name = property_details.get("building_name") or property_details.get("project_name") or "मधुबन"
        
        for evt in temp_other_evts:
            src_txt = str(evt.get("source_text", "")).lower()
            doc_n = str(evt.get("document_name", "")).lower()
            is_flat_sale = (
                "flat" in src_txt or "unit" in src_txt or "apartment" in src_txt
                or "फ्लैट" in src_txt or "फ्लेट" in src_txt or "यूनिट" in src_txt or "अपार्टमेंट" in src_txt or "अपार्टमेन्ट" in src_txt
                or "फ्लेट" in doc_n or "फ्लैट" in doc_n
            )
            if is_flat_sale:
                builder_name = evt.get("executant_name", "")
                break
                
        if builder_name:
            injected_const = {
                "template_key": "CONSTRUCTION_FLAT",
                "event_type": "CONSTRUCTION",
                "executant_name": builder_name,
                "project_name": project_name,
                "document_name": "CONSTRUCTION",
                "is_registered": "false"
            }
            filtered_chain.append(injected_const)

    # 3. Chronological healing and builder executant resolution
    const_evts = [e for e in filtered_chain if e.get("event_type") == "CONSTRUCTION"]
    other_evts = [e for e in filtered_chain if e.get("event_type") != "CONSTRUCTION"]
    
    def get_event_date_key(e):
        return get_event_date_key_universal(e, filtered_chain)
        
    other_evts.sort(key=get_event_date_key)
    
    healed_chain = []
    construction_placed = False
    
    for evt in other_evts:
        src_txt = str(evt.get("source_text", "")).lower()
        doc_n = str(evt.get("document_name", "")).lower()
        is_flat_sale = (
            "flat" in src_txt or "unit" in src_txt or "apartment" in src_txt
            or "फ्लैट" in src_txt or "फ्लेट" in src_txt or "यूनिट" in src_txt or "अपार्टमेंट" in src_txt or "अपार्टमेन्ट" in src_txt
            or "फ्लेट" in doc_n or "फ्लैट" in doc_n
        )
        
        if is_flat_sale and const_evts and not construction_placed:
            for c_evt in const_evts:
                # Resolve executant of construction to the executant of the flat sale (builder)
                c_evt["executant_name"] = evt.get("executant_name", "")
                
                # Annotate field sources metadata for the construction event
                c_evt["field_sources"] = {
                    "event_type": {"classification": "EXTRACTED", "field_source": "tsr"},
                    "executant_name": {"classification": "INFERRED", "field_source": "chronology_healing"},
                    "claimant_name": {"classification": "EXTRACTED", "field_source": "tsr"},
                    "project_name": {
                        "classification": "INFERRED" if not c_evt.get("project_name") else "EXTRACTED",
                        "field_source": "property" if not c_evt.get("project_name") else "tsr"
                    },
                    "unit_number": {"classification": "EXTRACTED", "field_source": "tsr"}
                }
                healed_chain.append(c_evt)
            construction_placed = True
            
        healed_chain.append(evt)
        
    if const_evts and not construction_placed:
        for c_evt in const_evts:
            c_evt["field_sources"] = {
                "event_type": {"classification": "EXTRACTED", "field_source": "tsr"},
                "executant_name": {"classification": "EXTRACTED", "field_source": "tsr"},
                "claimant_name": {"classification": "EXTRACTED", "field_source": "tsr"},
                "project_name": {
                    "classification": "INFERRED" if not c_evt.get("project_name") else "EXTRACTED",
                    "field_source": "property" if not c_evt.get("project_name") else "tsr"
                },
                "unit_number": {"classification": "EXTRACTED", "field_source": "tsr"}
            }
            healed_chain.append(c_evt)
            
    filtered_chain = healed_chain

    if not filtered_chain:
        return []
    
    # Determine if the main property is a flat or plot
    is_flat = False
    if context and isinstance(context, dict) and context.get("property_type"):
        is_flat = (context.get("property_type") == "Flat")
    elif property_details:
        is_flat = bool(
            property_details.get("flat_no") 
            or property_details.get("building_name") 
            or property_details.get("floor")
            or "Unit" in str(property_details.get("property_portion", ""))
            or "फ्लैट" in str(property_details.get("plot_no", ""))
            or "Flat" in str(property_details.get("plot_no", ""))
        )

    # Determine event_property_type for each event in the healed chain
    const_idx = -1
    for i, e in enumerate(filtered_chain):
        if e.get("event_type") == "CONSTRUCTION":
            const_idx = i
            break
            
    # Force convert template keys to match the current property type
    if is_flat:
        key_map = {
            "ALLOTMENT_PLOT": "ALLOTMENT_FLAT",
            "ALLOTMENT_PLOT_NO_DEPOSIT": "ALLOTMENT_FLAT_NO_DEPOSIT",
            "ALLOTMENT_MUNICIPAL_PLOT": "ALLOTMENT_MUNICIPAL_FLAT",
            "SALE_DEED_PLOT": "SALE_DEED_FLAT",
            "TRANSFER_PLOT": "TRANSFER_FLAT"
        }
    else:
        key_map = {
            "ALLOTMENT_FLAT": "ALLOTMENT_PLOT",
            "ALLOTMENT_FLAT_NO_DEPOSIT": "ALLOTMENT_PLOT_NO_DEPOSIT",
            "ALLOTMENT_MUNICIPAL_FLAT": "ALLOTMENT_MUNICIPAL_PLOT",
            "SALE_DEED_FLAT": "SALE_DEED_PLOT",
            "TRANSFER_FLAT": "TRANSFER_PLOT"
        }

    for i, e in enumerate(filtered_chain):
        # Update template key if it matches the map
        old_key = e.get("template_key")
        if old_key in key_map:
            e["template_key"] = key_map[old_key]

        # Compute event_property_type dynamically based on the current is_flat setting
        if const_idx != -1 and i < const_idx:
            e["event_property_type"] = "PLOT"
        elif e.get("event_type") == "CONSTRUCTION":
            e["event_property_type"] = "FLAT"
        else:
            e["event_property_type"] = "FLAT" if const_idx != -1 else ("FLAT" if is_flat else "PLOT")
            
    paragraphs = []
    extractor = SDDataExtractor()
        
    for idx, evt in enumerate(filtered_chain):
        if not evt or not any(str(v).strip() for v in evt.values()):
            continue
            
        event_type = evt.get("event_type", "TRANSFER")
        doc_name = evt.get("document_name", "")
        # Coerce generic TRANSFER to SALE_DEED if document name indicates a sale/registry transaction
        doc_name_lower = doc_name.lower() if doc_name else ""
        exec_lower = str(evt.get("executant_name", "")).lower()
        if event_type == "TRANSFER" and any(x in doc_name_lower for x in ["sale", "deed", "विक्रय", "बैचान"]):
            event_type = "SALE_DEED"
        elif event_type == "TRANSFER" and (
            "मृतक" in exec_lower or "deceased" in exec_lower or "dead" in exec_lower or
            "उत्तराधिकार" in doc_name_lower or "succession" in doc_name_lower or
            "मृत्यु" in doc_name_lower or "death" in doc_name_lower
        ):
            event_type = "DEATH"
        # Coerce generic RELINQUISHMENT / TRANSFER to HAK_TYAG if it's a relinquishment/release deed event
        elif event_type in ["RELINQUISHMENT", "TRANSFER"] and (
            "रिलीज़" in doc_name_lower or "release" in doc_name_lower or
            "हकत्याग" in doc_name_lower or "relinquish" in doc_name_lower
        ):
            event_type = "HAK_TYAG"
        # Coerce generic TRANSFER to PARTITION if document name indicates a partition deed
        elif event_type == "TRANSFER" and (
            "partition" in doc_name_lower or "विभाजन" in doc_name_lower or
            "बंटवारा" in doc_name_lower or "बटवारा" in doc_name_lower
        ):
            event_type = "PARTITION"
        date = evt.get("date", "")
        executant = evt.get("executant_name", "")
        claimant = evt.get("claimant_name", "")
        amount = evt.get("consideration_amount", "")
        is_reg = str(evt.get("is_registered", "true")).lower() == "true"
        reg_office = evt.get("reg_office", "")
        reg_date = evt.get("reg_date", "")
        def coerce_book_number(val):
            if not val:
                return val
            val_str = str(val).strip()
            roman_map = {
                "I": "01", "II": "02", "III": "03", "IV": "04", "V": "05",
                "VI": "06", "VII": "07", "VIII": "08", "IX": "09", "X": "10"
            }
            upper_val = val_str.upper()
            if upper_val in roman_map:
                return roman_map[upper_val]
            if val_str.isdigit() and len(val_str) == 1:
                return f"0{val_str}"
            return val_str

        def normalize_registry_office(office_name):
            if not office_name:
                return office_name
            office_str = str(office_name).strip()
            # Clean hyphens before Roman/Arabic numerals at the end of the office name
            office_str = re.sub(r'-([IVX\d]+)$', r' \1', office_str, flags=re.IGNORECASE)
            # Replace hyphen between office type and city with a space (e.g., उप-पंजीयक-जयपुर -> उप-पंजीयक जयपुर)
            office_str = re.sub(r'उप-पंजीयक-([अ-ज्ञ])', r'उप-पंजीयक \1', office_str)
            
            roman_hindi_map = {
                "I": "प्रथम", "II": "द्वितीय", "III": "तृतीय", "IV": "चतुर्थ", "V": "पंचम्",
                "VI": "षष्ठम", "VII": "सप्तम", "VIII": "अष्टम", "IX": "नवम", "X": "दशम",
                "1": "प्रथम", "2": "द्वितीय", "3": "तृतीय", "4": "चतुर्थ", "5": "पंचम्",
                "6": "षष्ठम", "7": "सप्तम", "8": "अष्टम", "9": "नवम", "10": "दशम"
            }
            # Translate Roman or Arabic suffix
            match = re.search(r'\s+([IVX\d]+)$', office_str, re.IGNORECASE)
            if match:
                suffix = match.group(1).upper()
                if suffix in roman_hindi_map:
                    base = office_str[:match.start()].strip()
                    return f"{base} {roman_hindi_map[suffix]}"
            return office_str

        reg_office = normalize_registry_office(evt.get("reg_office", ""))
        reg_book = coerce_book_number(evt.get("reg_book", ""))
        reg_vol = evt.get("reg_vol", "")
        reg_page = evt.get("reg_page", "")
        reg_no = evt.get("reg_no", "")
        doc_no = evt.get("document_number", "")
        reg_add_book = coerce_book_number(evt.get("reg_add_book", ""))
        reg_add_vol = evt.get("reg_add_vol", "")
        reg_add_page = evt.get("reg_add_page", "")
        evt_proj_name = evt.get("project_name", "")

        # New fields
        receipt_no = evt.get("receipt_no", "")
        receipt_date = evt.get("receipt_date", "")
        khata_no = evt.get("khata_no", "")
        khasra_no = evt.get("khasra_no", "")
        rakba = evt.get("rakba", "")
        share_fraction = evt.get("share_fraction", "")
        wife_name = evt.get("wife_name", "")
        wife_death_date = evt.get("wife_death_date", "")
        husband_name = evt.get("husband_name", "")
        husband_death_date = evt.get("husband_death_date", "")
        east_owner = evt.get("east_owner", "")
        west_owner = evt.get("west_owner", "")
        co_owner = evt.get("co_owner", "")
        parent_property_info = evt.get("parent_property_info", "")
        owner_name = evt.get("owner_name", "")
        will_type = evt.get("will_type", "नोटेरीशुदा") or "नोटेरीशुदा"
        death_date = evt.get("death_date", "")
        extra_deaths_text = evt.get("extra_deaths_text", "")

        # Count heirs and calculate share_fraction dynamically if missing
        if not share_fraction and event_type == "DEATH":
            if claimant:
                # Split by commas or 'एवं' / 'तथा' / 'और' or newlines
                raw_parts = re.split(r'[,，\n]|(?:\s+एवं\s+|\s+तथा\s+|\s+और\s+)', claimant)
                valid_heirs = []
                for p in raw_parts:
                    p_clean = re.sub(r'^\d+[\s\.]*', '', p.strip()) # strip numbering like 1.
                    p_clean = p_clean.strip()
                    if p_clean and len(p_clean) > 1:
                        valid_heirs.append(p_clean)
                count = len(valid_heirs)
                if count > 0:
                    share_fraction = f"1/{count}"

        # Dynamic heirs formatting for DEATH events
        if event_type == "DEATH" and claimant:
            # Format the claimant as a numbered list with parentage if not already formatted
            raw_parts = re.split(r'[,，\n]|(?:\s+एवं\s+|\s+तथा\s+|\s+और\s+)', claimant)
            raw_parts = [p.strip() for p in raw_parts if p.strip() and len(p.strip()) > 1]
            if raw_parts and not any(re.match(r'^\d+[\s\.]+', p) for p in raw_parts):
                formatted_heirs = []
                # Clean deceased name for parentage (remove "मृतक" or "deceased" tags)
                parent_name = re.sub(r'\s*\([\s\w]*मृतक[\s\w]*\)', '', executant).strip()
                parent_name = re.sub(r'\s*\([\s\w]*deceased[\s\w]*\)', '', parent_name, flags=re.IGNORECASE).strip()
                # Translate Mr/Mrs prefix of parent to respectful श्री
                parent_name = parent_name.replace("मि.", "श्री").replace("Mr.", "श्री").replace("mr.", "श्री")
                if not parent_name.startswith("श्री") and not parent_name.startswith("श्रीमती"):
                    parent_name = f"श्री {parent_name}"
                
                idx_heir = 1
                for p in raw_parts:
                    p_clean = p.strip()
                    # Check gender of heir to use पुत्र or पुत्री
                    relation_term = "पुत्र"
                    female_keywords = ["श्रीमती", "कुमारी", "रिहान", "रिहियान", "wife", "daughter", "mrs.", "miss", "shrimati"]
                    if any(kw in p_clean.lower() for kw in female_keywords):
                        relation_term = "पुत्री"
                    
                    # Ensure respect prefix श्री / श्रीमती on heir and replace मि. / Mr.
                    heir_name = p_clean
                    if relation_term == "पुत्री":
                        if not heir_name.startswith("श्रीमती") and not heir_name.startswith("कुमारी"):
                            if heir_name.startswith("मि."):
                                heir_name = heir_name.replace("मि.", "श्रीमती")
                            elif heir_name.startswith("Mrs."):
                                heir_name = heir_name.replace("Mrs.", "श्रीमती")
                            else:
                                heir_name = f"श्रीमती {heir_name}"
                    else:
                        if not heir_name.startswith("श्री") and not heir_name.startswith("मि.") and not heir_name.startswith("Mr."):
                            heir_name = f"श्री {heir_name}"
                        elif heir_name.startswith("मि."):
                            heir_name = heir_name.replace("मि.", "श्री")
                        elif heir_name.startswith("Mr."):
                            heir_name = heir_name.replace("Mr.", "श्री")
                    
                    formatted_heirs.append(f"{idx_heir}. {heir_name} {relation_term} {parent_name}")
                    idx_heir += 1
                
                if formatted_heirs:
                    claimant = ", ".join(formatted_heirs)
        # Dynamic heirs formatting for HAK_TYAG events
        if event_type == "HAK_TYAG" and executant:
            raw_parts = re.split(r'[,，\n]|(?:\s+एवं\s+|\s+तथा\s+|\s+और\s+)', executant)
            raw_parts = [p.strip() for p in raw_parts if p.strip() and len(p.strip()) > 1]
            if raw_parts and not any(re.match(r'^\d+[\s\.]+', p) for p in raw_parts):
                # Find deceased parent name from the chain
                parent_name = ""
                for prev_evt in filtered_chain:
                    prev_exec = str(prev_evt.get("executant_name", ""))
                    prev_doc = str(prev_evt.get("document_name", "")).lower()
                    if prev_evt.get("event_type") == "DEATH" or "मृतक" in prev_exec or "उत्तराधिकार" in prev_doc:
                        parent_name = re.sub(r'\s*\([\s\w]*मृतक[\s\w]*\)', '', prev_evt.get("executant_name", "")).strip()
                        parent_name = re.sub(r'\s*\([\s\w]*deceased[\s\w]*\)', '', parent_name, flags=re.IGNORECASE).strip()
                        parent_name = parent_name.replace("मि.", "श्री").replace("Mr.", "श्री").replace("mr.", "श्री")
                        break
                if not parent_name:
                    parent_name = "श्री मोहम्मद हनीफ"
                if not parent_name.startswith("श्री") and not parent_name.startswith("श्रीमती"):
                    parent_name = f"श्री {parent_name}"
                
                # Group into males and females
                males = []
                females = []
                for p in raw_parts:
                    p_clean = p.strip()
                    is_female = False
                    female_keywords = ["श्रीमती", "कुमारी", "रिहान", "रिहियान", "wife", "daughter", "mrs.", "miss", "shrimati"]
                    if any(kw in p_clean.lower() for kw in female_keywords):
                        is_female = True
                    
                    heir_name = p_clean
                    if is_female:
                        if not heir_name.startswith("श्रीमती") and not heir_name.startswith("कुमारी"):
                            if heir_name.startswith("मि."):
                                heir_name = heir_name.replace("मि.", "श्रीमती")
                            elif heir_name.startswith("Mrs."):
                                heir_name = heir_name.replace("Mrs.", "श्रीमती")
                            else:
                                heir_name = f"श्रीमती {heir_name}"
                        females.append(heir_name)
                    else:
                        if not heir_name.startswith("श्री") and not heir_name.startswith("मि.") and not heir_name.startswith("Mr."):
                            heir_name = f"श्री {heir_name}"
                        elif heir_name.startswith("मि."):
                            heir_name = heir_name.replace("मि.", "श्री")
                        elif heir_name.startswith("Mr."):
                            heir_name = heir_name.replace("Mr.", "श्री")
                        males.append(heir_name)
                
                formatted_parts = []
                idx_heir = 1
                # Format males
                if males:
                    if len(males) > 1:
                        male_list = ", ".join(f"{idx_heir + i}. {males[i]}" for i in range(len(males)))
                        formatted_parts.append(f"{male_list} पुत्रान् स्व. {parent_name}")
                        idx_heir += len(males)
                    else:
                        formatted_parts.append(f"{idx_heir}. {males[0]} पुत्र स्व. {parent_name}")
                        idx_heir += 1
                # Format females
                if females:
                    for f in females:
                        formatted_parts.append(f"{idx_heir}. {f} पुत्री स्व. {parent_name}")
                        idx_heir += 1
                
                if formatted_parts:
                    executant = ", ".join(formatted_parts)
        
        # Format claimant parentage for HAK_TYAG
        if event_type == "HAK_TYAG" and claimant:
            if "पुत्र" not in claimant and "पुत्री" not in claimant:
                # Find deceased parent name
                parent_name = ""
                for prev_evt in filtered_chain:
                    prev_exec = str(prev_evt.get("executant_name", ""))
                    prev_doc = str(prev_evt.get("document_name", "")).lower()
                    if prev_evt.get("event_type") == "DEATH" or "मृतक" in prev_exec or "उत्तराधिकार" in prev_doc:
                        parent_name = re.sub(r'\s*\([\s\w]*मृतक[\s\w]*\)', '', prev_evt.get("executant_name", "")).strip()
                        parent_name = re.sub(r'\s*\([\s\w]*deceased[\s\w]*\)', '', parent_name, flags=re.IGNORECASE).strip()
                        parent_name = parent_name.replace("मि.", "श्री").replace("Mr.", "श्री").replace("mr.", "श्री")
                        break
                if not parent_name:
                    parent_name = "श्री मोहम्मद हनीफ"
                if not parent_name.startswith("श्री") and not parent_name.startswith("श्रीमती"):
                    parent_name = f"श्री {parent_name}"
                
                # Check gender of claimant
                relation_term = "पुत्र"
                female_keywords = ["श्रीमती", "कुमारी", "रिहान", "रिहियान", "wife", "daughter", "mrs.", "miss", "shrimati"]
                if any(kw in claimant.lower() for kw in female_keywords):
                    relation_term = "पुत्री"
                
                # Standardize respect prefix
                claimant_clean = claimant.strip()
                if relation_term == "पुत्री":
                    if not claimant_clean.startswith("श्रीमती") and not claimant_clean.startswith("कुमारी"):
                        if claimant_clean.startswith("मि."):
                            claimant_clean = claimant_clean.replace("मि.", "श्रीमती")
                        else:
                            claimant_clean = f"श्रीमती {claimant_clean}"
                else:
                    if not claimant_clean.startswith("श्री") and not claimant_clean.startswith("मि.") and not claimant_clean.startswith("Mr."):
                        claimant_clean = f"श्री {claimant_clean}"
                    elif claimant_clean.startswith("मि."):
                        claimant_clean = claimant_clean.replace("मि.", "श्री")
                    elif claimant_clean.startswith("Mr."):
                        claimant_clean = claimant_clean.replace("Mr.", "श्री")
                
                claimant = f"{claimant_clean} पुत्र स्व. {parent_name}" if relation_term == "पुत्र" else f"{claimant_clean} पुत्री स्व. {parent_name}"

        prefix = "यह कि सर्वप्रथम " if idx == 0 else "तत्पश्चात् "
        
        # default owner suffix
        is_joint = False
        if claimant and ("एवं" in claimant or "तथा" in claimant or "," in claimant):
            is_joint = True
            
        is_female = False
        if claimant:
            female_keywords = ["श्रीमती", "पत्नी", "पत्नि", "श्रीमती.", "wife", "w/o", "d/o", "daughter", "mrs."]
            if any(kw in claimant.lower() for kw in female_keywords):
                is_female = True

        if is_joint:
            owner_suffix = "संयुक्तरूप से मालिक, स्वामी व अधिकारी हुए।"
        elif is_female:
            owner_suffix = "एकमात्र मालिक, स्वामी व अधिकारी हुई।"
        else:
            owner_suffix = "एकमात्र मालिक, स्वामी व अधिकारी हुए।"

        # --- Prepare context variables for template ---
        ctx = {
            "prefix": prefix,
            "executant": executant,
            "claimant": claimant,
            "date": date,
            "document_name": doc_name or "विक्रय-पत्र",
            "document_number": doc_no,
            "document_no": doc_no or "",
            "amount": amount,
            "reg_office": reg_office,
            "reg_date": reg_date,
            "reg_book": reg_book,
            "reg_vol": reg_vol,
            "reg_page": reg_page,
            "reg_no": reg_no,
            "reg_add_book": reg_add_book,
            "reg_add_vol": reg_add_vol,
            "reg_add_page": reg_add_page,
            "book_no": evt.get("book_no", reg_book),
            "volume_no": evt.get("volume_no", reg_vol),
            "page_no": evt.get("page_no", reg_page),
            "additional_book_no": evt.get("additional_book_no", reg_add_book),
            "additional_volume_no": evt.get("additional_volume_no", reg_add_vol),
            "additional_page_range": evt.get("additional_page_range", reg_add_page),
            "project_name": evt_proj_name,
            "full_address": "",
            "dimension_text": "",
            "boundary_text": "",
            "total_area": property_details.get("land_area", "183.33") if property_details else "183.33",
            "area_unit": property_details.get("unit", "वर्गगज") if property_details else "वर्गगज",
            "amount_str": "",
            "document_name_str": "",
            "reg_details": "",
            "document_number_phrase": "",
            # New context variables
            "receipt_no": receipt_no,
            "receipt_date": receipt_date,
            "khata_no": khata_no,
            "khasra_no": khasra_no,
            "rakba": rakba,
            "share_fraction": share_fraction,
            "wife_name": wife_name,
            "wife_death_date": wife_death_date,
            "husband_name": husband_name,
            "husband_death_date": husband_death_date,
            "east_owner": east_owner,
            "west_owner": west_owner,
            "co_owner": co_owner,
            "parent_property_info": parent_property_info,
            "owner_name": owner_name,
            "owner_suffix": owner_suffix,
            "will_type": will_type,
            "death_date": death_date,
            "extra_deaths_text": extra_deaths_text,
            
            # Micro-level property detail placeholders
            "east_to_west": property_details.get("length_ew", "") if property_details else "",
            "north_to_south": property_details.get("length_ns", "") if property_details else "",
            "boundary_east": property_details.get("e", "") if property_details else "",
            "boundary_west": property_details.get("w", "") if property_details else "",
            "boundary_north": property_details.get("n", "") if property_details else "",
            "boundary_south": property_details.get("s", "") if property_details else "",
            "authority_name": executant or "जेडीए, जयपुर",
            
            # Double registration and other specific defaults to avoid KeyErrors
            "possession_no": evt.get("possession_no", ""),
            "possession_date": evt.get("possession_date", ""),
            "nodues_date": evt.get("nodues_date", ""),
            "lease_date": evt.get("lease_date", ""),
            "conveyance_date": evt.get("conveyance_date", ""),
            "reg_add_serial": evt.get("reg_add_serial", ""),
            "conv_reg_book": evt.get("conv_reg_book", ""),
            "conv_reg_vol": evt.get("conv_reg_vol", ""),
            "conv_reg_page": evt.get("conv_reg_page", ""),
            "conv_reg_no": evt.get("conv_reg_no", ""),
            "conv_reg_add_book": evt.get("conv_reg_add_book", ""),
            "conv_reg_add_vol": evt.get("conv_reg_add_vol", ""),
            "conv_reg_add_serial": evt.get("conv_reg_add_serial", ""),
            "conv_reg_add_page_start": "",
            "conv_reg_add_page_end": "",
            "reg_add_page_start": "",
            "reg_add_page_end": ""
        }
        
        # Additional logic for Allotment document numbers
        if doc_no:
            ctx["document_number_phrase"] = f" संख्या {doc_no}"
        else:
            ctx["document_number_phrase"] = ""

        # Format Property/Address/Boundary details for ALLOTMENT using clean helper methods
        if (event_type in ["ALLOTMENT", "AGRICULTURAL_ALLOTMENT"]) and property_details:
            p_type = str(evt.get("event_property_type", "Plot")).title()
            ctx["full_address"] = extractor.generate_full_property_address(property_details, "SD", p_type)
            
            # Retrieve dimension text and boundary text
            dim_str = extractor.generate_dimension_text(property_details)
            # Remove trailing period if present and replace with a comma to keep grammar valid
            if dim_str.endswith("।"):
                dim_str = dim_str[:-1].strip() + ","
            elif dim_str.endswith("."):
                dim_str = dim_str[:-1].strip() + ","
            ctx["dimension_text"] = dim_str
            
            ctx["boundary_text"] = extractor.generate_boundary_text(property_details)

        # 1. Deterministic consideration fallback
        if amount and str(amount).strip():
            # Format number with commas for amount if it doesn't have them
            amt_digits = re.sub(r'[^\d]', '', str(amount))
            if amt_digits:
                try:
                    formatted_amount = "{:,}".format(int(amt_digits))
                except:
                    formatted_amount = amount
            else:
                formatted_amount = amount
            ctx["amount_str"] = f"के प्रतिफल राश्िा {formatted_amount}/- रूपये में "
        else:
            ctx["amount_str"] = ""

        # 2. Document name & number formatting
        if event_type == "ALLOTMENT":
            verb_doc = doc_name or "पट्टा-विलेख/ आवंटन/विक्रय-पत्र"
            ctx["document_name"] = verb_doc
            ctx["document_name_str"] = verb_doc
        else:
            verb_doc = doc_name or "विक्रय-पत्र"
            if is_reg and not any(k in verb_doc for k in ["पंजीकृत", "पंजीकत"]):
                ctx["document_name_str"] = f"पंजीकृत {verb_doc}"
            else:
                ctx["document_name_str"] = verb_doc

        # 3. Deterministic Registration details fallback
        # If reg_no is missing, we omit registration details entirely
        if is_reg and reg_no and str(reg_no).strip():
            # Build office phrase
            if reg_office and str(reg_office).strip():
                office_clean = reg_office.strip()
                if event_type == "ALLOTMENT":
                    if office_clean.startswith("कार्यालय"):
                        office_phrase = f"{office_clean} के यहां "
                    else:
                        office_phrase = f"कार्यालय {office_clean} के यहां "
                else:
                    if "उप-पंजीयक कार्यालय" in office_clean or "उप पंजीयक कार्यालय" in office_clean:
                        office_phrase = f"{office_clean} के यहां "
                    elif "उप-पंजीयक" in office_clean or "उप पंजीयक" in office_clean:
                        t = office_clean.replace("उप-पंजीयक", "उप-पंजीयक कार्यालय").replace("उप पंजीयक", "उप-पंजीयक कार्यालय")
                        office_phrase = f"{t} के यहां "
                    elif "कार्यालय" in office_clean:
                        office_phrase = f"{office_clean} के यहां "
                    else:
                        office_phrase = f"उप-पंजीयक कार्यालय {office_clean} के यहां "
                
                # Cleanup any duplicates
                office_phrase = office_phrase.replace("कार्यालय कार्यालय", "कार्यालय")
                office_phrase = office_phrase.replace("उप-पंजीयक कार्यालय उप-पंजीयक कार्यालय", "उप-पंजीयक कार्यालय")
            else:
                office_phrase = ""
            
            # Build date phrase
            if reg_date and str(reg_date).strip():
                date_phrase = f"दिनांक {reg_date} को "
            else:
                date_phrase = ""
                
            # Build additional page details if present
            reg_add_page_str = ""
            reg_add_page_start = ""
            reg_add_page_end = ""
            if reg_add_page and str(reg_add_page).strip():
                normalized_page = str(reg_add_page).strip()
                normalized_page = re.sub(r'\s+(?:to|से|and)\s+', '-', normalized_page, flags=re.IGNORECASE)
                if "-" in normalized_page:
                    start_p, end_p = normalized_page.split("-", 1)
                    reg_add_page_str = f"के पृष्ठ संख्या {start_p.strip()} से {end_p.strip()}"
                    reg_add_page_start = start_p.strip()
                    reg_add_page_end = end_p.strip()
                else:
                    reg_add_page_str = f"के पृष्ठ संख्या {normalized_page}"
                    reg_add_page_start = normalized_page
                    reg_add_page_end = normalized_page
            
            ctx["reg_add_page_start"] = reg_add_page_start
            ctx["reg_add_page_end"] = reg_add_page_end
            ctx["conv_reg_add_page_start"] = reg_add_page_start  # Fallback
            ctx["conv_reg_add_page_end"] = reg_add_page_end      # Fallback
                    
            # Additional book details
            if reg_add_book and reg_add_vol:
                add_details = f"तथा अतिरिक्त पुस्तक संख्या {reg_add_book} जिल्द संख्या {reg_add_vol} {reg_add_page_str} पर चस्पा किया गया।"
            else:
                add_details = ""
                
            reg_tpl_name = "ALLOTMENT" if event_type == "ALLOTMENT" else "GENERAL"
            reg_tpl = REGISTRATION_TEMPLATES.get(reg_tpl_name, "")
            
            # Build details dynamically
            ctx["office_phrase"] = office_phrase
            ctx["date_phrase"] = date_phrase
            ctx["reg_add_page_str"] = reg_add_page_str
            
            # Format reg template
            reg_text = reg_tpl.format(**ctx)
            if not add_details and "तथा अतिरिक्त पुस्तक संख्या" in reg_text:
                reg_text = re.sub(r'तथा अतिरिक्त पुस्तक संख्या.*$', '', reg_text).strip()
                if not reg_text.endswith("।"):
                    reg_text += "।"
            ctx["reg_details"] = reg_text + " "
        else:
            ctx["reg_details"] = ""

        # --- Template Key Selection ---
        explicit_tpl_key = evt.get("template_key")
        evt_is_flat = (evt.get("event_property_type", "FLAT" if is_flat else "PLOT") == "FLAT")
        
        if explicit_tpl_key and explicit_tpl_key in CHAIN_TEMPLATES:
            tpl_key = explicit_tpl_key
        else:
            tpl_key = event_type
            if event_type == "SALE_DEED":
                if share_fraction:
                    tpl_key = "PART_SALE"
                else:
                    tpl_key = "SALE_DEED_FLAT" if evt_is_flat else "SALE_DEED_PLOT"
            elif event_type == "TRANSFER":
                tpl_key = "TRANSFER_FLAT" if evt_is_flat else "TRANSFER_PLOT"
            elif event_type == "ALLOTMENT":
                doc_n_lower = str(doc_name or "").lower()
                # Detect if it's a municipal / authority / committee allotment
                exec_lower = str(executant or "").lower()
                is_municipal = any(x in exec_lower for x in ["नगर निगम", "नगरनिगम", "विकास प्राधिकरण", "samiti", "समिति", "jda", "जेडीए", "uit", "यूआईटी"])
                
                if "lease" in doc_n_lower or "लीज" in doc_n_lower:
                    tpl_key = "LEASE_DEED"
                elif receipt_no:
                    tpl_key = "ALLOTMENT_SOCIETY"
                elif is_municipal:
                    tpl_key = "ALLOTMENT_MUNICIPAL_FLAT" if evt_is_flat else "ALLOTMENT_MUNICIPAL_PLOT"
                else:
                    has_dep = bool(claimant and executant)
                    if evt_is_flat:
                        tpl_key = "ALLOTMENT_FLAT" if has_dep else "ALLOTMENT_FLAT_NO_DEPOSIT"
                    else:
                        tpl_key = "ALLOTMENT_PLOT" if has_dep else "ALLOTMENT_PLOT_NO_DEPOSIT"
            elif event_type == "WILL":
                tpl_key = "WILL"
            elif event_type == "CONSTRUCTION":
                tpl_key = "CONSTRUCTION_FLAT" if ctx["project_name"] else "CONSTRUCTION_FLAT_NO_NAME"
            elif event_type == "DEATH":
                if east_owner or west_owner:
                    tpl_key = "DEATH_DIVIDED"
                elif wife_name or husband_name:
                    tpl_key = "DEATH_HEIRS_WITH_SPOUSE"
                else:
                    tpl_key = "DEATH_HEIRS_SINGLE"
            elif event_type == "HAK_TYAG":
                tpl_key = "HAK_TYAG"
            elif event_type == "POA":
                if khasra_no:
                    tpl_key = "POA_AGRICULTURAL"
                else:
                    tpl_key = "POA_NON_AGRICULTURAL"
            elif event_type == "DEVELOPER_AGREEMENT":
                tpl_key = "DEVELOPER_AGREEMENT"
            elif event_type == "GIFT_DEED":
                tpl_key = "GIFT_DEED"
            elif event_type == "TRANSFER_CERTIFICATE":
                tpl_key = "TRANSFER_CERTIFICATE"
            elif event_type == "COLONY_DEVELOPMENT":
                tpl_key = "COLONY_DEVELOPMENT"
            elif event_type == "AGRICULTURAL_ALLOTMENT":
                tpl_key = "AGRICULTURAL_ALLOTMENT"
            
        if tpl_key not in CHAIN_TEMPLATES:
            tpl_key = "TRANSFER_FLAT" if evt_is_flat else "TRANSFER_PLOT"
            
        template = CHAIN_TEMPLATES[tpl_key]
        formatted_para = template.format(**ctx)
        
        # Clean up double spaces or dangling commas
        formatted_para = re.sub(r'\s+,\s+', ', ', formatted_para)
        formatted_para = re.sub(r'\s+', ' ', formatted_para).strip()
        
        paragraphs.append(formatted_para)

    return paragraphs
