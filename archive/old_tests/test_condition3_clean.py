import os
import sys
import json
import re
from docx import Document

# Include root dir in sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extractor import DataExtractor
from template_tools.builder_core import DocManipulator, clean_mapping

TEST_DOC_PATH = "templates/SALE_DEED/manoj kumar & Monu kumari MW +EAST PART OF BALAJI NAGAR+SO PATTA+3REC+SD.docx"
WORKING_KEY = "AQ.Ab8RN6LT45vwhXCygf42E1_cCExGjyFvD95qNo1vQ37hC3ZnBQ"

def get_doc_text_clean(doc):
    chunks = []
    for part_name, part in DocManipulator.iter_story_parts(doc):
        for p in DocManipulator.iter_paragraphs_deep(part):
            if p.text.strip():
                chunks.append(p.text.strip())
    return "\n".join(chunks)

def count_placeholders(doc):
    count = 0
    tags = []
    for part_name, part in DocManipulator.iter_story_parts(doc):
        for p in DocManipulator.iter_paragraphs_deep(part):
            matches = re.findall(r"\{\{.*?\}\}", p.text)
            if matches:
                count += len(matches)
                tags.extend(matches)
    return count, tags

def extract_json_robust(text):
    if not text: return None
    
    # Pre-process raw text to escape double quotes inside keys/values
    # Look for code block or the whole dict
    m = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if m:
        text_to_clean = m.group(1)
    else:
        m_dict = re.search(r'(\{.*\})', text, re.DOTALL)
        if m_dict:
            text_to_clean = m_dict.group(1)
        else:
            return None
            
    cleaned_lines = []
    for line in text_to_clean.splitlines():
        match = re.search(r':\s*"(\{\{.*?\}\})"\s*(,?)\s*$', line)
        if match:
            tag = match.group(1)
            comma = match.group(2)
            left_part = line[:match.start()].strip()
            if left_part.startswith('"') and left_part.endswith('"'):
                raw_key = left_part[1:-1]
                escaped_key = raw_key.replace('"', '\\"')
                cleaned_line = f'  "{escaped_key}": "{tag}"{comma}'
                cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append(line)
        else:
            cleaned_lines.append(line)
            
    cleaned_text = "\n".join(cleaned_lines)
    
    try:
        return json.loads(cleaned_text)
    except Exception as e:
        print("JSON clean load failed:", e)
        # Try fallbacks
        try:
            m = re.search(r'(\{.*\})', text, re.DOTALL)
            if m: return json.loads(m.group(1))
        except:
            pass
    return None

def main():
    doc = Document(TEST_DOC_PATH)
    content = get_doc_text_clean(doc)
    
    schema_info = """
    - rd: Sale Date
    - amount: Figures
    - amount_words: Words
    - hypothecation: Bank Name if property is mortgaged
    - ss[i]: Sellers. n=Name, a=Age, c=Caste, r=Relation, rn=Rel Name, adr=Address, id=Aadhar, pan=PAN
    - bs[i]: Buyers. n=Name, a=Age, c=Caste, r=Relation, rn=Rel Name, adr=Address, id=Aadhar, pan=PAN
    - ws[i]: Witnesses. n=Name, r=Relation, rn=Relative Name, adr=Address
    - ps[0]: Property details. plot_no, scheme, village, tehsil, dist, land_area, const_area, unit, adr, n, s, e, w
    - title_chain[i]: Title chain transitions. owner, deed_type, date, book, vol, page, reg_no, add_book
    - reg: {office, book, vol, page, reg_no, reg_date}
    """
    
    prompt = f"""
    CRITICAL MISSION: CONVERT COMPLETED DOCUMENT TO MASTER JINJA2 TEMPLATE.
    Identify ALL case-specific variable fields in the text below and map them to our system tags.

    MODE: SD
    CORE TAG SCHEMA:
    {schema_info}

    Return ONLY a JSON dictionary where keys are EXACT text from the document and values are the tags.
    Example: {{"24th March 2026": "{{{{rd}}}}", "15,00,000": "{{{{ls[0].a}}}}"}}
    TEXT:
    {content}
    """
    
    extractor = DataExtractor(api_key=WORKING_KEY)
    
    print("\nAttempting AI discovery...")
    raw = extractor.raw_generate(prompt, "gemini-2.5-flash")
    if not raw:
        print("Failed to get response from AI.")
        return
        
    mapping = extract_json_robust(raw) or {}
    clean = clean_mapping(mapping)
    
    print(f"AI discovered {len(clean)} fields.")
    
    # Generate template without heuristics
    doc = Document(TEST_DOC_PATH)
    reps = sorted(clean.items(), key=lambda x: len(x[0]), reverse=True)
    for part_name, part in DocManipulator.iter_story_parts(doc):
        for p in DocManipulator.iter_paragraphs_deep(part):
            for old, new in reps:
                if "{{" in p.text: continue
                DocManipulator.safe_replace(p, old, new)
                
    placeholder_count, tags = count_placeholders(doc)
    print(f"Template contains {placeholder_count} placeholders.")
    print("Unique placeholders found:", set(tags))
    
    # Save the output to verify
    output_path = "temp_builder/MASTER_TEMPLATE_TEST_CONDITION3.docx"
    doc.save(output_path)
    print(f"Saved test template to {output_path}")

if __name__ == "__main__":
    main()
