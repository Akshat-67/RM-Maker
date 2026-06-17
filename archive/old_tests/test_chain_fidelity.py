import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')

from modules.sd.extractor import SDDataExtractor
from modules.sd.narrative import generate_chain_narrative

def test_fidelity():
    session_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'cases', 'case_1781374115', 'session.json'))
    
    with open(session_path, 'r', encoding='utf-8') as f:
        session = json.load(f)
        
    data = session.get("data", {})
    title_chain = data.get("title_chain", [])
    
    print("=== Raw Extraction Events (Prior to test) ===")
    for idx, evt in enumerate(title_chain):
        print(f"Event {idx+1} ({evt.get('event_type')}):")
        print(f"  reg_book: {evt.get('reg_book')}")
        print(f"  reg_vol: {evt.get('reg_vol')}")
        print(f"  reg_page: {evt.get('reg_page')}")
        print(f"  reg_add_book: {evt.get('reg_add_book')}")
        print(f"  reg_add_vol: {evt.get('reg_add_vol')}")
        print(f"  reg_add_page: {evt.get('reg_add_page')}")
        print(f"  book_no: {evt.get('book_no')}")
        print(f"  volume_no: {evt.get('volume_no')}")
        print(f"  page_no: {evt.get('page_no')}")
        print(f"  additional_book_no: {evt.get('additional_book_no')}")
        print(f"  additional_volume_no: {evt.get('additional_volume_no')}")
        print(f"  additional_page_range: {evt.get('additional_page_range')}")
        
    print("\n=== Simulating Extractor Normalization ===")
    extractor = SDDataExtractor()
    # Mock normalizer call on title_chain
    # Let's manually set a range with "to" in reg_add_page to see if it survives
    title_chain[0]["reg_add_page"] = "1026 to 1039"
    title_chain[2]["reg_add_page"] = "494 to 507"
    title_chain[3]["reg_add_page"] = "796 to 813"
    
    extractor._normalize_list(data, "title_chain", [
        "event_type", "document_name", "document_number", "date", "consideration_amount", 
        "executant_name", "claimant_name", "reg_office", "reg_date", 
        "reg_book", "reg_vol", "reg_page", "reg_no", "reg_add_book", "reg_add_vol", "reg_add_page", 
        "book_no", "volume_no", "page_no", "additional_book_no", "additional_volume_no", "additional_page_range",
        "confidence", "source_text", "is_registered", "project_name", "unit_number", "field_sources"
    ])
    
    normalized_chain = data.get("title_chain", [])
    
    print("\n=== Normalized Events (After Alias Sync) ===")
    for idx, evt in enumerate(normalized_chain):
        print(f"Event {idx+1} ({evt.get('event_type')}):")
        print(f"  reg_book: {evt.get('reg_book')} <-> book_no: {evt.get('book_no')}")
        print(f"  reg_vol: {evt.get('reg_vol')} <-> volume_no: {evt.get('volume_no')}")
        print(f"  reg_page: {evt.get('reg_page')} <-> page_no: {evt.get('page_no')}")
        print(f"  reg_add_book: {evt.get('reg_add_book')} <-> additional_book_no: {evt.get('additional_book_no')}")
        print(f"  reg_add_vol: {evt.get('reg_add_vol')} <-> additional_volume_no: {evt.get('additional_volume_no')}")
        print(f"  reg_add_page: {evt.get('reg_add_page')} <-> additional_page_range: {evt.get('additional_page_range')}")
        
    print("\n=== Generating Narratives ===")
    ps0 = data.get("ps", [{}])[0]
    paras = generate_chain_narrative(normalized_chain, property_details=ps0, context=data)
    
    print("\n=== Resulting Paragraphs ===")
    for idx, p in enumerate(paras):
        print(f"Paragraph {idx+1}:")
        print(f"  {p}")
        
    print("\n=== Checking Construction Event Metadata ===")
    for idx, evt in enumerate(normalized_chain):
        if evt.get("event_type") == "CONSTRUCTION":
            print("Construction Event field_sources:")
            print(json.dumps(evt.get("field_sources"), indent=2))

if __name__ == "__main__":
    test_fidelity()
