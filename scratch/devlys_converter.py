import sys
import os

# Add root directory to path to import processor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from processor import Unicode_to_KrutiDev

test_strings = {
    "vivek": "विवेक सक्सेना",
    "jb": "जे-बी- सक्सेना",
    "sunita": "सुनीता सक्सेना",
    "vijay": "विजय लक्ष्मी",
    "dharmendra": "धर्मेन्द्र सिंह",
    "sultan": "सुल्तान",
    "allahnoor": "अल्लाहनूर",
    "pawan": "पवन कुमार",
    "deendayal": "दीनदयाल",
    "flat": "फ्लैट",
    "sqft": "वर्गफीट",
    "property_adr": "आवासीय फ्लैट नम्बर एस-1, सैकण्ड फ्लोर, श्री सांई रेजीडेन्सी - द्वितीय, प्लाट नं- ए-24, कृष्णपुरी, ग्राम बदरवास, अजमेर रोड, जयपुर, राजस्थान"
}

sys.stdout.reconfigure(encoding='utf-8')
print("--- UNICODE TO DEVLYS ASCII TRANSLATIONS ---")
for k, v in test_strings.items():
    converted = Unicode_to_KrutiDev(v)
    print(f"{k}: {v} -> {converted}")
