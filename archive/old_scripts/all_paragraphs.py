import sys
import os
from docx import Document

sys.path.append(r"C:\Users\aksha\Documents\RM Generator\RM-Maker")
from utils.devlys_to_unicode import DevLysToUnicodeConverter

firm_path = r"C:\Users\aksha\Documents\RM Generator\RM-Maker\Reference Materials\Sale Deed\FLAT\SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat.docx"
gen_path = r"C:\Users\aksha\Documents\RM Generator\RM-Maker\cases\case_1781374115\Generated_AI_Test3.docx"

def convert_if_devlys(text):
    return DevLysToUnicodeConverter.devlys_to_unicode_text(text)

def dump_all(filepath, out_path):
    doc = Document(filepath)
    lines = []
    for i, p in enumerate(doc.paragraphs):
        text = p.text
        converted = convert_if_devlys(text)
        lines.append(f"P[{i}]: {text}  ===>  {converted}")
        
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

dump_all(firm_path, r"C:\Users\aksha\Documents\RM Generator\RM-Maker\scratch\firm_all.txt")
dump_all(gen_path, r"C:\Users\aksha\Documents\RM Generator\RM-Maker\scratch\generated_all.txt")
print("Saved all paragraphs to firm_all.txt and generated_all.txt")
