import os
import sys
import glob
import json

# Add root to sys.path to resolve module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.sd.narrative import generate_chain_narrative
from modules.sd.processor import SDTemplateProcessor
from modules.sd.extractor import SDDataExtractor
from app import prune_case_data
from collections import defaultdict
import docx

def find_target_document(case_dir):
    files = []
    for ext in ['*.doc', '*.docx']:
        files.extend(glob.glob(os.path.join(case_dir, ext)))
    if not files: return None
    for f in files:
        base = os.path.basename(f).lower()
        if 'sd' in base or 'sale deed' in base:
            return f
    if files:
        files.sort(key=lambda x: os.path.getsize(x), reverse=True)
        return files[0]
    return None

def find_source_documents(case_dir, target_doc):
    all_files = [os.path.join(case_dir, f) for f in os.listdir(case_dir) if os.path.isfile(os.path.join(case_dir, f))]
    source_docs = []
    for f in all_files:
        if target_doc and os.path.abspath(f) == os.path.abspath(target_doc):
            continue
        if not f.endswith(('.pdf', '.jpeg', '.jpg', '.png')):
            continue
        source_docs.append(f)
    return source_docs

def extract_text_from_docx(path):
    try:
        doc = docx.Document(path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception:
        return ""

def compare_documents(generated_path, target_path):
    print("  [Compare] Comparing documents...")
    if not target_path or not os.path.exists(target_path):
        print("  [Compare] No target document found to compare.")
        return
    try:
        if target_path.endswith('.docx'):
            target_text = extract_text_from_docx(target_path)
            generated_text = extract_text_from_docx(generated_path)
            if len(target_text) > 0:
                print(f"  [Compare] Target doc size: {len(target_text)} chars")
                print(f"  [Compare] Generated doc size: {len(generated_text)} chars")
            else:
                 print("  [Compare] Target doc is empty or unreadable.")
        else:
             print("  [Compare] Target document is a .doc, text extraction currently only supports .docx.")
    except Exception as e:
        print(f"  [Compare] Warning: failed to parse target doc: {e}")

def local_build_sd_context(data):
    """Replicates the critical path of context generation from app.py"""
    context = data.copy()

    # Ensure all required lists exist to prevent Jinja2 errors, and pad them to prevent out-of-bounds [MISSING]
    for key in ["bs", "ls", "ps", "ws", "ss", "sellers", "buyers", "chain"]:
        if key not in context or not isinstance(context[key], list):
            context[key] = []
        while len(context[key]) < 10:
            context[key].append(defaultdict(str))

    context["w1"] = context["ws"][0]
    context["w2"] = context["ws"][1]

    for i, s in enumerate(context["sellers"]):
        if i < len(context["ss"]):
            context["ss"][i]["address"] = s.get("adr", "")
            context["ss"][i]["aadhaar"] = s.get("id", "")
    for i, b in enumerate(context["buyers"]):
        if i < len(context["bs"]):
            context["bs"][i]["address"] = b.get("adr", "")
            context["bs"][i]["aadhaar"] = b.get("id", "")

    if "title_chain" in context and isinstance(context["title_chain"], list):
        context["chain_text"] = generate_chain_narrative(context["title_chain"])
    else:
        context["chain_text"] = ""

    context['d'] = context.copy()
    return context

def run_case(case_dir, case_id):
    print(f"\n--- Processing Case: {case_id} ---")

    target_doc = find_target_document(case_dir)
    print(f"  Target Draft Identified: {target_doc}")

    source_docs = find_source_documents(case_dir, target_doc)
    print(f"  Source Documents Found: {len(source_docs)}")

    if not source_docs:
        print("  [FAIL] No valid source documents found for extraction. Skipping.")
        return False

    print(f"  [Extract] Running live extraction via SDDataExtractor...")

    from utils.config import DEFAULT_GEMINI_API_KEYS
    extractor = SDDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS, provider="gemini")

    try:
        # Use extract_with_ai instead of extract
        session_data = extractor.extract_with_ai(file_paths=source_docs, selected_model="gemini-2.5-flash", expected_sellers=1, expected_buyers=1)
        if not session_data:
             print("  [FAIL] Extraction returned no data.")
             return False
        if "error" in session_data:
             print(f"  [FAIL] Extraction returned error: {session_data['error']}")
             return False

        print("  [OK] Extraction Successful")

        # Log basic extraction facts for report updates
        extracted_ps = session_data.get("ps", [{}])[0]
        extracted_ss = session_data.get("ss", [{}])[0]
        extracted_bs = session_data.get("bs", [{}])[0]
        print(f"    - Seller: {extracted_ss.get('n', 'None')}")
        print(f"    - Buyer: {extracted_bs.get('n', 'None')}")
        print(f"    - Consideration: {session_data.get('sale', {}).get('amount', 'None')}")
        print(f"    - Property: {extracted_ps.get('adr', 'None')}")
        print(f"    - Title Events: {len(session_data.get('title_chain', []))}")

        # Save session mock data locally
        with open(f"validation_cases/{case_id}/session.json", "w") as f:
            json.dump(session_data, f, indent=4)

    except Exception as e:
        print(f"  [FAIL] Extraction Error: {e}")
        import traceback; traceback.print_exc()
        return False

    try:
        context = local_build_sd_context(session_data)
        print("  [OK] Context Generated")
    except Exception as e:
        print(f"  [FAIL] Context Generation Error: {e}")
        import traceback; traceback.print_exc()
        return False

    template_path = glob.glob("templates/SALE_DEED/*.docx")[0]
    output_path = f"validation_cases/{case_id}/generated_SD.docx"

    try:
        processor = SDTemplateProcessor(template_path)
        processor.generate(context, output_path, highlight_ai=True)
        print(f"  [OK] SD Generated at {output_path}")

        # Compare
        compare_documents(output_path, target_doc)

        return True
    except Exception as e:
        print(f"  [FAIL] Generation Error: {e}")
        return False

def main():
    from utils.config import DEFAULT_GEMINI_API_KEYS
    if not DEFAULT_GEMINI_API_KEYS:
         print("Warning: No Gemini API keys found in environment. Extraction will fail.")

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
