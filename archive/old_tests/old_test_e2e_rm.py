import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from modules.rm.processor import RMTemplateProcessor as TemplateProcessor

template_path = "templates/ICICI/RM_ICICI_1B_1L(One Property).docx"
output_path = "cases/test_rm_output_agent.docx"
os.makedirs("cases", exist_ok=True)

context = {
    "d": {
        "bs": [
            {
                "s": "Mr.",
                "n": "Mr. Deendayal",
                "a": "45",
                "r": "S/o",
                "rn": "Mohanlal",
                "adr": "Flat No. 101, Pink City Apartments, Jaipur, Rajasthan",
                "id": "1234 5678 9012",
                "pan": "ABCDE1234F"
            }
        ],
        "ls": [
            {
                "n": "L-ICICI-999888",
                "a": "15,00,000/-",
                "w": "Fifteen Lakhs Only",
                "t": "Home Loan"
            }
        ],
        "ps": [
            {
                "adr": "Residential House on Plot No. 42, Vinayak Enclave, Sanganer, Jaipur, Rajasthan",
                "n": "Plot No. 43",
                "s": "Plot No. 41",
                "e": "Plot No. 22",
                "w": "Road 30 Feet Wide",
                "lease_deed_no": "JDA-LEASE-1122"
            }
        ],
        "ws": [
            {
                "n": "Ram Avtar",
                "r": "S/o",
                "rn": "Gopal Lal",
                "adr": "Mansarovar, Jaipur"
            },
            {
                "n": "Sita Ram",
                "r": "S/o",
                "rn": "Hari Prasad",
                "adr": "Malviya Nagar, Jaipur"
            }
        ],
        "bsign": {
            "n": "Mr. Bank Officer",
            "r": "S/o",
            "rn": "Officer Father",
            "s": "Mr."
        },
        "ds": [
            {"t": "Registry Sale Deed dated 15-05-2024"},
            {"t": "JDA Allotment Letter dated 10-04-2024"}
        ],
        "execution_date": "23-06-2026",
        "second_schedule": "Registry Sale Deed dated 15-05-2024\nJDA Allotment Letter dated 10-04-2024"
    }
}

# Duplicate d context at root level for template rendering compatibility
context.update(context["d"])

print("--- EXECUTING E2E REGISTERED MORTGAGE (RM) DOCUMENT GENERATION ---")
try:
    processor = TemplateProcessor(template_path)
    processor.generate(context, output_path, highlight_ai=True, highlight_missing=True)
    
    print("\n[SUCCESS]: Registered Mortgage generated successfully at:", output_path)
    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        print("[OK] Output file exists and size is valid:", os.path.getsize(output_path), "bytes")
    else:
        raise ValueError("Generated file is missing or invalid size!")
        
except Exception as e:
    print("\n[FAILED]: Document Generation failed due to exception:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
