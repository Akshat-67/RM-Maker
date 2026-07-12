import sys
import os

# Add root directory to path to import processor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.sd.processor import SDTemplateProcessor as TemplateProcessor

# Define the template path and the output path
template_path = "templates/SALE_DEED/Flat - 2S_1B_1P.docx"
output_path = "cases/test_sd_output_agent.docx"
os.makedirs("cases", exist_ok=True)

# 1. Construct Mock Bilingual & Grid Context
context = {
    "rd": "25-05-2026", # Execution date
    
    # 2 Sellers
    "ss": [
        {
            "n": "विवेक सक्सेना", # Mr. Vivek Saxena
            "n_en": "Vivek Saxena",
            "r": "iqr Jh", # S/o
            "rn": "जे-बी- सक्सेना", # Late Mr. J.B. Saxena
            "rn_en": "J.B. Saxena",
            "a": "58",
            "adr": "फ्लैट नं- 101, फर्स्ट फ्लोर, भगवती राज अपार्टमेंट, 9 देवी निकेतन कम्पाउंड, सरदार पटेल रोड, जयपुर राजस्थान-302001",
            "adr_en": "Flat No. 101, First Floor, Bhagwati Raj Apartment, 9 Devi Niketan Compound, Sardar Patel Road, Jaipur",
            "id": "5564 0963 9476",
            "pan": "AKHPS7097L"
        },
        {
            "n": "सुनीता सक्सेना", # Mrs. Sunita Saxena
            "n_en": "Sunita Saxena",
            "r": "iRuh Jh", # Wife of
            "rn": "विवेक सक्सेना",
            "rn_en": "Vivek Saxena",
            "a": "58",
            "adr": "टी-28, जी-पी-आर-ए- कॉलोनी, टाईप-4, सेक्टर नम्बर 26, आकुर्डी रेलवे स्टेशन के पास, निगड़ी, प्राधिकरण, पुणे, महाराष्ट्र-411044",
            "adr_en": "T-28, G.P.R.A. Colony, Type-4, Sector Number 26, Pune, Maharashtra",
            "id": "6267 4409 8295",
            "pan": "BSOPS8468K"
        }
    ],
    
    # 1 Buyer
    "bs": [
        {
            "n": "विजय लक्ष्मी", # Mrs. Vijay Laxmi
            "n_en": "Vijay Laxmi",
            "r": "iRuh Jh", # Wife of
            "rn": "धर्मेन्द्र सिंह",
            "rn_en": "Dharmendra Singh",
            "a": "25",
            "adr": "एफ- न- 115-ए, घर आंगन अपार्टमेंट, मुहाना, जयपुर, राजस्थान- 302029",
            "adr_en": "F-No. 115-A, Ghar Aangan Apartment, Muhana, Jaipur, Rajasthan",
            "id": "6693 2771 2261",
            "pan": "BQOPL5182P"
        }
    ],
    
    # Property Schedule & Boundaries
    "ps": [
        {
            "adr": "आवासीय फ्लैट नम्बर एस-1, सैकण्ड फ्लोर, श्री सांई रेजीडेन्सी - द्वितीय, प्लाट नं- ए-24, कृष्णपुरी, ग्राम बदरवास, अजमेर रोड, जयपुर, राजस्थान",
            "adr_en": "Residential Flat S-1, Second Floor, Plot A-24, Krishnapuri, Jaipur",
            "area": "1087.19",
            "area_unit": "वर्गफीट",
            "e": "प्लाट न. 23", # East
            "w": "रास्ता 30 फीट चौड़ा", # West
            "n": "प्लाट न. 25", # North
            "s": "प्लाट न. ए-24 का शेष भाग" # South
        }
    ],
    
    # Witnesses
    "ws": [
        {
            "n": "सुल्तान",
            "n_en": "Sultan",
            "r": "iqr Jh",
            "rn": "अल्लाहनूर",
            "rn_en": "Allahnoor",
            "adr": "410 कमला नेहरू नगर, शांति नगर, हसनपुरा, जयपुर, स्टेशन रोड, जयपुर, राजस्थान-302006",
            "adr_en": "410 Kamla Nehru Nagar, Station Road, Jaipur",
            "id": "4493 8314 4916"
        },
        {
            "n": "पवन कुमार",
            "n_en": "Pawan Kumar",
            "r": "iqr Jh",
            "rn": "दीनदयाल",
            "rn_en": "Deendayal",
            "adr": "फ्लैट न. एल जी-1 लोवर, विनायक आपार्टमेंट, विनायक विहार, गणपतिपुरा, भारत माता सर्किल, जयपुर, राजस्थान-302020",
            "adr_en": "Flat LG-1, Lower, Vinayak Apartment, Vinayak Vihar, Jaipur",
            "id": "9999 8888 7777"
        }
    ],
    
    # Title Chain Historical Grid
    "chain": [
        {
            "d": "11-07-2019", # prior registry date
            "s": "राम किशोर", # prior seller
            "b": "विवेक सक्सेना", # prior buyer
            "b_no": "01",
            "v_no": "544",
            "p_no": "140",
            "r_no": "201903021106599"
        }
    ],
    
    # Payments Grid Schedule
    "payments": [
        {
            "a": "20,000/-",
            "d": "18.05.2016",
            "n": "CASH",
            "b": "SELF"
        },
        {
            "a": "4,80,000/-",
            "d": "16.05.2026",
            "n": "IMPS-613611327488",
            "b": "ICICI Bank"
        },
        {
            "a": "15,00,000/-",
            "d": "20.05.2026",
            "n": "Cheque No.849938",
            "b": "ICICI Bank"
        }
    ],
    "amount": "1980000",
    "amount_words": "Nineteen Lakhs Eighty Thousand"
}

# Provide 'd' alias for the entire context data structure without circular references
data = context
context = data.copy()
context["w1"] = data["ws"][0]
context["w2"] = data["ws"][1]
from modules.sd.narrative import generate_chain_narrative
context["chain_text"] = generate_chain_narrative(context.get("title_chain", []))
context['d'] = context.copy()

print("--- EXECUTING E2E SALE DEED DOCUMENT GENERATION ---")
try:
    processor = TemplateProcessor(template_path)
    processor.generate(context, output_path, highlight_ai=True, highlight_missing=True)
    
    print("\n[SUCCESS]: Sale Deed generated successfully at:", output_path)
    print("Format and Font mappings applied completely!")
    
    # Verify file sizes and paths
    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        print("[OK] Output file exists and size is valid:", os.path.getsize(output_path), "bytes")
    else:
        raise ValueError("Generated file is missing or invalid size!")
        
except Exception as e:
    print("\n[FAILED]: Document Generation failed due to exception:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
