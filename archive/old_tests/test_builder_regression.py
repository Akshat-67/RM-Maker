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

API_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4")
]
API_KEYS = list(dict.fromkeys([k for k in API_KEYS if k]))

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
    m = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if m:
        try: return json.loads(m.group(1))
        except: pass
    m = re.search(r'(\{.*\})', text, re.DOTALL)
    if m:
        try: return json.loads(m.group(1))
        except: pass
    return None

def test_condition_1_current(content):
    """Condition 1: Current prompt + Deterministic rules enabled"""
    print("\n--- Running Condition 1: Current Prompt + Deterministic Rules ---")
    
    schema_info = """
    - rd: Sale Date
    - amount: Figures
    - amount_words: Words
    - hypothecation: Bank Name if property is mortgaged
    - ss[i]: Sellers. n=Name, a=Age, c=Caste, r=Relation, rn=Rel Name, adr=Address, id=Aadhar, pan=PAN
    - bs[i]: Buyers. n=Name, a=Age, c=Caste, r=Relation, rn=Rel Name, adr=Address, id=Aadhar, pan=PAN
    - ws[i]: Witnesses. n=Name, r=Relation, rn=Relative Name, adr=Address
    - reg: {office, book, vol, page, reg_no, reg_date}
    
    NOTE: Large narrative sections (Title Chain, Property Address, Boundaries) are handled automatically. 
    ONLY identify short Case-specific entities.
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
    
    extractor = DataExtractor(api_keys=API_KEYS)
    raw = extractor.raw_generate(prompt, "gemini-2.5-flash")
    mapping = extract_json_robust(raw) or {}
    clean = clean_mapping(mapping)
    
    print(f"AI discovered {len(clean)} fields.")
    
    # Generate template with heuristics
    doc = Document(TEST_DOC_PATH)
    DocManipulator.apply_deterministic_rules(doc)
    reps = sorted(clean.items(), key=lambda x: len(x[0]), reverse=True)
    for part_name, part in DocManipulator.iter_story_parts(doc):
        for p in DocManipulator.iter_paragraphs_deep(part):
            for old, new in reps:
                if "{{" in p.text: continue
                DocManipulator.safe_replace(p, old, new)
                
    placeholder_count, tags = count_placeholders(doc)
    print(f"Template contains {placeholder_count} placeholders.")
    print("Placeholders:", set(tags))
    return clean, placeholder_count, set(tags)

def test_condition_2_no_heuristics(content):
    """Condition 2: Current prompt + Deterministic rules disabled"""
    print("\n--- Running Condition 2: Current Prompt + NO Deterministic Rules ---")
    
    schema_info = """
    - rd: Sale Date
    - amount: Figures
    - amount_words: Words
    - hypothecation: Bank Name if property is mortgaged
    - ss[i]: Sellers. n=Name, a=Age, c=Caste, r=Relation, rn=Rel Name, adr=Address, id=Aadhar, pan=PAN
    - bs[i]: Buyers. n=Name, a=Age, c=Caste, r=Relation, rn=Rel Name, adr=Address, id=Aadhar, pan=PAN
    - ws[i]: Witnesses. n=Name, r=Relation, rn=Relative Name, adr=Address
    - reg: {office, book, vol, page, reg_no, reg_date}
    
    NOTE: Large narrative sections (Title Chain, Property Address, Boundaries) are handled automatically. 
    ONLY identify short Case-specific entities.
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
    
    extractor = DataExtractor(api_keys=API_KEYS)
    raw = extractor.raw_generate(prompt, "gemini-2.5-flash")
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
    print("Placeholders:", set(tags))
    return clean, placeholder_count, set(tags)

def test_condition_3_granular(content):
    """Condition 3: Granular prompt (reverted) + NO Deterministic Rules"""
    print("\n--- Running Condition 3: Granular Prompt + NO Deterministic Rules ---")
    
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
    
    extractor = DataExtractor(api_keys=API_KEYS)
    raw = extractor.raw_generate(prompt, "gemini-2.5-flash")
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
    print("Placeholders:", set(tags))
    return clean, placeholder_count, set(tags)

if __name__ == "__main__":
    if not os.path.exists(TEST_DOC_PATH):
        print(f"Error: {TEST_DOC_PATH} not found.")
        sys.exit(1)
        
    doc = Document(TEST_DOC_PATH)
    content = get_doc_text_clean(doc)
    print(f"Loaded document {TEST_DOC_PATH}. Length: {len(content)}")
    
    res1 = test_condition_1_current(content)
    res2 = test_condition_2_no_heuristics(content)
    res3 = test_condition_3_granular(content)
    
    print("\n=================== AUDIT REPORT COMPARISON ===================")
    print(f"Condition 1 (Current, Heuristics): Discovered {len(res1[0])} mappings, {res1[1]} placeholders in output.")
    print(f"Condition 2 (Current, No Heur):   Discovered {len(res2[0])} mappings, {res2[1]} placeholders in output.")
    print(f"Condition 3 (Granular, No Heur):  Discovered {len(res3[0])} mappings, {res3[1]} placeholders in output.")
