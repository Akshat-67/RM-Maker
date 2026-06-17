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
    # 1. Filter out the current transaction from the chain
    filtered_chain = []
    if context and context.get("bs"):
        buyer_names = [b.get("n", "").strip().lower() for b in context["bs"] if b.get("n")]
        
        for evt in title_chain:
            claimant = evt.get("claimant_name", "").strip().lower()
            is_current = False
            if claimant:
                for bn in buyer_names:
                    if bn and (bn in claimant or claimant in bn):
                        is_current = True
                        break
            if not is_current:
                filtered_chain.append(evt)
    else:
        filtered_chain = title_chain

    # 2. Deduplicate events
    filtered_chain = deduplicate_chain(filtered_chain)

    # 3. Chronological healing and builder executant resolution
    const_evts = [e for e in filtered_chain if e.get("event_type") == "CONSTRUCTION"]
    other_evts = [e for e in filtered_chain if e.get("event_type") != "CONSTRUCTION"]
    
    def get_event_date_key(e):
        d_str = str(e.get("date", "")).replace("-", ".")
        if not d_str:
            return "99.99.9999"
        parts = d_str.split(".")
        if len(parts) == 3:
            # Ensure 2 digits for day/month
            day = parts[0].zfill(2)
            month = parts[1].zfill(2)
            year = parts[2]
            return f"{year}{month}{day}"
        return "99.99.9999"
        
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
    if property_details:
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
            
    for i, e in enumerate(filtered_chain):
        # Allow pre-existing event_property_type if set, else compute it dynamically
        if e.get("event_property_type"):
            continue
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
        date = evt.get("date", "")
        executant = evt.get("executant_name", "")
        claimant = evt.get("claimant_name", "")
        amount = evt.get("consideration_amount", "")
        is_reg = str(evt.get("is_registered", "true")).lower() == "true"
        reg_office = evt.get("reg_office", "")
        reg_date = evt.get("reg_date", "")
        reg_book = evt.get("reg_book", "")
        reg_vol = evt.get("reg_vol", "")
        reg_page = evt.get("reg_page", "")
        reg_no = evt.get("reg_no", "")
        doc_no = evt.get("document_number", "")
        reg_add_book = evt.get("reg_add_book", "")
        reg_add_vol = evt.get("reg_add_vol", "")
        reg_add_page = evt.get("reg_add_page", "")
        evt_proj_name = evt.get("project_name", "")

        prefix = "यह कि सर्वप्रथम " if idx == 0 else "तत्पश्चात् "
        
        # --- Prepare context variables for template ---
        ctx = {
            "prefix": prefix,
            "executant": executant,
            "claimant": claimant,
            "date": date,
            "document_name": doc_name or "विक्रय-पत्र",
            "document_number": doc_no,
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
            "document_number_phrase": ""
        }
        
        # Additional logic for Allotment document numbers
        if doc_no:
            ctx["document_number_phrase"] = f" संख्या {doc_no}"
        else:
            ctx["document_number_phrase"] = ""

        # Format Property/Address/Boundary details for ALLOTMENT using clean helper methods
        if event_type == "ALLOTMENT" and property_details:
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
            if reg_add_page and str(reg_add_page).strip():
                normalized_page = str(reg_add_page).strip()
                normalized_page = re.sub(r'\s+(?:to|से|and)\s+', '-', normalized_page, flags=re.IGNORECASE)
                if "-" in normalized_page:
                    start_p, end_p = normalized_page.split("-", 1)
                    reg_add_page_str = f"के पृष्ठ संख्या {start_p.strip()} से {end_p.strip()}"
                else:
                    reg_add_page_str = f"के पृष्ठ संख्या {normalized_page}"
                    
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
        tpl_key = event_type
        evt_is_flat = (evt.get("event_property_type", "FLAT" if is_flat else "PLOT") == "FLAT")
        if event_type == "SALE_DEED":
            tpl_key = "SALE_DEED_FLAT" if evt_is_flat else "SALE_DEED_PLOT"
        elif event_type == "TRANSFER":
            tpl_key = "TRANSFER_FLAT" if evt_is_flat else "TRANSFER_PLOT"
        elif event_type == "ALLOTMENT":
            has_dep = bool(claimant and executant)
            if evt_is_flat:
                tpl_key = "ALLOTMENT_FLAT" if has_dep else "ALLOTMENT_FLAT_NO_DEPOSIT"
            else:
                tpl_key = "ALLOTMENT_PLOT" if has_dep else "ALLOTMENT_PLOT_NO_DEPOSIT"
        elif event_type == "CONSTRUCTION":
            tpl_key = "CONSTRUCTION_FLAT" if ctx["project_name"] else "CONSTRUCTION_FLAT_NO_NAME"
            
        if tpl_key not in CHAIN_TEMPLATES:
            tpl_key = "TRANSFER_FLAT" if evt_is_flat else "TRANSFER_PLOT"
            
        template = CHAIN_TEMPLATES[tpl_key]
        formatted_para = template.format(**ctx)
        
        # Clean up double spaces or dangling commas
        formatted_para = re.sub(r'\s+,\s+', ', ', formatted_para)
        formatted_para = re.sub(r'\s+', ' ', formatted_para).strip()
        
        paragraphs.append(formatted_para)

    return paragraphs
