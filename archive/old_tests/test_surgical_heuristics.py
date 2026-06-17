import sys
import os
import re
from docx import Document

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from template_tools.builder_core import DocManipulator

def main():
    doc_path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat.docx"
    doc = Document(doc_path)
    
    # Get paragraphs from deep iteration
    paragraphs = list(DocManipulator.iter_paragraphs_deep(doc))
    p = paragraphs[28]
    
    with open("scratch/surgical_heuristics_output.txt", "w", encoding="utf-8") as f:
        f.write("Original Paragraph 28:\n")
        f.write(p.text + "\n\n")
        
        # Test surgical replacements
        # 1. Dimension replacement
        dim_match = re.search(r'(ftldh uki.*?oxZxt gS|जिसकी नाप.*?वर्गगज है)', p.text)
        if dim_match:
            dim_text = dim_match.group(0)
            f.write(f"Found Dimension Text: '{dim_text}'\n")
            DocManipulator.safe_replace(p, dim_text, "{{ps[0].dimension_text}}")
            
        # 2. Boundary replacement
        boundary_match = re.search(r'(ftldh pkjksa lhekvkssa.*?fLFkr gS|जिसकी चारों सीमाएं.*?स्थित है)', p.text)
        if boundary_match:
            boundary_text = boundary_match.group(0)
            f.write(f"Found Boundary Text: '{boundary_text}'\n")
            DocManipulator.safe_replace(p, boundary_text, "{{ps[0].boundary_text}}")
            
        f.write("Modified Paragraph 28:\n")
        f.write(p.text + "\n")

if __name__ == "__main__":
    main()
