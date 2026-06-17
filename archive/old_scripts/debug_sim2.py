import sys
sys.path.insert(0, '.')
from utils.helpers import KrutiDev_to_Unicode
from docx import Document

doc = Document(r'cases\case_1781374115\Generated_AI_Test3.docx')
for i, p in enumerate(doc.paragraphs):
    t = p.text.strip().replace('~~HL~~', '')
    if not t: continue
    if any('\u0900' <= c <= '\u097f' for c in t): continue
    try:
        KrutiDev_to_Unicode(t)
    except Exception as e:
        print(f"Exception at {i}: {e}")
