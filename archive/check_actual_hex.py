import docx
doc = docx.Document('Test/ACTUAL.docx')
for p in doc.paragraphs:
    if "vkt fnukad" in p.text:
        text = p.text
        # find the date part
        import re
        m = re.search(r'\d+.\d+.\d+', text)
        if m:
            date_str = m.group(0)
            print(f"ACTUAL DATE: '{date_str}'")
            print(f"HEX: {' '.join(hex(ord(c)) for c in date_str)}")
