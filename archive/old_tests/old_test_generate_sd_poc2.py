import sys, json, os
from docxtpl import DocxTemplate
sys.path.insert(0, '.')
from app import app
from modules.sd.extractor import SDDataExtractor
from modules.sd.narrative import generate_chain_narrative

data = {
    'doc_type': 'SD',
    'rd': '25-05-2026',
    'amount': '20,00,000/-',
    'amount_words': 'बीस लाख',
    'ss': [
        {'n': 'श्री विवेक सक्सैना', 'a': '58', 'c': 'हिन्दु', 'relation_text': 'पुत्र स्व. श्री जे.बी. सक्सैना', 'adr': 'फ्लैट नं. 101, फस्र्ट फ्लोर, भगवती राज अपार्टमेन्ट, 9 देवी निकेतन कम्पाउण्ड, सरदार पटेल रोड़, जयपुर राजस्थान-302001', 'id': 'xxxx xxxx xxxx', 'pan': 'XXXXX1111X'},
        {'n': 'श्रीमती सुनीता सक्सैना', 'a': '58', 'c': 'हिन्दु', 'relation_text': 'पत्नी श्री विवेक सक्सैना', 'adr': 'टी-28, जी.पी.आर.ए. काॅलोनी, टाइप-4, सेक्टर नम्बर 26, आकुर्डी रेलवे स्टेशन के पास, निगड़ी, प्राध्िाकरण, पुणे, महाराष्ट्र-411044', 'id': 'xxxx xxxx xxxx'}
    ],
    'bs': [
        {'n': 'श्रीमती विजय लक्ष्मी', 'a': '25', 'c': 'हिन्दु', 'relation_text': 'पत्नी श्री धर्मेन्द्र सिंह', 'adr': 'एफ- न- 115-ए, घर आंगन अपारटमेंट, मुहाना, जयपुर, राजस्थान- 302029', 'id': 'xxxx xxxx xxxx'}
    ],
    'ps': [{
        'flat_no': 'एस-1',
        'plot_no': 'ए-24',
        'floor': 'सैकण्ड फ्लोर',
        'building_name': 'श्री सांई रेजीडेन्सी - द्वितीय',
        'project_name': 'मधुबन',
        'scheme': 'कृष्णपुरी',
        'village': 'ग्राम बदरवास',
        'tehsil': '',
        'dist': '',
        'state': 'अजमेर रोड़, जयपुर, राजस्थान में स्थित है',
        'const_area': '1087.19',
        'const_unit': 'वर्गफीट',
        'land_area': '183.33',
        'unit': 'वर्गगज',
        'length_ew': '30 फीट',
        'length_ns': '55 फीट',
        'n': 'अन्य',
        's': '40 फुट चौड़ी सड़क',
        'e': 'प्लाट नंबर ए-23',
        'w': 'प्लाट नंबर ए-25',
        'parking_type': 'common',
        'parking_number': '1',
        'full_address': 'प्लॉट नं. ए-24, योजना कृष्णपुरी, ग्राम बदरवास, जिला जयपुर',
        'dimension_text': 'जिसका कुल क्षेत्रफल 183.33 वर्गगज है।',
        'boundary_text': 'जिसकी चारों सीमाएं निम्न प्रकार हैं —\nपूर्व : प्लाट नंबर ए-23\nपश्चिम : प्लाट नंबर ए-25\nउत्तर : अन्य\nदक्षिण : 40 फुट चौड़ी सड़क'
    }],
    'title_chain': [
        {
            'event_type': 'ALLOTMENT',
            'executant_name': 'कार्यालय जयपुर विकास प्राधिकरण, जयपुर',
            'claimant_name': 'श्रीमती राजबाला पत्नी श्री महेश चन्द तोदवाल',
            'doc_name': 'पट्टा विलेख आवंटन/विक्रय-पत्र',
            'date': '17.04.2018',
            'document_number': 'डी-2341',
            'reg_no': '201803021103534',
            'reg_office': 'उप-पंजीयक जयपुर सप्तम्',
            'reg_date': '19.04.2018',
            'reg_book': '01', 'reg_vol': '464', 'reg_page': '98', 'reg_add_book': '01', 'reg_add_vol': '1855', 'reg_add_page': '1026-1039'
        },
        {
            'event_type': 'SALE_DEED',
            'executant_name': 'श्रीमती राजबाला पत्नी श्री महेश चन्द तोदवाल',
            'claimant_name': 'मैसर्स स्नेहा बिल्डिंग मैटेरियल सप्लायर्स जरिये प्रोपरार्इटर श्री सोहन लाल पुत्र श्री ज्वारा राम',
            'doc_name': 'विक्रय पत्र',
            'date': '23.04.2018',
            'reg_no': '201803021103660',
            'reg_office': 'जयपुर-सप्तम',
            'reg_date': '23.04.2018',
            'reg_book': '01', 'reg_vol': '465', 'reg_page': '24', 'reg_add_book': '01', 'reg_add_vol': '1858', 'reg_add_page': '494-507'
        },
        {
            'event_type': 'CONSTRUCTION',
            'executant_name': 'मैसर्स स्नेहा बिल्डिंग मैटेरियल सप्लायर्स जरिये प्रोपरार्इटर श्री सोहन लाल पुत्र श्री ज्वारा राम'
        },
        {
            'event_type': 'SALE_DEED',
            'executant_name': 'मैसर्स स्नेहा बिल्डिंग मैटेरियल सप्लायर्स जरिये प्रोपरार्इटर श्री सोहन लाल पुत्र श्री ज्वारा राम',
            'claimant_name': 'श्री विवेक सक्सैना पुत्र स्वर्गीय श्री जे. बी. सक्सैना एवं श्रीमती सुनीता सक्सैना पत्नी श्री विवेक सक्सैना',
            'doc_name': 'विक्रय पत्र',
            'date': '11.07.2019',
            'reg_no': '201903021106599',
            'reg_office': 'जयपुर-सप्तम',
            'reg_date': '11.07.2019',
            'reg_book': '01', 'reg_vol': '544', 'reg_page': '140', 'reg_add_book': '01', 'reg_add_vol': '2176', 'reg_add_page': '796-813'
        }
    ],
    'ws': [
        {'n': 'श्री विस्वनाथ', 'relation_text': 'पुत्र श्री भगवान सिंह', 'adr': 'फ्लैट न- 007 बी, 2 ब्लॉक, अनुपम अपार्टमेंट, प्रतान नगर, सांगानेर, सेक्टर 11 जयपुर राजस्थान-302033', 'id': '5818 8631 0579'},
        {'n': 'श्री पवन कुमार', 'relation_text': 'पुत्र श्री दाऊदयाल', 'adr': 'फ्लैट न- एल जी-1 लोवर, विनायक अपार्टमेंट, विनायक विहार, गणपतिपुरा, भारत माता सर्किल, जयपुर, राजस्थान-302020', 'id': '3730 5620 3432'}
    ]
}

context = data.copy()
context['w1'] = data['ws'][0]
context['w2'] = data['ws'][1]

for s in context['ss']:
    s['age'] = s.get('a','')
    s['caste'] = s.get('c','')
    s['address'] = s.get('adr','')
    s['aadhaar'] = s.get('id','')
for b in context['bs']:
    b['age'] = b.get('a','')
    b['caste'] = b.get('c','')
    b['address'] = b.get('adr','')
    b['aadhaar'] = b.get('id','')
for w in context['ws']:
    w['address'] = w.get('adr','')
    w['aadhaar'] = w.get('id','')
context['w1']['address'] = context['w1'].get('adr','')
context['w1']['aadhaar'] = context['w1'].get('id','')
context['w2']['address'] = context['w2'].get('adr','')
context['w2']['aadhaar'] = context['w2'].get('id','')

context['sale'] = {'payment_details': f"{data['amount']} रुपये अक्षरे {data['amount_words']} रुपये मात्र"}
context['deed'] = {'execution_date': context['rd']}

e = SDDataExtractor()
p = context['ps'][0]
# Force exact address for SIM test
p['full_address'] = 'आवासीय फ्लैट नम्बर एस-1, सैकण्ड फ्लोर, श्री सांई रेजीडेन्सी - द्वितीय, प्लाट नं. ए-24, कृष्णपुरी, ग्राम बदरवास, अजमेर रोड़, जयपुर, राजस्थान में स्थित है'
p['dimension_text'] = e.generate_dimension_text(p)
p['boundary_text'] = e.generate_boundary_text(p)

chain_paras = generate_chain_narrative(context["title_chain"], property_details=p)
if chain_paras and context["title_chain"] and context["title_chain"][0].get("event_type") == "ALLOTMENT":
    dim_text = p.get("dimension_text", "")
    bnd_text = p.get("boundary_text", "")
    prop_intro = f"सर्वप्रथम {p.get('full_address', '')}, {dim_text}, {bnd_text}, जिसे उक्त विक्रय पत्र में ‘‘उक्त मूल सम्पत्ति’’ कहा गया है, बाबत् "
    chain_paras[0] = chain_paras[0].replace("सर्वप्रथम ", prop_intro, 1)

context["chain_paragraphs"] = chain_paras
context["chain_text"] = "\n\n\tतत्पश्चात् ".join(chain_paras)

# Do not do context['d'] = context.copy() because processor.generate does it properly
# and doing it here creates a circular reference.

from modules.sd.processor import SDTemplateProcessor
processor = SDTemplateProcessor(r'templates\SALE_DEED\SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat_unicode (1)_devlys.docx')
processor.generate(context, r'Test\Final_AI_Test2.docx', highlight_ai=False, highlight_missing=False)
print(r'Generated Test\Final_AI_Test2.docx')
