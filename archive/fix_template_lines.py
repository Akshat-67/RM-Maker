import docx

def fix_template_lines():
    path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat_unicode (1)_devlys.docx"
    doc = docx.Document(path)
    
    # Identify empty paragraphs between witnesses and drafter
    # Witnesses end with {{w2.aadhaar}}
    found_w2 = False
    to_delete = []
    for i, p in enumerate(doc.paragraphs):
        if "{{w2.aadhaar}}" in p.text:
            found_w2 = True
            continue
        if found_w2:
            if p.text.strip() == "":
                to_delete.append(p)
            elif "Drafted By" in p.text:
                break
                
    # Delete them
    for p in to_delete:
        p_element = p._p
        p_element.getparent().remove(p_element)
        
    doc.save(path)
    print("Template lines cleaned.")

if __name__ == "__main__":
    fix_template_lines()
