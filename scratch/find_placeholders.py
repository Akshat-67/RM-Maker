import zipfile
import re
import os

template_path = "templates/SALE_DEED/SD_JDA_2SD_Flat_2S_1B.docx"

if not os.path.exists(template_path):
    print("Template not found at", template_path)
    exit(1)

placeholders = set()
with zipfile.ZipFile(template_path) as zf:
    for name in zf.namelist():
        if name == "word/document.xml":
            xml = zf.read(name).decode("utf-8", errors="ignore")
            plain_text = re.sub(r"<[^>]+>", "", xml)
            found = re.findall(r"\{\{([^}]+)\}\}", plain_text)
            for f in found:
                placeholders.add(f.strip())

print("--- PLACEHOLDERS FOUND IN SALE DEED TEMPLATE ---")
for p in sorted(list(placeholders)):
    print(p)
