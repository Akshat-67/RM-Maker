import sys
import os
from docx import Document

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from template_tools.builder_core import DocManipulator

def main():
    doc_path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat.docx"
    doc = Document(doc_path)
    
    needle = "¶ySV u- 007 ch] 2 CykWd] vuqie vikVZesUV] izrku uxj] lkaxkusj] lsDVj 11 t;iqj jktLFkku&302033"
    paragraphs = list(DocManipulator.iter_paragraphs_deep(doc))
    for idx, p in enumerate(paragraphs):
        if "foLoukFk" in p.text:
            print(f"Paragraph {idx} text:")
            print(repr(p.text))
            match = DocManipulator.find_fuzzy_match(p, needle)
            print(f"Match: {match}")

if __name__ == "__main__":
    main()
