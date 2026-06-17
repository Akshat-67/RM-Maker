import pypdf
import os

path = r"cases\case_1781374115\files\ATS - dharmendra.pdf"
if not os.path.exists(path):
    print("ATS file not found")
    exit(1)

reader = pypdf.PdfReader(path)
print(f"Total pages in ATS: {len(reader.pages)}")
text_sample = ""
for i, page in enumerate(reader.pages):
    t = page.extract_text()
    if t:
        text_sample += t + "\n"

print(f"Total extracted text length: {len(text_sample)}")
if text_sample:
    print("Sample text from ATS:")
    print(text_sample[:1000])
    
    # Check for keywords
    keywords = ["ज्वारा", "jwara", "madhuban", "मधुबन", "सोहन", "sohan"]
    for kw in keywords:
        if kw in text_sample or kw in text_sample.lower():
            print(f"Found keyword '{kw}' in ATS text!")
else:
    print("No text could be extracted from ATS (likely image-only PDF).")
