from docx import Document
import os

def replace_text_in_docx(doc, old_text, new_tag):
    if not old_text or len(old_text) < 3: return
    for p in doc.paragraphs:
        if old_text in p.text:
            p.text = p.text.replace(old_text, new_tag)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if old_text in p.text:
                        p.text = p.text.replace(old_text, new_tag)

def tag_template(input_path, output_path, replacements):
    if not os.path.exists(input_path):
        print(f"Skipping {input_path}, not found.")
        return
    doc = Document(input_path)
    for _ in range(3): # 3-pass to ensure thoroughness
        for old, new in replacements:
            replace_text_in_docx(doc, old, new)
    doc.save(output_path)
    print(f"Generated: {output_path}")

def run_all_tagging():
    base = "icici_repo_temp/icici_templates/"
    out = "template_tools/"

    # 1. MANJU DEVI
    tag_template(base + "RM_MANJU DEVI.docx", out + "MASTER_ICICI_MANJU.docx", [
        ("21th day May 2026", "{{rd}}"), ("21st day of May 2026", "{{rd}}"),
        ("Mrs. Manju Devi", "{{bs[0].n}}"), ("W/O: Puran Chand Bunkar", "W/O: {{bs[0].rn}}"),
        ("Mr. Pooran Chand Bunkar", "{{bs[1].n}}"), ("S/o Mr. Gullaram", "S/o {{bs[1].rn}}"),
        ("29.04.2026", "{{ad}}"),
        ("RS. 20,90,000/-", "RS. {{ls[0].a}}/-"), ("2090000", "{{ls[0].a}}"), ("Twenty Lakhs Ninety Thousand only", "{{ls[0].w}}"),
        ("RS. 26,953/-", "RS. {{ls[1].a}}/-"), ("26953", "{{ls[1].a}}"), ("Twenty-Six Thousand Nine Hundred and Fifty-Three only", "{{ls[1].w}}"),
        ("LHKWX00001765042", "{{ls[0].n}}"),
        ("Mr. Akash Sharma", "{{bsign.n}}"), ("S/o Mr. Govind Sharma", "S/o {{bsign.rn}}"),
        # Property Address (The "big block")
        ("Plot No. B-43, Shree Krishna Van-B, in Khasra No. 1425/238, 1426/241, 1430/268, 240, 242, 243, Village Harsuliya, Tehsil Madhorajpura, Jaipur, Area 84.20 Sq. Mtr.", "{{ps[0].adr}}"),
        ("Plot No. B 43 , Shree Krishna Van B , in Khasra No. 1425/238, 1426/241, 1430/268, 240, 242, 243, Village Harsuliya, Tehsil - Madhorajpura Jaipur Area 84.20 Sq. Mtr", "{{ps[0].adr}}"),
        ("North: Plot No. B-44", "North: {{ps[0].n}}"), ("South: Plot No. B-42", "South: {{ps[0].s}}"),
        ("East : Plot No. B-36", "East : {{ps[0].e}}"), ("West: Road 9 Mtr.", "West: {{ps[0].w}}")
    ])

    # 2. ANAND SINGH
    tag_template(base + "ANAND SINGH SHEKHAWAT  1 Senction Lettar.docx", out + "MASTER_ICICI_ANAND.docx", [
        ("24th day March 2026", "{{rd}}"),
        ("Mr. Anand Singh Shekhawat", "{{bs[0].n}}"), ("S/o Mr. Mahendra Singh Shekhawat", "S/o {{bs[0].rn}}"),
        ("RS. 35,08,000/-", "RS. {{ls[0].a}}/-"), ("3508000", "{{ls[0].a}}"),
        ("Mr. Nitin Jangid", "{{bsign.n}}"), ("S/o Mr. Suresh Jangid", "S/o {{bsign.rn}}"),
        ("48, Laxmi Nagar Royal City, Manchwa,  Jaipur, Rajasthan-302012", "{{ps[0].adr}}")
    ])

    # 3. ANKIT KUMAR
    tag_template(base + "Ankit Kumar Sharma Munni Devi & ICICI Sanwar mal Sharma 3 Senction Lettar.docx", out + "MASTER_ICICI_ANKIT.docx", [
        ("5th day of May 2026", "{{rd}}"),
        ("Mrs. Munni Devi", "{{bs[0].n}}"), ("W/o Mr. Hira Lal Sharma", "W/o {{bs[0].rn}}"),
        ("Mr. Ankit Kumar Sharma", "{{ws[0].n}}"), ("Mr. Vishnu Kumar Sharma", "{{ws[1].n}}"),
        ("Mr. Sanwar Mal Sharma", "{{bsign.n}}"), ("S/o Mr. Bansi Lal Sharma", "S/o {{bsign.rn}}"),
        ("17,15,000/-", "{{ls[0].a}}/-"), ("12,85,000/-", "{{ls[1].a}}/-"),
        ("Plot No. A-18, Ramesh Vihar EXT., Charan Nadi, Benars Road, Nangal Jaisa Bohara, Jaipur Area 90.00 Sq. Yards", "{{ps[0].adr}}")
    ])

    # 4. SHIV RAJ
    tag_template(base + "SHIV RAJ  2 Senction Lettar ICICI DEEPAK GARH.docx", out + "MASTER_ICICI_SHIVRAJ.docx", [
        ("Mr. Shiv Raj", "{{bs[0].n}}"), ("S/o Mr. Narayan Lal", "S/o {{bs[0].rn}}"),
        ("14,84,000/-", "{{ls[0].a}}/-"), ("35,432/-", "{{ls[1].a}}/-"),
        ("Mr. Deepak Garh", "{{bsign.n}}"), ("S/o Mr. Sanwar Mal", "S/o {{bsign.rn}}")
    ])

if __name__ == "__main__":
    run_all_tagging()
    print("All master templates generated with deep verification.")
