from docx import Document
import os

files = [
    "templates/SALE_DEED/SD_JDA_2SD_Flat_2S_1B.docx",
    "templates/SALE_DEED/Balkishan Yadav & Vinod Gurjar MM PNo 72 Shiv Enclave Vill Gawar Brahmani Sanganer.docx",
    "templates/SALE_DEED/manoj kumar & Monu kumari MW +EAST PART OF BALAJI NAGAR+SO PATTA+3REC+SD.docx"
]

for f_path in files:
    print(f"\n--- FILE: {os.path.basename(f_path)} ---")
    if not os.path.exists(f_path):
        print("ERROR: File not found.")
        continue
    try:
        doc = Document(f_path)
        # Just print the first 5000 characters to keep context clean
        text = "\n".join([p.text for p in doc.paragraphs])
        print(text[:5000])
    except Exception as e:
        print(f"ERROR reading docx: {e}")
