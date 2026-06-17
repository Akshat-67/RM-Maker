import zipfile
import re

def get_tags(filename):
    with zipfile.ZipFile(filename) as zf:
        for name in zf.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                xml = zf.read(name).decode("utf-8", errors="ignore")
                # Find all {{ ... }}
                tags = re.findall(r"\{\{([^}]+)\}\}", xml)
                for t in tags:
                    print(t.strip())

if __name__ == "__main__":
    template_path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat_unicode (1)_devlys.docx"
    get_tags(template_path)
