import sys
import os
import json
from docx import Document

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from template_tools.builder_core import DocManipulator

def main():
    mappings_path = "scratch/fresh_discovery_mappings.json"
    doc_path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat.docx"
    
    with open(mappings_path, "r", encoding="utf-8") as f:
        mapping_dict = json.load(f)
        
    doc = Document(doc_path)
    DocManipulator.apply_deterministic_rules(doc)
    
    paragraphs = list(DocManipulator.iter_paragraphs_deep(doc))
    p = paragraphs[132]
    
    print("INITIAL STATE:")
    print(repr(p.text))
    print("-" * 50)
    
    reps = sorted(mapping_dict.items(), key=lambda x: len(x[0]), reverse=True)
    for old, new in reps:
        if old in p.text:
            print(f"Applying: '{old}' -> '{new}'")
            DocManipulator.safe_replace(p, old, new)
            print(f"Result: {repr(p.text)}")
            print("-" * 50)

if __name__ == "__main__":
    main()
