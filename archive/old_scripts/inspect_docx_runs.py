from docx import Document
import os

def main():
    f_path = "templates/SALE_DEED/manoj kumar & Monu kumari MW +EAST PART OF BALAJI NAGAR+SO PATTA+3REC+SD.docx"
    if not os.path.exists(f_path):
        print("File not found")
        return
    doc = Document(f_path)
    p = doc.paragraphs[22]
    print(f"Paragraph 22 raw text: {repr(p.text)}")
    for r_idx, r in enumerate(p.runs):
        print(f"Run {r_idx}: {repr(r.text)}")
        for c_idx, c in enumerate(r.text):
            print(f"  Char {c_idx}: {repr(c)} (code: {ord(c)})")

if __name__ == "__main__":
    main()
