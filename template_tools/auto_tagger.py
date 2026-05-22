from docx import Document
import os

def replace_text_in_docx(doc, old_text, new_tag):
    """
    Search and replace text while trying to preserve formatting.
    Note: Simple search/replace in docx is tricky because of 'runs'.
    """
    for p in doc.paragraphs:
        if old_text in p.text:
            # We use a simple replacement for now, though it can break complex runs
            p.text = p.text.replace(old_text, new_tag)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if old_text in p.text:
                        p.text = p.text.replace(old_text, new_tag)

def tag_manju_devi(input_path, output_path):
    doc = Document(input_path)

    # Specific data from Manju Devi sample to replace with tags
    replacements = [
        # Borrowers
        ("Mrs. Manju Devi", "{{bs[0].n}}"),
        ("W/O: Puran Chand Bunkar", "W/O: {{bs[0].rn}}"),
        ("Mr. Pooran Chand Bunkar", "{{bs[1].n}}"),
        ("S/o Mr. Gullaram", "S/o {{bs[1].rn}}"),

        # Preamble dates
        ("29.04.2026", "{{ad}}"),
        ("21st day of May 2026", "{{rd}}"),

        # Loan details
        ("2090000", "{{ls[0].a}}"),
        ("Twenty Lakhs Ninety Thousand only", "{{ls[0].w}}"),
        ("26953", "{{ls[1].a}}"),
        ("Twenty-Six Thousand Nine Hundred and Fifty-Three only", "{{ls[1].w}}"),
        ("LHKWX00001765042", "{{ls[0].n}}"),

        # Bank Signatory
        ("Mr. Akash Sharma", "{{bsign.n}}"),
        ("S/o Mr. Govind Sharma", "S/o {{bsign.rn}}"),
    ]

    for old, new in replacements:
        replace_text_in_docx(doc, old, new)

    doc.save(output_path)
    print(f"Created Master Template: {output_path}")

if __name__ == "__main__":
    # Create the Master Template for Manju Devi
    sample_path = "icici_repo_temp/icici_templates/RM_MANJU DEVI.docx"
    master_path = "template_tools/MASTER_ICICI_MANJU_DEVI.docx"
    if os.path.exists(sample_path):
        tag_manju_devi(sample_path, master_path)
    else:
        print(f"Sample not found at {sample_path}")
