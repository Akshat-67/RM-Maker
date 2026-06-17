import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import _generate_chain_narrative
from processor import TemplateProcessor
from extractor import DataExtractor
import json

def test_chain():
    # 1. Provide a dummy title_chain event
    events = [
        {
            "event_type": "ALLOTMENT",
            "document_name": "पट्टा विलेख",
            "date": "01.01.2010",
            "executant_name": "नगर निगम",
            "claimant_name": "श्री राम",
            "is_registered": True,
            "reg_office": "जयपुर",
            "reg_date": "05.01.2010",
            "reg_book": "1",
            "reg_vol": "20",
            "reg_page": "5",
            "reg_no": "100",
            "consideration_amount": "50000"
        },
        {
            "event_type": "SALE_DEED",
            "document_name": "विक्रय पत्र",
            "date": "15.06.2015",
            "executant_name": "श्री राम",
            "claimant_name": "श्री श्याम",
            "is_registered": True,
            "reg_office": "जयपुर द्वितीय",
            "reg_date": "16.06.2015",
            "reg_book": "1",
            "reg_vol": "50",
            "reg_page": "10",
            "reg_no": "500",
            "consideration_amount": "1500000"
        }
    ]

    print("--- 1. Chain Events ---")
    print(json.dumps(events, indent=2, ensure_ascii=False))

    # 2. Generate narrative
    chain_text = _generate_chain_narrative(events)
    print("\n--- 2. chain_text Narrative ---")
    print(chain_text)

    # 3. Simulate TemplateProcessor conversion
    tp = TemplateProcessor("dummy") # Won't load if dummy doesn't exist, wait, TemplateProcessor init checks file existence
    
if __name__ == "__main__":
    test_chain()
