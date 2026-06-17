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
    paragraphs = list(DocManipulator.iter_paragraphs_deep(doc))
    p = paragraphs[132]
    
    addr_start_idx = p.text.find("fuoklh%& ") + len("fuoklh%& ")
    doc_addr = p.text[addr_start_idx:]
    
    json_addr = ""
    for k in mapping_dict.keys():
        if "007" in k:
            json_addr = k
            break
            
    print("DOC :", repr(doc_addr[60:80]))
    print("JSON:", repr(json_addr[60:80]))

if __name__ == "__main__":
    main()
