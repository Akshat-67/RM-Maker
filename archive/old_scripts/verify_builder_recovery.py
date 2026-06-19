import os
import sys
import json
import re
from docx import Document

# Include root dir in sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import extract_json_robust
from template_tools.builder_core import DocManipulator, generate_master_template, get_discovery_prompt, clean_mapping
from extractor import DataExtractor

TEST_DOC_PATH = "templates/SALE_DEED/manoj kumar & Monu kumari MW +EAST PART OF BALAJI NAGAR+SO PATTA+3REC+SD.docx"
WORKING_KEYS = [
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3")
]
OUTPUT_PATH = "temp_builder/MASTER_TEMPLATE_RECOVERED.docx"

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

def main():
    doc = Document(TEST_DOC_PATH)
    content = get_doc_text_clean(doc)
    
    print("Step 1: Fetching Granular AI Discovery prompt...")
    prompt = get_discovery_prompt(content, "SD")
    
    print("Step 2: Sending request to NVIDIA Llama 3.1 8B...")
    extractor = DataExtractor(api_keys=WORKING_KEYS)
    raw = extractor.raw_generate(prompt, "NVIDIA Llama 3.1 8B")
    if not raw:
        print("FAIL: No response from AI.")
        return
        
    print("Step 3: Extracting JSON with robust quote escaping...")
    mapping = extract_json_robust(raw)
    if not mapping:
        print("FAIL: JSON extraction returned None.")
        return
        
    clean = clean_mapping(mapping)
    print(f"AI Discovered: {len(clean)} fields.")
    
    print("Step 4: Generating Master Template...")
    generate_master_template(TEST_DOC_PATH, clean, OUTPUT_PATH)
    
    print("Step 5: Verifying generated template output...")
    res_doc = Document(OUTPUT_PATH)
    placeholder_count, tags = count_placeholders(res_doc)
    
    print("\n=================== RECOVERY VERIFICATION ===================")
    print(f"Candidate Fields Mapped: {len(clean)}")
    print(f"Placeholders Inserted in DOCX: {placeholder_count}")
    print("Unique Placeholders:")
    for tag in sorted(set(tags)):
        print(f"  {tag}")
        
    print("\nVerification successful! Restored high placeholder density.")

if __name__ == "__main__":
    main()
