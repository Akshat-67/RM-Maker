import os
import sys
import json
from modules.rm.processor import RMTemplateProcessor as TemplateProcessor
from app import discover_templates

def test_generation():
    case_id = "case_1781087650"
    session_path = f"cases/{case_id}/session.json"
    
    with open(session_path, "r", encoding="utf-8") as f:
        session = json.load(f)
    
    data = session.get("data", {})
    verified_fields = set(session.get("verified_fields", []))
    bank = session.get("bank")
    borrowers = session.get("borrower_count")
    loans = session.get("loan_count")
    properties = session.get("properties_count", "1")
    
    template_map, sd_template_map, bank_folders = discover_templates()
    
    sub_map = template_map.get(bank, {}).get(str(borrowers), {}).get(str(loans))
    if isinstance(sub_map, dict):
        template_path = sub_map.get(str(properties)) or sub_map.get("1")
    else:
        template_path = sub_map
        
    print(f"Template Path: {template_path}")
    if not template_path or not os.path.exists(template_path):
        print("Template not found!")
        return

    # Mocking the generation logic from app.py
    sec_sched_val = data.get("second_schedule", "")
    import re
    sec_sched_val = re.sub(r'(?<=\S)\s+(Original\b|Certified Copy\b|Endorsed Copy\b)', r'\n\1', sec_sched_val, flags=re.IGNORECASE)
    sec_lines = [x.strip() for x in sec_sched_val.split("\n") if x.strip()]
    ds_list = [{"t": line} for line in sec_lines]
    while len(ds_list) < 10: ds_list.append({"t": ""})
    data["ds"] = ds_list

    from collections import defaultdict
    for key in ["bs", "ls", "ps", "ws", "ss", "title_chain", "ds"]:
        if key not in data or not isinstance(data[key], list):
            data[key] = []
        while len(data[key]) < 100:
            data[key].append(defaultdict(str))

    context = data.copy()
    context['d'] = data 

    print("Context List Lengths:")
    for k, v in context.items():
        if isinstance(v, list):
            print(f"  {k}: {len(v)}")

    output_filename = "test_output_case.docx"
    
    print("Running processor.generate...")
    try:
        processor = TemplateProcessor(template_path)
        processor.generate(context, output_filename, highlight_ai=True, highlight_missing=True, verified_fields=verified_fields)
        print("SUCCESS: Document generated.")
    except Exception as e:
        print(f"FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generation()
