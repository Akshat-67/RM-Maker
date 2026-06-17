import os
from docx import Document

def extract_text(filepath):
    doc = Document(filepath)
    text = []
    for p in doc.paragraphs:
        t = p.text.strip()
        if t:
            text.append(t)
    return "\n".join(text)

files = [
    "Reference Materials/Sale Deed/PLOT/Balkishan Yadav & Vinod Gurjar MM PNo 72 Shiv Enclave Vill Gawar Brahmani Sanganer.docx",
    "Reference Materials/Sale Deed/FLAT/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat.docx"
]

for f in files:
    try:
        print(f"\n--- File: {f} ---")
        text = extract_text(f)
        # We know it's DevLys, let's print lines that likely contain dates or registration details 
        # Registration details in DevLys often contain numbers or words like "cgh" (bahi/book), "ftYn" (jild/vol), "i`" (prishth/page).
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if "ftYn" in line or "cgh" in line or "i`" in line or "fnukad" in line: # fnukad = dinank (date)
                print(f"Line {i}: {line}")
    except Exception as e:
        print(f"Error: {e}")
