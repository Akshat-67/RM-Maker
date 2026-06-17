import sys
import os
from docx import Document

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.devlys_to_unicode import DevLysToUnicodeConverter

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    input_deed = r"templates/SALE_DEED/manoj kumar & Monu kumari MW +EAST PART OF BALAJI NAGAR+SO PATTA+3REC+SD.docx"
    doc = Document(input_deed)

    print("Testing is_likely_english on all paragraphs:")
    falsely_classified = 0
    total_non_empty = 0

    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if not text:
            continue
        total_non_empty += 1
        
        is_eng = DevLysToUnicodeConverter.is_likely_english(text)
        if is_eng:
            # We check if it actually looks like English or DevLys
            # English usually contains normal English words, DevLys has Remington keys
            # Let's print it
            print(f"P{i:2d} classified as ENGLISH: {repr(text)}")
            falsely_classified += 1
            
    print(f"\nSummary: Total non-empty paragraphs: {total_non_empty}, Classified as English: {falsely_classified}")

if __name__ == "__main__":
    main()
