from docx import Document
import os

def smart_replace(doc, old_text, new_tag):
    """
    More robust replacement that handles cases where Word splits text into multiple runs.
    """
    if not old_text or len(old_text) < 3: return

    def replace_in_paragraphs(paragraphs):
        for p in paragraphs:
            if old_text in p.text:
                # Basic replacement first
                # If the text is simple and within one run, this works.
                # If it's split, we might need to clear runs and reset text.
                # To preserve formatting, we try to keep it simple.
                # If the whole text is exactly the old_text, we can preserve style.
                full_text = p.text
                new_text = full_text.replace(old_text, new_tag)

                # To minimize formatting loss, we only replace if found
                # Note: this simple method still has the 'run' limitation
                # but we will try to merge runs where possible.
                inline = p.runs
                combined = "".join([r.text for r in inline])
                if old_text in combined:
                    # Logic to handle split runs:
                    # For now, we use a slightly safer replacement:
                    p.text = new_text

    replace_in_paragraphs(doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                replace_in_paragraphs(cell.paragraphs)

def process_template(name, replacements):
    in_path = f"icici_repo_temp/icici_templates/{name}"
    out_path = f"template_tools/MASTER_ICICI_{name.split()[0]}.docx"

    if not os.path.exists(in_path):
        print(f"Not found: {in_path}")
        return

    doc = Document(in_path)
    # Sort replacements by length descending to avoid partial matches
    replacements.sort(key=lambda x: len(x[0]), reverse=True)

    for _ in range(5): # 5 passes for extra certainty
        for old, new in replacements:
            smart_replace(doc, old, new)

    doc.save(out_path)
    print(f"Finalized: {out_path}")

if __name__ == "__main__":
    # 1. MANJU DEVI
    process_template("RM_MANJU DEVI.docx", [
        ("Mrs. Manju Devi", "{{bs[0].n}}"),
        ("W/O: Puran Chand Bunkar", "W/O: {{bs[0].rn}}"),
        ("W/o Mr. Puran Chand Bunkar", "W/o {{bs[0].rn}}"),
        ("Age 40 Years", "Age {{bs[0].a}} Years"),
        ("50, sawai gatore, balaiyon ka mohalla, Jaipur, Malviya Nagar, Rajasthan, 302017", "{{bs[0].adr}}"),
        ("Mr. Pooran Chand Bunkar", "{{bs[1].n}}"),
        ("Mr. Puran Chand Bunkar", "{{bs[1].n}}"),
        ("S/o Mr. Gullaram", "S/o {{bs[1].rn}}"),
        ("near water tank girls school, swai getor jagatpura, Jaipur, PO:Malviya Nagar, DIST:Jaipur, Rajasthan, 302017", "{{bs[1].adr}}"),
        ("Plot No. B-43, Shree Krishna Van-B, in Khasra No. 1425/238, 1426/241, 1430/268, 240, 242, 243, Village Harsuliya, Tehsil Madhorajpura, Jaipur, Area 84.20 Sq. Mtr.", "{{ps[0].adr}}"),
        ("Plot No. B 43 , Shree Krishna Van B , in Khasra No. 1425/238, 1426/241, 1430/268, 240, 242, 243, Village Harsuliya, Tehsil - Madhorajpura Jaipur Area 84.20 Sq. Mtr", "{{ps[0].adr}}"),
        ("Plot No. B-43", "{{ps[0].n_short}}"),
        ("Plot No. B-44", "{{ps[1].n_short}}"),
        ("Plot No. B 4 4", "{{ps[1].n_short}}"),
        ("Plot No. B 43", "{{ps[0].n_short}}"),
        ("Shree Krishna Van-B", "{{ps[0].sch}}"),
        ("Shree Krishna Van B", "{{ps[0].sch}}"),
        ("29.04.2026", "{{ad}}"),
        ("21th day May 2026", "{{rd}}"),
        ("21st day of May 2026", "{{rd}}"),
        ("21.05.2025", "{{prev_reg_date}}"),
        ("2090000", "{{ls[0].a}}"),
        ("Twenty Lakhs Ninety Thousand only", "{{ls[0].w}}"),
        ("RS. 20,90,000/-", "RS. {{ls[0].a}}/-"),
        ("26953", "{{ls[1].a}}"),
        ("Twenty-Six Thousand Nine Hundred and Fifty-Three only", "{{ls[1].w}}"),
        ("RS. 26,953/-", "RS. {{ls[1].a}}/-"),
        ("180 Months", "{{ls[0].t}}"),
        ("120 Months", "{{ls[1].t}}"),
        ("LHKWX00001765042", "{{ls[0].n}}"),
        ("Mr. Akash Sharma", "{{bsign.n}}"),
        ("S/o Mr. Govind Sharma", "S/o {{bsign.rn}}"),
        ("North: Plot No. B-44", "North: {{ps[0].n}}"),
        ("South: Plot No. B-42", "South: {{ps[0].s}}"),
        ("East : Plot No. B-36", "East : {{ps[0].e}}"),
        ("West: Road 9 Mtr.", "West: {{ps[0].w}}"),
        ("Mrs. Guddi Devi", "{{ws[0].n}}"),
        ("W/O Mr. Nand Kishor", "W/O {{ws[0].rn}}"),
        ("1709, sanjay nagar, DCM, Ajmer Road, Heerapura, Jaipur, Rajasthan, 302021", "{{ws[0].adr}}"),
        ("Mr. Ravinder Kumar", "{{ws[1].n}}"),
        ("S/o Mr. Hari Shankar", "S/o {{ws[1].rn}}"),
        ("2659, gothwal bhawan, bhindo ka rasta, indra bazar, jaipur, jaipur, rajasthan - 302001", "{{ws[1].adr}}")
    ])

    # 2. ANAND SINGH
    process_template("ANAND SINGH SHEKHAWAT  1 Senction Lettar.docx", [
        ("Mr. Anand Singh Shekhawat", "{{bs[0].n}}"),
        ("S/o Mr. Mahendra Singh Shekhawat", "S/o {{bs[0].rn}}"),
        ("Age 36 Years", "Age {{bs[0].a}} Years"),
        ("48, Laxmi Nagar Royal City, Manchwa,  Jaipur, Rajasthan-302012", "{{bs[0].adr}}"),
        ("Plot No. 47 and 48 Scheme- Laxmi Nagar, Machwa, Kalwar Road, Jaipur total Area 95.47 SQ. Yds.", "{{ps[0].adr}}"),
        ("24th day March 2026", "{{rd}}"),
        ("24.04.2026", "{{ad}}"),
        ("35,08,000/-", "{{ls[0].a}}/-"),
        ("3508000", "{{ls[0].a}}"),
        ("Thirty Five Lakh Eight Thousand only", "{{ls[0].w}}"),
        ("180 Months", "{{ls[0].t}}"),
        ("77000254337", "{{ls[0].n}}"),
        ("Mr. Nitin Jangid", "{{bsign.n}}"),
        ("S/o Mr. Suresh Jangid", "S/o {{bsign.rn}}")
    ])

    # 3. ANKIT KUMAR
    process_template("Ankit Kumar Sharma Munni Devi & ICICI Sanwar mal Sharma 3 Senction Lettar.docx", [
        ("Mrs. Munni Devi", "{{bs[0].n}}"),
        ("W/o Mr. Hira Lal Sharma", "W/o {{bs[0].rn}}"),
        ("Ankit Kumar Sharma", "{{ws[0].n}}"),
        ("Vishnu Kumar Sharma", "{{ws[1].n}}"),
        ("Plot No. A-18, Ramesh Vihar EXT., Charan Nadi, Benars Road, Nangal Jaisa Bohara, Jaipur Area 90.00 Sq. Yards", "{{ps[0].adr}}"),
        ("5th day of May 2026", "{{rd}}"),
        ("27.03.2026", "{{ad}}"),
        ("17,15,000/-", "{{ls[0].a}}/-"),
        ("12,85,000/-", "{{ls[1].a}}/-"),
        ("43,181/-", "{{ls[2].a}}/-"),
        ("Rupees Seventeen Lakh Fifteen Thousand Only", "{{ls[0].w}}"),
        ("Rupees Twelve Lakh Eighty Five Thousand Only", "{{ls[1].w}}"),
        ("Rupees Forty Three Thousand One Hundred Eighty One Only", "{{ls[2].w}}"),
        ("77000237925", "{{ls[0].n}}"),
        ("77000237926", "{{ls[1].n}}"),
        ("77950050492", "{{ls[2].n}}"),
        ("Mr. Sanwar Mal Sharma", "{{bsign.n}}"),
        ("S/o Mr. Bansi Lal Sharma", "S/o {{bsign.rn}}")
    ])

    # 4. SHIV RAJ
    process_template("SHIV RAJ  2 Senction Lettar ICICI DEEPAK GARH.docx", [
        ("Mr. Shiv Raj", "{{bs[0].n}}"),
        ("S/o Mr. Narayan Lal", "S/o {{bs[0].rn}}"),
        ("14,84,000/-", "{{ls[0].a}}/-"),
        ("1484000", "{{ls[0].a}}"),
        ("35,432/-", "{{ls[1].a}}/-"),
        ("35432", "{{ls[1].a}}"),
        ("180 Months", "{{ls[0].t}}"),
        ("120 Months", "{{ls[1].t}}"),
        ("Mr. Deepak Garh", "{{bsign.n}}"),
        ("S/o Mr. Sanwar Mal", "S/o {{bsign.rn}}")
    ])
