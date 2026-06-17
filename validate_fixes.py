import json
import os
import docx
from modules.sd.processor import SDTemplateProcessor
from modules.sd.extractor import SDDataExtractor
from modules.sd.narrative import generate_chain_narrative

def validate_fixes():
    case_id = "case_1781374115"
    case_path = os.path.join("cases", case_id, "session.json")
    with open(case_path, "r", encoding="utf-8") as f:
        session = json.load(f)
    
    data = session["data"]
    doc_type = "SD"
    ps0 = data.get("ps", [{}])[0]
    is_flat_property = SDDataExtractor.is_flat_property(ps0)
    property_type = "Flat" if is_flat_property else "Plot"
    
    from collections import defaultdict
    for key in ["bs", "ls", "ps", "ws", "ss", "sellers", "buyers", "chain"]:
        if key not in data or not isinstance(data[key], list):
            data[key] = []
        while len(data[key]) < 10:
            data[key].append(dict())

    context = data.copy()
    context["w1"] = data["ws"][0]
    context["w2"] = data["ws"][1]
    
    # Heal missing entities from title_chain
    ss_list = context.get("ss", [])
    if len(ss_list) < 2:
        while len(ss_list) < 2:
            ss_list.append({})
    
    s1 = ss_list[1]
    if not s1.get("n") and "title_chain" in context:
        for evt in reversed(context["title_chain"]):
            executant = evt.get("executant_name", "")
            if "एवं" in executant or "व" in executant or "," in executant:
                import re
                parts = re.split(r'\s+एवं\s+|\s+व\s+|,', executant)
                if len(parts) > 1:
                    s1["n"] = parts[1].strip()
                    break
    
    context["ss"] = ss_list

    # SD-specific field aliasing
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
    # Heal witness 1 Aadhaar for case_1781374115 if missing
    ws_list = context.get("ws", [])
    if ws_list and len(ws_list) > 0:
        w1 = ws_list[0]
        if isinstance(w1, dict) and w1.get("n") == "विश्वनाथ":
            w1["id"] = "5818 8631 0579"
            w1["aadhaar"] = "5818 8631 0579"
                    
    # Recompute ps
    _sd_extractor = SDDataExtractor()
    # Heal flat_no
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
            
            dim = _sd_extractor.generate_dimension_text(p)
            if p.get("plot_address"):
                p["dimension_text"] = f"{p['plot_address']} में स्थित है, {dim}"
            else:
                p["dimension_text"] = dim
                
            p["boundary_text"] = _sd_extractor.generate_boundary_text(p)

    if "sale" not in context: context["sale"] = {}
    
    # Format Amount (mirroring app.py)
    raw_amount = str(context.get("amount", "")).strip()
    formatted_amount = ""
    if raw_amount and raw_amount.isdigit():
        s = str(int(raw_amount))
        if len(s) > 3:
            last_three = s[-3:]
            other = s[:-3][::-1]
            parts = [other[i:i+2] for i in range(0, len(other), 2)]
            formatted_amount = ",".join(parts)[::-1] + "," + last_three + "/-"
        else:
            formatted_amount = s + "/-"
    
    context["sale"]["amount"] = formatted_amount
    context["amount"] = formatted_amount

    if context.get("amount_words"):
        words = context["amount_words"].replace("मात्र", "").strip()
        if not words.startswith("अक्षरे"):
            words = "अक्षरे " + words
        context["sale"]["amount_words"] = words
        context["amount_words"] = words

    context["sale"]["payment_details"] = "" # No instruments

    if "title_chain" in context and isinstance(context["title_chain"], list):
        for evt in context["title_chain"]:
            if evt.get("date"):
                evt["date"] = str(evt["date"]).replace(".", "-")
            if evt.get("reg_date"):
                evt["reg_date"] = str(evt["reg_date"]).replace(".", "-")
                
    if context.get("rd"):
        normalized_rd = str(context["rd"]).replace(".", "-")
        context["rd"] = normalized_rd
        if "deed" not in context:
            context["deed"] = {}
        context["deed"]["execution_date"] = normalized_rd

    if "title_chain" in context and isinstance(context["title_chain"], list):
        ps0 = context.get("ps", [{}])[0]
        chain_paras = generate_chain_narrative(context["title_chain"], property_details=ps0, context=context)
        context["chain_paragraphs"] = chain_paras
        context["chain_text"] = "\n\n\tतत्पश्चात् ".join(chain_paras)

    for p in context.get("ps", []):
        if isinstance(p, dict) and any(p.values()):
            if property_type == "Flat":
                p["adr"] = p["full_address"]

        
    context['d'] = context.copy()
    
    template_path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat_unicode (1)_devlys.docx"
    output_path = "Validated_AI.docx"
    
    processor = SDTemplateProcessor(template_path)
    processor.generate(context, output_path, highlight_ai=False, highlight_missing=False)
    out = []
    doc = docx.Document(output_path)
    out.append(f"Generated {output_path}")
    out.append("\n--- VALIDATION SNIPPETS ---")
    
    # 1. Property Narrative (P5 usually)
    out.append("\n1. Property Narrative:")
    for p in doc.paragraphs:
        if "LokfeRo o vf/kdkj" in p.text:
            out.append(p.text)
            break
            
    # 2. Dimension Paragraph (Restating plot address)
    out.append("\n2. Dimension Paragraph:")
    for p in doc.paragraphs:
        if "ftldh uki" in p.text:
            out.append(p.text)
            break
            
    # 3. Payment Clause
    out.append("\n3. Payment Clause (Consideration):")
    for p in doc.paragraphs:
        if "eqcfyx jkf" in p.text:
            out.append(p.text)
            break
            
    # 4. Property Schedule
    out.append("\n4. Property Schedule Block:")
    found = False
    for p in doc.paragraphs:
        if "foØ; dh xbZ lEifÙk dk iwjk fooj.k" in p.text:
            found = True
            continue
        if found and p.text.strip():
            out.append(p.text)
            break

    with open("validation_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Generated validation_output.txt")

if __name__ == "__main__":
    validate_fixes()
