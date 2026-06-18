import os
import sys
import glob
from unittest.mock import patch

# Add root to sys.path to resolve module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.sd.narrative import generate_chain_narrative
from modules.sd.processor import SDTemplateProcessor
import docx

# Mock extraction data so we can test the pipeline locally without an API key
MOCK_EXTRACTION = {
    "execution_date": "2025-06-05",
    "sellers": [{"name": "Mock Seller", "name_en": "Mock Seller", "relative_name": "Mock Relative", "address": "Mock Address"}],
    "buyers": [{"name": "Mock Buyer", "name_en": "Mock Buyer", "relative_name": "Mock Relative", "address": "Mock Address"}],
    "property_schedule": [{"address": "Mock Property Address", "area": "1000", "area_unit": "SqFt"}],
    "consideration_amount": "100000",
    "witnesses": [{"name": "Mock Witness", "address": "Mock Witness Address"}],
    "title_chain": [{"event_type": "SALE_DEED", "date": "2020-01-01", "seller": "Old Seller", "buyer": "Mock Seller"}],
    "payments": [{"amount": "100000", "date": "2025-06-01", "method": "Cheque", "bank": "Mock Bank"}]
}

def find_target_document(case_dir):
    """Heuristic to find the firm-created SD draft (.doc or .docx)"""
    files = []
    for ext in ['*.doc', '*.docx']:
        files.extend(glob.glob(os.path.join(case_dir, ext)))

    if not files:
        return None

    # Heuristics:
    # 1. Contains 'SD' or 'Sale Deed'
    for f in files:
        base = os.path.basename(f).lower()
        if 'sd' in base or 'sale deed' in base:
            return f

    # 2. Return the largest document if no obvious match
    files.sort(key=lambda x: os.path.getsize(x), reverse=True)
    return files[0]

def mock_build_context(data):
    # Extremely basic mapping based on SD_SCHEMA and app.py logic
    ctx = {
        "rd": data.get("execution_date", ""),
        "ss": [{"n": s.get("name"), "r": s.get("relative_name"), "adr": s.get("address")} for s in data.get("sellers", [])],
        "bs": [{"n": b.get("name"), "r": b.get("relative_name"), "adr": b.get("address")} for b in data.get("buyers", [])],
        "ps": [{"adr": p.get("address"), "area": p.get("area")} for p in data.get("property_schedule", [])],
        "ws": [{"n": w.get("name"), "adr": w.get("address")} for w in data.get("witnesses", [])],
        "chain": data.get("title_chain", []),
        "payments": data.get("payments", [])
    }
    # Provide the 'd' object pattern needed by templates
    ctx["d"] = ctx.copy()
    ctx["chain_text"] = generate_chain_narrative(ctx.get("chain", []))
    # Alias w1, w2
    if len(ctx["ws"]) > 0: ctx["w1"] = ctx["ws"][0]
    if len(ctx["ws"]) > 1: ctx["w2"] = ctx["ws"][1]
    return ctx

def extract_text_from_docx(path):
    doc = docx.Document(path)
    return "\n".join([para.text for para in doc.paragraphs])

def compare_documents(generated_path, target_path):
    print("  [Compare] Comparing documents...")
    if not target_path or not os.path.exists(target_path):
        print("  [Compare] No target document found to compare.")
        return

    try:
        if target_path.endswith('.docx'):
            target_text = extract_text_from_docx(target_path)
            generated_text = extract_text_from_docx(generated_path)

            # VERY basic length comparison for demonstration
            if len(target_text) > 0:
                print(f"  [Compare] Target doc size: {len(target_text)} chars")
                print(f"  [Compare] Generated doc size: {len(generated_text)} chars")
            else:
                 print("  [Compare] Target doc is empty or unreadable.")
        else:
             print("  [Compare] Target document is a .doc, text extraction currently only supports .docx.")
    except Exception as e:
        print(f"  [Compare] Warning: failed to parse target doc: {e}")

def run_case(case_dir, case_id):
    print(f"\n--- Processing Case: {case_id} ---")

    target_doc = find_target_document(case_dir)
    print(f"  Target Draft Identified: {target_doc}")

    session_data = MOCK_EXTRACTION
    print("  [OK] Extraction Simulated")

    try:
        context = mock_build_context(session_data)
        print("  [OK] Context Generated")
    except Exception as e:
        print(f"  [FAIL] Context Generation Error: {e}")
        return False

    template_path = glob.glob("templates/SALE_DEED/*.docx")[0]
    output_path = f"validation_cases/{case_id}/generated_SD.docx"

    try:
        processor = SDTemplateProcessor(template_path)
        processor.generate(context, output_path, highlight_ai=True)
        print(f"  [OK] SD Generated at {output_path}")

        # Compare
        compare_documents(output_path, target_doc)

        # Clean up output artifact
        os.remove(output_path)

        return True
    except Exception as e:
        print(f"  [FAIL] Generation Error: {e}")
        return False

def main():
    validation_dir = 'validation_cases'
    if not os.path.exists(validation_dir):
        print(f"Validation directory {validation_dir} not found.")
        return

    cases = sorted([d for d in os.listdir(validation_dir) if os.path.isdir(os.path.join(validation_dir, d))])

    for case in cases:
        case_dir = os.path.join(validation_dir, case)
        run_case(case_dir, case)

if __name__ == '__main__':
    main()
