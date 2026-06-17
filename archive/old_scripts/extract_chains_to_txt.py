import sys
import os
from docx import Document

sys.path.append(r"C:\Users\aksha\Documents\RM Generator\RM-Maker")
from utils.devlys_to_unicode import DevLysToUnicodeConverter

firm_path = r"C:\Users\aksha\Documents\RM Generator\RM-Maker\Reference Materials\Sale Deed\FLAT\SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat.docx"
gen_path = r"C:\Users\aksha\Documents\RM Generator\RM-Maker\cases\case_1781374115\Generated_AI_Test3.docx"

def convert_if_devlys(text):
    return DevLysToUnicodeConverter.devlys_to_unicode_text(text)

def save_document_text(filepath, out_path):
    doc = Document(filepath)
    lines = []
    
    lines.append(f"=== File: {os.path.basename(filepath)} ===")
    
    # We want to extract paragraphs that look like chain events
    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if text:
            converted = convert_if_devlys(text)
            # Check if it starts with standard chain openings
            if "सर्वप्रथम" in converted or "तत्पश्चात्" in converted or "यह कि" in converted or "पंजीकृत" in converted or "allotment" in text.lower() or "sale deed" in text.lower() or "construction" in text.lower():
                lines.append(f"P[{i}]: {converted}")
                
    for i, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                text = cell.text.strip()
                if text:
                    converted = convert_if_devlys(text)
                    if "सर्वप्रथम" in converted or "तत्पश्चात्" in converted or "यह कि" in converted or "पंजीकृत" in converted:
                        lines.append(f"T[{i}] Row {r_idx} Col {c_idx}: {converted}")
                        
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

save_document_text(firm_path, r"C:\Users\aksha\Documents\RM Generator\RM-Maker\scratch\firm_chain.txt")
save_document_text(gen_path, r"C:\Users\aksha\Documents\RM Generator\RM-Maker\scratch\generated_chain.txt")

print("Successfully written chain texts to scratch files!")
