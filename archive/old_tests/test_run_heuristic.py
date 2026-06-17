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

    print("Testing is_likely_english on all runs:")
    total_runs = 0
    english_runs = 0

    for i, p in enumerate(doc.paragraphs):
        # Merge runs just like the converter does
        DevLysToUnicodeConverter.merge_runs_compatible(p)
        for r_idx, r in enumerate(p.runs):
            text = r.text
            if not text or not text.strip():
                continue
            total_runs += 1
            is_eng = DevLysToUnicodeConverter.is_likely_english(text)
            if is_eng:
                # Check if it was DevLys font name
                has_devlys_font = False
                if r.font and r.font.name:
                    f_name = r.font.name.lower()
                    if "devlys" in f_name or "kruti" in f_name or "remington" in f_name:
                        has_devlys_font = True
                
                print(f"P{i:2d} Run{r_idx:2d} ({'DevLysFont' if has_devlys_font else 'NoDevLysFont'}) classified as English: {repr(text)}")
                english_runs += 1

    print(f"\nSummary: Total non-empty runs: {total_runs}, Classified as English: {english_runs}")

if __name__ == "__main__":
    main()
