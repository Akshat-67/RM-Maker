import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.sd.processor import SDTemplateProcessor

CASES_DIR = "cases"
FAILED_CASES = []
SUCCESS_CASES = []
SKIPPED_CASES = []

def run_case(case_dir):
    session_file = os.path.join(case_dir, "session.json")
    if not os.path.exists(session_file):
        return "SKIP"

    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        doc_type = data.get("doc_type", "RM")
        if doc_type != "SD":
            return "SKIP"

        context = data.get('data', data.get('context', data))

        # Skip truly empty/newly created stub cases that don't even have an array mapped to 'ss' or empty lists
        if not context.get('ss') and not context.get('sellers'):
            print(f"[SKIP] {os.path.basename(case_dir)} is an empty stub case with no extraction data.")
            return "SKIP"

        template_path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat_unicode (1)_devlys.docx"
        output_path = os.path.join(case_dir, "test_output.docx")

        processor = SDTemplateProcessor(template_path)
        processor.generate(context, output_path, highlight_ai=False, highlight_missing=False)

        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            if size > 10000:
                print(f"[PASS] {os.path.basename(case_dir)} - generated {size} bytes")
                os.remove(output_path)
                return "PASS"
    except Exception as e:
        print(f"[ERROR] {os.path.basename(case_dir)} - {e}")
    return "FAIL"

if __name__ == "__main__":
    case_dirs = [os.path.join(CASES_DIR, d) for d in os.listdir(CASES_DIR) if os.path.isdir(os.path.join(CASES_DIR, d))]

    for c_dir in case_dirs:
        res = run_case(c_dir)
        if res == "PASS": SUCCESS_CASES.append(c_dir)
        elif res == "FAIL": FAILED_CASES.append(c_dir)
        else: SKIPPED_CASES.append(c_dir)

    print(f"\n--- VALIDATION SUMMARY ---")
    print(f"Total Cases: {len(case_dirs)}")
    print(f"SD Success: {len(SUCCESS_CASES)}")
    print(f"SD Failed: {len(FAILED_CASES)}")
    print(f"Skipped: {len(SKIPPED_CASES)}")

    if FAILED_CASES:
        sys.exit(1)
