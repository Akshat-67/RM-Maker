import json
from modules.sd.extractor import SDDataExtractor

def test_pipeline():
    with open('cases/case_1781374115/session.json', 'r', encoding='utf-8') as f:
        session = json.load(f)
    
    ps0 = session['data']['ps'][0]
    property_type = session.get('property_type', 'Plot')
    
    print(f"DEBUG: property_type = {property_type}")
    print(f"DEBUG: ps[0] keys = {list(ps0.keys())}")
    
    extractor = SDDataExtractor()
    full_address = extractor.generate_full_property_address(ps0, "SD", property_type)
    dim_text = extractor.generate_dimension_text(ps0)
    boundary_text = extractor.generate_boundary_text(ps0)
    
    print(f"RESULT full_address: '{full_address}'")
    print(f"RESULT dimension_text: '{dim_text}'")
    print(f"RESULT boundary_text: '{boundary_text}'")

if __name__ == "__main__":
    test_pipeline()
