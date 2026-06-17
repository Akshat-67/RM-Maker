import json
from modules.sd.extractor import SDDataExtractor
from utils.helpers import Unicode_to_KrutiDev

def test_conversion():
    with open('cases/case_1781374115/session.json', 'r', encoding='utf-8') as f:
        session = json.load(f)
    
    ps0 = session['data']['ps'][0]
    extractor = SDDataExtractor()
    full_address = extractor.generate_full_property_address(ps0, "SD", "Plot")
    
    print(f"UNICODE: {full_address}")
    legacy = Unicode_to_KrutiDev(full_address)
    print(f"LEGACY: '{legacy}'")

if __name__ == "__main__":
    test_conversion()
