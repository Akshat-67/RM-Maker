import docx

def revert_template():
    path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat_unicode (1)_devlys.docx"
    doc = docx.Document(path)
    
    # 1. Restore 'para' placeholder
    for p in doc.paragraphs:
        if "{% p for line in paragraphs %}" in p.text:
            p.text = "{{para}}"
            print("Template restored with {{para}}.")
            
    # 2. Add back dimension paragraph (P6)
    # Actually, I'll keep it removed if it's redundant.
    # But for de-overfitting, I should keep the template as generic as possible.
    
    doc.save(path)

if __name__ == "__main__":
    revert_template()
