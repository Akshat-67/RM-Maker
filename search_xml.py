import zipfile
import re
import sys

def search_in_docx(filename, search_text):
    with zipfile.ZipFile(filename) as zf:
        for name in zf.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                xml = zf.read(name).decode("utf-8", errors="ignore")
                index = xml.find(search_text)
                if index != -1:
                    print(f"Found in {name}:")
                    # Show more context
                    print(xml[max(0, index-500):min(len(xml), index+1000)])

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python search_xml.py <docx_file> <text>")
    else:
        search_in_docx(sys.argv[1], sys.argv[2])
