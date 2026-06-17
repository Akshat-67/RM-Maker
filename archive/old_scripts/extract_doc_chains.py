import sys
import os
from docx import Document

sys.stdout.reconfigure(encoding='utf-8')

# Import DevLys to Unicode converter
sys.path.append(r"C:\Users\aksha\Documents\RM Generator\RM-Maker")
from utils.devlys_to_unicode import DevLysToUnicodeConverter

firm_path = r"C:\Users\aksha\Documents\RM Generator\RM-Maker\Reference Materials\Sale Deed\FLAT\SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat.docx"
gen_path = r"C:\Users\aksha\Documents\RM Generator\RM-Maker\cases\case_1781374115\Generated_AI_Test3.docx"

def convert_if_devlys(text):
    # If it has DevLys specific sequences, convert it
    return DevLysToUnicodeConverter.devlys_to_unicode_text(text)

def dump_document(filepath, label):
    print(f"\n=====================================")
    print(f"=== {label} : {os.path.basename(filepath)} ===")
    print(f"=====================================")
    doc = Document(filepath)
    
    print("--- Paragraphs ---")
    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if text:
            converted = convert_if_devlys(text)
            print(f"P[{i}]: {converted}")
                
    print("\n--- Tables ---")
    for i, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                text = cell.text.strip()
                if text:
                    converted = convert_if_devlys(text)
                    print(f"T[{i}] Row {r_idx} Col {c_idx}: {converted}")

dump_document(firm_path, "FIRM APPROVED SD (Converted)")
dump_document(gen_path, "LATEST GENERATED SD (Converted)")
