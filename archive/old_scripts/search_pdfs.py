import os
import re

pdf_files = [
    r"cases\case_1781374115\files\seller OCR - dharmendra.pdf",
    r"cases\case_1781374115\files\lsr 1 - dharmendra.pdf",
    r"cases\case_1781374115\files\dharmendra singh_Legal & Technical_Legal Report_1.pdf",
    r"cases\case_1781374115\files\dharmendra singh_Legal & Technical_Technical Report_1.pdf",
    r"cases\case_1781374115\files\ATS - dharmendra.pdf",
]

def search_with_pdfplumber():
    try:
        import pdfplumber
        print("Using pdfplumber:")
        for path in pdf_files:
            if not os.path.exists(path):
                print(f"File not found: {path}")
                continue
            print(f"\nSearching in {os.path.basename(path)}...")
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text:
                        continue
                    for line in text.split("\n"):
                        if "ज्वारा" in line or "Jwara" in line or "Madhuban" in line or "मधुबन" in line or "Sohan" in line or "सोहन" in line:
                            print(f"Page {i+1}: {line}")
    except ImportError:
        print("pdfplumber not installed")

def search_with_pypdf():
    try:
        import pypdf
        print("\nUsing pypdf:")
        for path in pdf_files:
            if not os.path.exists(path):
                continue
            print(f"\nSearching in {os.path.basename(path)}...")
            reader = pypdf.PdfReader(path)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text:
                    continue
                for line in text.split("\n"):
                    if "ज्वारा" in line or "Jwara" in line or "Madhuban" in line or "मधुबन" in line or "Sohan" in line or "सोहन" in line:
                        print(f"Page {i+1}: {line}")
    except ImportError:
        print("pypdf not installed")

def search_with_fitz():
    try:
        import fitz  # PyMuPDF
        print("\nUsing PyMuPDF:")
        for path in pdf_files:
            if not os.path.exists(path):
                continue
            print(f"\nSearching in {os.path.basename(path)}...")
            doc = fitz.open(path)
            for i, page in enumerate(doc):
                text = page.get_text()
                if not text:
                    continue
                for line in text.split("\n"):
                    if "ज्वारा" in line or "Jwara" in line or "Madhuban" in line or "मधुबन" in line or "Sohan" in line or "सोहन" in line:
                        print(f"Page {i+1}: {line}")
    except ImportError:
        print("PyMuPDF not installed")

if __name__ == "__main__":
    search_with_pdfplumber()
    search_with_pypdf()
    search_with_fitz()
