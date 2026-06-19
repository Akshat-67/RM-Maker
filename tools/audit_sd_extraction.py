import os
import json
import sys
import copy
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import prune_case_data, smart_merge

def check_person_array(data: Dict[str, Any], array_key: str, required_fields: List[str]) -> List[str]:
    missing = []
    arr = data.get(array_key, [])
    if not arr:
        missing.append(f"{array_key} array missing or empty")
        return missing
    for idx, item in enumerate(arr):
        if not isinstance(item, dict):
             missing.append(f"{array_key}[{idx}] is not a dict")
             continue
        for field in required_fields:
             val = item.get(field)
             if not val or (isinstance(val, str) and not val.strip()):
                 missing.append(f"{array_key}[{idx}].{field}")
    return missing

def evaluate_data(data: Dict[str, Any], step_name: str) -> Dict[str, Any]:
    print(f"\n--- Evaluating {step_name} ---")
    missing_fields = []

    # Sellers
    missing_fields.extend(check_person_array(data, 'ss', ['n', 'relation_text', 'adr']))
    # Buyers
    missing_fields.extend(check_person_array(data, 'bs', ['n', 'relation_text', 'adr']))
    # Property
    prop_missing = check_person_array(data, 'ps', [])
    if prop_missing:
         missing_fields.extend(prop_missing)
    else:
         props = data.get('ps', [])
         for idx, prop in enumerate(props):
             has_desc = prop.get('plot_no') or prop.get('flat_no') or prop.get('building_name') or prop.get('document_number') or prop.get('scheme') or prop.get('village') or prop.get('adr')
             if not has_desc:
                 missing_fields.append(f"ps[{idx}] lacks identifiable property description")

    # Financial
    if not data.get('amount') and not data.get('consideration') and not data.get('amount_words') and not data.get('sale', {}).get('amount'):
        missing_fields.append("amount/consideration")

    status = "FAIL" if missing_fields else "PASS"
    print(f"Status: {status}")
    if missing_fields:
        print("Missing Fields:")
        for m in missing_fields:
            print(f"  - {m}")
    else:
        print("All critical fields present.")

    return {"status": status, "missing": missing_fields}

def audit_case(case_dir: str):
    session_path = os.path.join(case_dir, "session.json")
    if not os.path.exists(session_path):
        return

    with open(session_path, 'r', encoding='utf-8') as f:
        session = json.load(f)

    if session.get("doc_type") != "SD":
        return

    data = session.get("data", {})
    if not data:
        return

    print(f"\n{'='*50}")
    print(f"Auditing Case: {case_dir}")
    print(f"{'='*50}")

    print("\nEvaluating existing session data state:")
    evaluate_data(data, "Current Session state")

if __name__ == "__main__":
    for folder in ["validation_cases", "cases"]:
        if os.path.exists(folder):
            for case in os.listdir(folder):
                case_path = os.path.join(folder, case)
                if os.path.isdir(case_path):
                    audit_case(case_path)

    print("\n\nAudit Complete.")
