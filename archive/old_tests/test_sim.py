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

matcher = difflib.SequenceMatcher(None, '\n'.join(ai), '\n'.join(actual))
sim = matcher.ratio() * 100

report = []
report.append(f'Similarity on decoded text: {sim:.2f}%\n')
report.append(f'AI paragraphs: {len(ai)}')
report.append(f'ACTUAL paragraphs: {len(actual)}\n')

report.append('--- Gaps ---')
for tag, i1, i2, j1, j2 in matcher.get_opcodes():
    if tag != 'equal':
        report.append(f'[{tag}] AI[{i1}:{i2}] vs ACTUAL[{j1}:{j2}]')
        if i2 > i1:
            snippet = ai[i1][:150] if i1 < len(ai) else "END_OF_DOC"
            report.append(f'  AI: {snippet}')
        if j2 > j1:
            snippet = actual[j1][:150] if j1 < len(actual) else "END_OF_DOC"
            report.append(f'  ACTUAL: {snippet}')
        report.append('')

with open(r'Test\sim_report.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))

print('Done')
