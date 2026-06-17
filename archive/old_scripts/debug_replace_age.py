import sys
import os
from docx import Document

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from template_tools.builder_core import DocManipulator

def main():
    doc_path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat.docx"
    doc = Document(doc_path)
    
    needle = '58 o"kZ'
    for part_name, part in DocManipulator.iter_story_parts(doc):
        for idx, p in enumerate(DocManipulator.iter_paragraphs_deep(part)):
            if needle in p.text:
                print("BEFORE:", p.text[:150])
                DocManipulator.safe_replace(p, needle, "{{ss[0].a}}")
                print("AFTER:", p.text[:150])
                print("-" * 50)

if __name__ == "__main__":
    main()
