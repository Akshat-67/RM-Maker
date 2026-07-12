import os
import re
import html
import datetime
from collections import defaultdict

import docx
from docxtpl import DocxTemplate
from docx.text.paragraph import Paragraph
from docx.table import Table

from services.session_manager import CASES_DIR, title_case_address, normalize_amount_in_words
from services.file_service import TEMPLATES_DIR, discover_templates
from utils.devlys_to_unicode import DevLysToUnicodeConverter
from utils.helpers import format_date_to_ordinal_english

from modules.rm.processor import RMTemplateProcessor
from modules.sd.processor import SDTemplateProcessor
from modules.sd.extractor import SDDataExtractor
from modules.sd.narrative import generate_chain_narrative

def compile_and_render_document(
    case_id,
    session,
    doc_type="RM",
    bank=None,
    borrowers=None,
    loans=None,
    properties="1",
    sellers_count="1",
    buyers_count="1",
    chain_scenario="",
    selected_template="",
    property_type="Plot",
    verified_fields=None
):
    if verified_fields is None:
        verified_fields = set()

    data = session.get("data", {})
    template_map, sd_template_map, _ = discover_templates()

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
        raise ValueError("No valid template found.")

    # Map the second_schedule string into the ds list for the templates.
    sec_sched_val = data.get("second_schedule", "")
    sec_sched_val = re.sub(r'(?<=\S)\s+(Original\b|Certified Copy\b)', r'\n\1', sec_sched_val, flags=re.IGNORECASE)
    sec_lines = [x.strip() for x in sec_sched_val.split("\n") if x.strip()]
    ds_list = [{"t": line} for line in sec_lines]
    
    while len(ds_list) < 10:
        ds_list.append({"t": ""})
    data["ds"] = ds_list

    # Ensure all required lists exist to prevent Jinja2 errors, and pad them to prevent out-of-bounds [MISSING]
    for key in ["bs", "ls", "ps", "ws", "ss", "sellers", "buyers", "chain"]:
        if key not in data or not isinstance(data[key], list):
            data[key] = []
        while len(data[key]) < 10:
            data[key].append(defaultdict(str))

    # Provide 'd' as an alias for the entire data object. 
    context = data.copy()
    context["w1"] = data["ws"][0]
    context["w2"] = data["ws"][1]

    # SD-specific field aliasing
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
        # Also alias w1, w2
        for w in [context.get("w1"), context.get("w2")]:
            if isinstance(w, dict):
                if "address" not in w or not w["address"]:
                    w["address"] = w.get("adr", "")
                if "aadhaar" not in w or not w["aadhaar"]:
                    w["aadhaar"] = w.get("id", "")

        # Format Consideration Amount
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

        # Clean up amount_words
        if context.get("amount_words"):
            context["amount_words"] = context["amount_words"].replace("मात्र", "").strip()

        # Build payment_details if not present
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
                    parts = re.split(r'\s+एवं\s+|\s+व\s+|,', executant)
                    if len(parts) > 1:
                        name2 = parts[1].strip()
                        s1["n"] = name2
                        break
        context["ss"] = ss_list

        # Recompute ps computed fields
        _sd_extractor = SDDataExtractor()
        ps0 = context.get("ps", [{}])[0]
        is_flat_property = _sd_extractor.is_flat_property(ps0)
        resolved_property_type = "Flat" if is_flat_property else "Plot"

        if "ps" in context and context["ps"] and isinstance(context["ps"][0], dict):
            p0 = context["ps"][0]
            if not p0.get("flat_no") and "title_chain" in context:
                for evt in context["title_chain"]:
                    if evt.get("unit_number"):
                        p0["flat_no"] = evt["unit_number"]
                        break

        for p in context.get("ps", []):
            if isinstance(p, dict) and any(p.values()):
                p["full_address"] = _sd_extractor.generate_full_property_address(p, "SD", resolved_property_type)
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

    # Normalize execution date for SD
    if doc_type == "SD" and context.get("rd"):
        normalized_rd = str(context["rd"]).replace(".", "-")
        context["rd"] = normalized_rd
        if "deed" not in context:
            context["deed"] = {}
        context["deed"]["execution_date"] = normalized_rd

    # Chain paragraphs narrative
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

    # Formatting of execution date (rd)
    if context.get("rd"):
        if doc_type == "RM":
            formatted_rd = format_date_to_ordinal_english(context["rd"])
        else:
            formatted_rd = str(context["rd"]).strip().replace("-", ".").replace("/", ".")
        context["rd"] = formatted_rd
        if "deed" not in context:
            context["deed"] = {}
        context["deed"]["execution_date"] = formatted_rd

    context['d'] = context.copy()

    output_filename = f"{doc_type}_{case_id}.docx"
    output_filepath = os.path.join(CASES_DIR, case_id, output_filename)

    if doc_type == "SD":
        processor = SDTemplateProcessor(template_path)
    else:
        processor = RMTemplateProcessor(template_path)
        
    processor.generate(context, output_filepath, highlight_ai=True, highlight_missing=True, verified_fields=verified_fields)
    return output_filepath, output_filename


def generate_draft_preview(
    case_id,
    session,
    doc_type="RM",
    bank=None,
    borrowers=None,
    loans=None,
    properties="1",
    sellers_count="1",
    buyers_count="1",
    chain_scenario="",
    selected_template="",
    property_type="Plot",
    verified_fields=None
):
    if verified_fields is None:
        verified_fields = set()

    data = session.get("data", {})
    template_map, sd_template_map, _ = discover_templates()

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
        raise ValueError("No valid template found.")

    sec_sched_val = data.get("second_schedule", "")
    sec_sched_val = re.sub(r'(?<=\S)\s+(Original\b|Certified Copy\b)', r'\n\1', sec_sched_val, flags=re.IGNORECASE)
    sec_lines = [x.strip() for x in sec_sched_val.split("\n") if x.strip()]
    ds_list = [{"t": line} for line in sec_lines]
    while len(ds_list) < 10:
        ds_list.append({"t": ""})
    data["ds"] = ds_list

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

    if context.get("rd"):
        if doc_type == "RM":
            formatted_rd = format_date_to_ordinal_english(context["rd"])
        else:
            formatted_rd = str(context["rd"]).strip().replace("-", ".").replace("/", ".")
        context["rd"] = formatted_rd
        if "deed" not in context:
            context["deed"] = {}
        context["deed"]["execution_date"] = formatted_rd

    if doc_type == "RM":
        for b in context.get("bs", []):
            if isinstance(b, dict) and b.get("adr"):
                b["adr"] = title_case_address(b["adr"])
        for w in context.get("ws", []):
            if isinstance(w, dict) and w.get("adr"):
                w["adr"] = title_case_address(w["adr"])
        bsign = context.get("bsign")
        if isinstance(bsign, dict) and bsign.get("adr"):
            bsign["adr"] = title_case_address(bsign["adr"])
        for p in context.get("ps", []):
            if isinstance(p, dict):
                if p.get("adr"):
                    p["adr"] = title_case_address(p["adr"])
                if p.get("full_address"):
                    p["full_address"] = title_case_address(p["full_address"])
        for l in context.get("ls", []):
            if isinstance(l, dict) and l.get("w"):
                l["w"] = normalize_amount_in_words(l["w"])

    context['d'] = context.copy()

    doc = DocxTemplate(template_path)
    doc.render(context)

    pages = []
    current_page_elements = []

    for element in doc.element.body:
        if element.tag.endswith('p'):
            p = Paragraph(element, doc)
            txt = p.text.strip()
            
            p_xml = element.xml
            has_page_break = ('w:br' in p_xml and 'w:type="page"' in p_xml) or ('w:lastRenderedPageBreak' in p_xml)
            
            if has_page_break and current_page_elements:
                pages.append(current_page_elements)
                current_page_elements = []

            if txt:
                unicode_parts = []
                for run in p.runs:
                    run_txt = run.text
                    if not run_txt:
                        continue
                    if DevLysToUnicodeConverter._devanagari_regex.search(run_txt):
                        unicode_parts.append(run_txt)
                    else:
                        unicode_parts.append(DevLysToUnicodeConverter.devlys_to_unicode_text(run_txt))
                
                unicode_txt = "".join(unicode_parts).strip()
                
                if unicode_txt:
                    escaped = html.escape(unicode_txt)
                    escaped = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', escaped)
                    
                    normalized_txt = unicode_txt.replace(" ", "")
                    if len(unicode_txt.strip()) < 20 and "!!श्री!!" in normalized_txt:
                        p_style = "text-align: center; color: #dc2626; font-weight: bold; font-size: 1.35rem; margin-top: 1rem; margin-bottom: 1.5rem; font-family: 'Segoe UI', 'Mangal';"
                        current_page_elements.append(f"<p style=\"{p_style}\">!! श्री !!</p>")
                    elif len(unicode_txt.strip()) < 20 and ("विक्रय-पत्र" in unicode_txt or "विक्रय पत्र" in unicode_txt):
                        p_style = "text-align: center; color: #dc2626; font-weight: bold; font-size: 1.35rem; text-decoration: underline; margin-bottom: 2.5rem; font-family: 'Segoe UI', 'Mangal';"
                        current_page_elements.append(f"<p style=\"{p_style}\">{escaped}</p>")
                    elif len(unicode_txt.strip()) < 30 and unicode_txt.strip().startswith("-") and unicode_txt.strip().endswith("-"):
                        p_style = "text-align: center; font-weight: bold; font-size: 1.15rem; margin: 1.8rem 0; font-family: 'Segoe UI', 'Mangal';"
                        current_page_elements.append(f"<p style=\"{p_style}\">{escaped}</p>")
                    else:
                        p_style = "text-align: justify; text-indent: 45px; font-size: 1.05rem; line-height: 1.75; margin-bottom: 1.2rem; font-family: 'Segoe UI', 'Mangal'; color: #111827;"
                        current_page_elements.append(f"<p style=\"{p_style}\">{escaped}</p>")
        
        elif element.tag.endswith('tbl'):
            t = Table(element, doc)
            table_html = ["<table class='table table-sm table-bordered shadow-sm bg-white' style='margin-bottom: 1.2rem; font-size: 0.85rem; font-family: Segoe UI, Mangal;'>"]
            for row in t.rows:
                table_html.append("<tr>")
                for cell in row.cells:
                    cell_parts = []
                    for cell_p in cell.paragraphs:
                        cell_unicode_parts = []
                        for run in cell_p.runs:
                            run_txt = run.text
                            if not run_txt:
                                continue
                            if DevLysToUnicodeConverter._devanagari_regex.search(run_txt):
                                cell_unicode_parts.append(run_txt)
                            else:
                                cell_unicode_parts.append(DevLysToUnicodeConverter.devlys_to_unicode_text(run_txt))
                        cell_parts.append("".join(cell_unicode_parts))
                    unicode_cell = "\n".join(cell_parts).strip()
                    table_html.append(f"<td style='padding: 8px 12px; border: 1px solid #dee2e6; vertical-align: middle;'>{html.escape(unicode_cell)}</td>")
                table_html.append("</tr>")
            table_html.append("</table>")
            current_page_elements.append("".join(table_html))

    if current_page_elements:
        pages.append(current_page_elements)

    html_parts = []
    for idx, page_elems in enumerate(pages):
        page_content = "".join(page_elems)
        page_header = f"<div class='word-page-number' style='text-align: center; font-size: 0.85rem; color: #64748b; margin-bottom: 35px; font-family: sans-serif;'>{idx + 1}</div>" if idx > 0 else ""
        html_parts.append(f"<div class='word-page' style='background: #ffffff; box-shadow: 0 4px 16px rgba(0,0,0,0.09); border: 1px solid #cbd5e1; border-radius: 2px; max-width: 800px; margin: 15px auto 25px auto; padding: 50px 65px; min-height: 297mm; box-sizing: border-box; text-align: left;'>{page_header}{page_content}</div>")

    preview_html = "".join(html_parts)
    if not preview_html:
        preview_html = "<p class='text-muted text-center py-4'>Template loaded but contained no readable text elements.</p>"
        
    return preview_html
