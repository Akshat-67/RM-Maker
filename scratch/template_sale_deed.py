import docx
import re
import os

template_path = "templates/SALE_DEED/SD_JDA_2SD_Flat_2S_1B.docx"
doc = docx.Document(template_path)

# Dictionary of exact DevLys / completed strings to replace with English Jinja2 tags
# Using triple quotes for strings containing double quotes or other special characters
replacements = [
    # Seller 1 details
    (r"ySV ua- 101] QLVZ ¶yksj] Hkxorh jkt vikVZesUV] 9 nsoh fudsru dEikm.M] ljnkj iVsy jksM+] t;iqj jktLFkku&302001", "{{sellers[0].adr}}"),
    (r"Lo- Jh ts-ch- lDlSuk", "{{sellers[0].r}} {{sellers[0].rn}}"),
    (r"Jh foosd lDlSuk", "{{sellers[0].n}}"),
    ("5564 0963 9476", "{{sellers[0].id}}"),
    ("AKHPS7097L", "{{sellers[0].pan}}"),
    
    # Seller 2 details
    ("""Vh&28] th-ih-vkj-,- dkWyksuh] Vkbi&4] lsDVj uEcj 26] vkdqMhZ jsyos LVs'ku ds ikl] fuxM+h] çkf/kdj.k] iq.ks] egkjk"Vª&411044""", "{{sellers[1].adr}}"),
    (r"iRuh Jh foosd lDlSuk", "{{sellers[1].r}} {{sellers[1].rn}}"),
    (r"lquhrk lDlsuk", "{{sellers[1].n}}"), 
    ("6267 4409 8295", "{{sellers[1].id}}"),
    ("BSOPS8468K", "{{sellers[1].pan}}"),

    # Buyer 1 details
    (r",Q- u- 115&,] ?kj vkaxu vikjVesaV] eqgkuk] t;iqj] jktLFkku& 302029", "{{buyers[0].adr}}"),
    (r"iRuh Jh /kesZUæ flag", "{{buyers[0].r}} {{buyers[0].rn}}"),
    (r"fot; y{eh", "{{buyers[0].n}}"),
    ("6693 2771 2261", "{{buyers[0].id}}"),
    ("BQOPL5182P", "{{buyers[0].pan}}"),

    # Property details
    ("""vkoklh; ¶ySV uEcj ,l&1] lSd.M ¶yksj] Jh lkabZ jsthMsUlh & f}rh;] IykV ua& ,&24] —".kiqjh] xzke cnjokl] vtesj jksM] t;iqj] jktLFkku""", "{{ps[0].adr}}"),
    ("1087-19", "{{ps[0].area}}"),
    ("oxZQhV", "{{ps[0].area_unit}}"),

    # Title Chain JDA Registry
    ("11-07-2019", "{{chain[0].d}}"),
    ("iqLrd la[;k 01", "iqLrd la[;k {{chain[0].b_no}}"),
    ("ftYn la[;k 544", "ftYn la[;k {{chain[0].v_no}}"),
    ("""i`"B la[;k 140""", """i`"B la[;k {{chain[0].p_no}}"""),
    ("Øe la[;k 201903021106599", "Øe la[;k {{chain[0].r_no}}"),

    # Witnesses details
    ("iqr Jh vyguwj", "{{ws[0].r}} {{ws[0].rn}}"),
    ("lqYrku", "{{ws[0].n}}"),
    ("410 deyk usg: uxj] 'kkafr uxj] gluiqjk] t;iqj] LVs'ku jksM] t;iqj] jktLFkku&302006", "{{ws[0].adr}}"),
    ("4493 8314 4916", "{{ws[0].id}}"),

    ("iqr Jh nkÅn;ky", "{{ws[1].r}} {{ws[1].rn}}"),
    ("iou dqekj", "{{ws[1].n}}"),
    ("¶ySV u- ,y th&1 yksvj] fouk;d vkiVZesaV] fouk;d fogkj] x.kiriqjk] Hkkjr ekrk lfdZy] t;iqj] jktLFkku&302020", "{{ws[1].adr}}"),
    
    # Table 0 Payments
    ("20,000/-", "{{payments[0].a}}"),
    ("18.05.2016", "{{payments[0].d}}"),
    
    ("4,80,000/-", "{{payments[1].a}}"),
    ("IMPS-613611327488", "{{payments[1].n}}"),
    ("16.05.2026", "{{payments[1].d}}"),
    
    ("15,00,000/-", "{{payments[2].a}}"),
    ("DN-05-2026-555495 Cheque No.849938", "{{payments[2].n}}"),
    ("20.05.2026", "{{payments[2].d}}"),

    # Execution Date
    ("25-05-2026", "{{rd}}")
]

def replace_in_text(text):
    for old, new in replacements:
        text = text.replace(old, new)
    return text

# Apply to paragraphs
for p in doc.paragraphs:
    # Target Seller 1 & 2 ages in paragraph 21
    if "foosd lDlSuk" in p.text or "lquhrk lDlsuk" in p.text:
        # Paragraph 21 has both Sellers names and ages
        # Split or replace manually:
        p.text = p.text.replace("""vk;q 58 o"kZ tkfr fgUnq] fuoklh%& ¶ySV ua- 101""", """vk;q {{sellers[0].a}} o"kZ tkfr fgUnq] fuoklh%& {{sellers[0].adr}}""")
        p.text = p.text.replace("""vk;q 58 o"kZ tkfr fgUnq] fuoklh%& Vh&28""", """vk;q {{sellers[1].a}} o"kZ tkfr fgUnq] fuoklh%& {{sellers[1].adr}}""")
    
    if "fot; y{eh" in p.text:
        # Paragraph 25 has Buyer age
        p.text = p.text.replace("""vk;q 25 o"kZ""", """vk;q {{buyers[0].a}} o"kZ""")

    p.text = replace_in_text(p.text)

# Apply to tables
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            # Check cell contents
            cell.text = replace_in_text(cell.text)
            
            # Special check for CASH cell in Table 0
            if cell.text.strip() == "CASH":
                cell.text = "{{payments[0].n}}"

# Save the updated doc back
doc.save(template_path)
print("Sale Deed template successfully compiled with Jinja2 placeholders!")
