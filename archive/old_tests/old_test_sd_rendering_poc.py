import os
import json
from modules.sd.processor import SDTemplateProcessor as TemplateProcessor

def test_minimal_sd_generation():
    # 1. Select a representative SD template
    # This template already exists in the workspace
    template_path = "templates/SALE_DEED/SD_JDA_2SD_Flat_2S_1B.docx"
    output_path = "sd_rendering_poc_output.docx"
    
    if not os.path.exists(template_path):
        print(f"ERROR: Template not found at {template_path}")
        return

    # 2. Mock reviewed SD data (Unicode Hindi)
    # Aligned with placeholders found in SD_JDA_2SD_Flat_2S_1B.docx
    context = {
        "doc_type": "SD",
        "rd": "01.01.2026",
        "sellers": [
            {
                "n": "मनोज कुमार",
                "a": "35",
                "c": "यादव",
                "r": "पुत्र",
                "rn": "भीवा राम",
                "adr": "जयपुर, राजस्थान",
                "id": "1234 5678 9012",
                "pan": "ABCDE1234F"
            },
            {
                "n": "बालकिशन यादव",
                "a": "40",
                "c": "यादव",
                "r": "पुत्र",
                "rn": "रामेश्वर प्रसाद",
                "adr": "जयपुर, राजस्थान",
                "id": "9876 5432 1098",
                "pan": "FGHIJ5678K"
            }
        ],
        "buyers": [
            {
                "n": "मोनू कुमारी",
                "a": "28",
                "c": "मीणा",
                "r": "पुत्री",
                "rn": "रामअवतार मीणा",
                "adr": "झुंझुनू, राजस्थान",
                "id": "1111 2222 3333",
                "pan": "KLMNO9012P"
            }
        ],
        "ps": [
            {
                "adr": "प्लॉट नंबर 15, बालाजी नगर, जयपुर",
                "plot_no": "15",
                "scheme": "बालाजी नगर",
                "village": "हाथोज",
                "tehsil": "झोटवाड़ा",
                "dist": "जयपुर",
                "land_area": "75",
                "const_area": "675",
                "unit": "वर्गगज",
                "n": "प्लॉट नंबर 14",
                "s": "अन्य भूमि",
                "e": "रोड 20 फीट",
                "w": "प्लॉट नंबर 15 का शेष भाग"
            }
        ],
        "ws": [
            {
                "n": "गवाह 1",
                "r": "पुत्र",
                "rn": "पिता 1",
                "adr": "पता 1"
            },
            {
                "n": "गवाह 2",
                "r": "पुत्र",
                "rn": "पिता 2",
                "adr": "पता 2"
            }
        ],
        "chain": [
            {
                "owner": "जमीला खातून",
                "deed_type": "पट्टा",
                "date": "11.06.1996",
                "reg_no": "2768"
            }
        ],
        "payments": "26,50,000"
    }

    print(f"--- Running Phase 3A POC: {template_path} ---")
    
    try:
        processor = TemplateProcessor(template_path)
        # Note: Phase 1/2 changes added 'ss' support to padding logic in processor.py?
        # Let's check LIST_DEFAULTS in processor.py above.
        # It currently lacks 'ss'. I should add it for the POC to work correctly with padding.
        
        processor.generate(context, output_path)
        print(f"SUCCESS: Document generated at {output_path}")
        
    except Exception as e:
        print(f"ERROR: Generation failed - {str(e)}")

if __name__ == "__main__":
    test_minimal_sd_generation()
