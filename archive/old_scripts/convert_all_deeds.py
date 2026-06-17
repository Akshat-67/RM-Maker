import os
import sys
from docx import Document

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.devlys_to_unicode import DevLysToUnicodeConverter

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    deed_dir = "templates/SALE_DEED"
    deeds = [
        "Balkishan Yadav & Vinod Gurjar MM PNo 72 Shiv Enclave Vill Gawar Brahmani Sanganer.docx",
        "Ganesh Pareek & hansa Devi MW P NO 35-B Krishna Vihar village BadhShyaopura vatika Road BT.docx",
        "SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat.docx",
        "manoj kumar & Monu kumari MW +EAST PART OF BALAJI NAGAR+SO PATTA+3REC+SD.docx"
    ]

    for deed in deeds:
        input_path = os.path.join(deed_dir, deed)
        output_path = os.path.join("scratch", f"conv_{deed}")
        
        print(f"\n==========================================")
        print(f"Converting: {deed}")
        print(f"==========================================")
        
        if not os.path.exists(input_path):
            print("File not found!")
            continue

        try:
            DevLysToUnicodeConverter.convert_docx(input_path, output_path)
            print(f"Successfully converted to {output_path}")
            
            doc = Document(output_path)
            # Find and print some sample converted runs
            print("Sample paragraph texts:")
            count = 0
            for i, p in enumerate(doc.paragraphs):
                text = p.text.strip()
                if text:
                    print(f"  P{i}: {text[:100]}...")
                    count += 1
                    if count >= 3:
                        break
        except Exception as e:
            print(f"Error converting {deed}: {e}")

if __name__ == "__main__":
    main()
