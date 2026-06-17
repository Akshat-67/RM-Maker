import sys, json, difflib
from docx import Document
sys.path.insert(0, '.')
from utils.helpers import KrutiDev_to_Unicode

def get_decoded_text(path):
    doc = Document(path)
    paras = []
    for p in doc.paragraphs:
        t = p.text.strip().replace('~~HL~~', '')
        if t:
            dev_count = sum('\u0900' <= c <= '\u097f' for c in t)
            asc_count = sum('a' <= c.lower() <= 'z' for c in t)
            if dev_count > asc_count:
                paras.append(t)
            else:
                try:
                    paras.append(KrutiDev_to_Unicode(t))
                except:
                    paras.append(t)
    return paras

ai = get_decoded_text(r'cases\case_1781374115\Generated_AI_Test3.docx')
actual = get_decoded_text(r'Test\ACTUAL.docx')

with open('scratch/debug_sim.json', 'w', encoding='utf-8') as f:
    json.dump({'ai': ai, 'actual': actual}, f, ensure_ascii=False, indent=2)

matcher = difflib.SequenceMatcher(None, ai, actual)
print(f"Similarity (lines): {matcher.ratio() * 100:.2f}%")
