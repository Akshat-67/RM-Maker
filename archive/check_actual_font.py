import docx
doc = docx.Document('Test/ACTUAL.docx')
for p in doc.paragraphs:
    if "vkt fnukad" in p.text:
        for run in p.runs:
            print(f"RUN TEXT: '{run.text}'")
            print(f"FONT: {run.font.name}")
