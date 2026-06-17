import sys
import os
from docx import Document

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from template_tools.builder_core import DocManipulator

def main():
    doc_path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat.docx"
    doc = Document(doc_path)
    
    needle = "25-05-2026"
    found = False
    for part_name, part in DocManipulator.iter_story_parts(doc):
        for p_idx, p in enumerate(DocManipulator.iter_paragraphs_deep(part)):
            if needle in p.text:
                print(f"Found needle in paragraph text: '{p.text}'")
                match = DocManipulator.find_fuzzy_match(p, needle)
                print(f"Fuzzy match result: {match}")
                if match:
                    print("Runs in paragraph:")
                    for r_idx, run in enumerate(p.runs):
                        print(f"  Run {r_idx}: '{run.text}'")
                    found = True
                    # Try safe_replace
                    DocManipulator.safe_replace(p, needle, "{{rd}}")
                    print(f"After replace: '{p.text}'")
    if not found:
        print("Needle not found in any paragraph.")

if __name__ == "__main__":
    main()
