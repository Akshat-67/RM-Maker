import zipfile
import re

def search_in_docx(filename, search_text):
    with zipfile.ZipFile(filename) as zf:
        for name in zf.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                xml = zf.read(name).decode("utf-8", errors="ignore")
                index = xml.find(search_text)
                if index != -1:
                    print(f"Found in {name}:")
                    print(xml[index:index+1000])

if __name__ == "__main__":
    template_path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat_unicode (1)_devlys.docx"
    search_in_docx(template_path, "fuEu çdkj ls vnk dh xbZ gS %")
