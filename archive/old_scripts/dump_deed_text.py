import docx
import os
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat.docx"
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return

    doc = docx.Document(path)
    
    # We will use DocManipulator's logic to iterate over all story parts
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from template_tools.builder_core import DocManipulator
    
    content = DocManipulator.get_doc_content(doc)
    with open("scratch/benchmark_deed_text.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("Deed text dumped successfully to scratch/benchmark_deed_text.txt. Length:", len(content))

if __name__ == "__main__":
    main()
