import os
import sys
import json
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass
from utils.devlys_converter import unicode_to_devlys
from modules.sd.processor import SDTemplateProcessor as TemplateProcessor

def test_full_conversion_validation():
    print("--- Phase 3B-A: Conversion Validation ---")
    
    # 1. Real SD sample values
    test_data = {
        "seller_name_1": "मनोज कुमार",
        "seller_name_2": "बालकिशन यादव",
        "buyer_name": "मोनू कुमारी",
        "address": "जयपुर, राजस्थान",
        "consideration": "छब्बीस लाख पचास हजार",
        "property_desc": "प्लॉट नंबर 15, बालाजी नगर, जयपुर",
        "boundaries": "उत्तर: प्लॉट नंबर 14, दक्षिण: अन्य भूमि",
        "title_chain": "जमीला खातून से प्राप्त पट्टा संख्या 2768"
    }

    # 2. Convert and Inspect Accuracy
    results = {}
    print("\n--- Individual Conversions ---")
    for key, value in test_data.items():
        converted = unicode_to_devlys(value)
        results[key] = converted
        print(f"{key}:")
        print(f"  Unicode: {value}")
        print(f"  DevLys : {converted}")

    # 3. Build Rendering POC
    # We'll use the same template as Phase 3A but with converted data
    template_path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat.docx"
    output_path = "sd_conversion_validation_output.docx"
    
    if not os.path.exists(template_path):
        print(f"\nERROR: Template not found at {template_path}")
        return

    # Map results to template placeholders
    context = {
        "sellers": [
            {"n": results["seller_name_1"], "adr": results["address"]},
            {"n": results["seller_name_2"], "adr": results["address"]}
        ],
        "buyers": [{"n": results["buyer_name"], "adr": results["address"]}],
        "ps": [{"adr": results["property_desc"], "n": results["boundaries"]}],
        "payments": results["consideration"],
        "chain": [{"owner": results["title_chain"]}],
        "rd": "01.01.2026"
    }

    print(f"\n--- Generating Validation Document: {output_path} ---")
    try:
        processor = TemplateProcessor(template_path)
        processor.generate(context, output_path)
        print("SUCCESS: Validation document generated.")
    except Exception as e:
        print(f"ERROR: Generation failed - {str(e)}")

if __name__ == "__main__":
    test_full_conversion_validation()
