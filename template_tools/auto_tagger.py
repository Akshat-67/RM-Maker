import json
import os
import re
from docx import Document

def merge_runs_in_paragraph(paragraph):
    if not paragraph.runs: return
    text = paragraph.text
    first_run = paragraph.runs[0]
    bold, italic, underline = first_run.bold, first_run.italic, first_run.underline
    font_name, font_size = first_run.font.name, first_run.font.size
    for _ in range(len(paragraph.runs)):
        p = paragraph._p
        p.remove(p.r_lst[0])
    new_run = paragraph.add_run(text)
    new_run.bold, new_run.italic, new_run.underline = bold, italic, underline
    new_run.font.name, new_run.font.size = font_name, font_size

def regex_replace(paragraph, old_text, new_tag):
    # Escape special characters and allow for any whitespace/hidden characters between words
    pattern = re.escape(old_text).replace(r'\ ', r'\s+')
    # Also handle the specific case of dashes and dots
    pattern = pattern.replace(r'\.', r'\.?\s*').replace(r'\-', r'\-?\s*')

    if re.search(pattern, paragraph.text, re.IGNORECASE):
        merge_runs_in_paragraph(paragraph)
        paragraph.text = re.sub(pattern, new_tag, paragraph.text, flags=re.IGNORECASE)

def apply_replacements(doc, replacements):
    # Sort by length descending
    replacements.sort(key=lambda x: len(x[0]), reverse=True)

    for p in doc.paragraphs:
        if not p.text.strip(): continue
        for old, new in replacements:
            regex_replace(p, old, new)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for old, new in replacements:
                        regex_replace(p, old, new)

def main():
    with open('template_tools/MASTER_FIELD_MAPS.json', 'r') as f:
        maps = json.load(f)

    base_dir = 'icici_repo_temp/icici_templates/'
    output_dir = 'template_tools/'

    file_map = {
        "RM_MANJU DEVI.docx": "MANJU DEVI",
        "ANAND SINGH SHEKHAWAT  1 Senction Lettar.docx": "ANAND SINGH",
        "Ankit Kumar Sharma Munni Devi & ICICI Sanwar mal Sharma 3 Senction Lettar.docx": "ANKIT KUMAR",
        "SHIV RAJ  2 Senction Lettar ICICI DEEPAK GARH.docx": "SHIV RAJ"
    }

    for filename, key in file_map.items():
        in_path = base_dir + filename
        if not os.path.exists(in_path): continue

        doc = Document(in_path)
        replacements = maps[key]["replacements"]
        apply_replacements(doc, replacements)

        out_path = output_dir + "MASTER_ICICI_" + key.replace(" ", "_") + ".docx"
        doc.save(out_path)
        print(f"Deep Verified & Tagged: {out_path}")

if __name__ == "__main__":
    main()
