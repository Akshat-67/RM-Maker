import docx
doc = docx.Document('Test/ACTUAL.docx')
for p in doc.paragraphs:
    if "vkt fnukad" in p.text:
        # Get the run containing the date
        for run in p.runs:
            if "-" in run.text:
                print(f"RUN TEXT: '{run.text}'")
                print(f"HEX: {' '.join(hex(ord(c)) for c in run.text)}")
