import sys, json, os
from docxtpl import DocxTemplate
sys.path.insert(0, '.')
from app import app
from modules.sd.extractor import SDDataExtractor
from modules.sd.narrative import generate_chain_narrative

data = {
    'doc_type': 'SD',
    'rd': '18.05.2026',
    'amount': '2000000',
    'amount_words': 'बीस लाख',
    'ss': [
        {'n': 'श्री विवेक सक्सेना', 'a': '58', 'c': 'हिंदू', 'relation_text': 'पुत्र स्वर्गीय श्री जे.बी. सक्सेना', 'adr': 'फ्लैट नं. 101, फर्स्ट फ्लोर, भगवती राज अपार्टमेंट, 9 देवी निकेतन कम्पाउंड, सरदार पटेल रोड, जयपुर', 'id': 'xxxx xxxx xxxx', 'pan': 'XXXXX1111X'},
        {'n': 'श्रीमती सुनीता सक्सेना', 'a': '58', 'c': 'हिंदू', 'relation_text': 'पत्नी श्री विवेक सक्सेना', 'adr': 'टी-28, जी.पी.आर.ए. कॉलोनी, टाइप-4, सेक्टर नम्बर 26, आकुर्डी रेलवे स्टेशन के पास, निगड़ी, प्राधिकरण, पुणे', 'id': 'xxxx xxxx xxxx'}
    ],
    'bs': [
        {'n': 'श्रीमती विजय लक्ष्मी', 'a': '25', 'c': 'हिंदू', 'relation_text': 'पत्नी श्री धर्मेन्द्र सिंह', 'adr': 'एफ-115-ए, घर आँगन अपार्टमेंट, मुहाना, जयपुर', 'id': 'xxxx xxxx xxxx'}
    ],
    'ps': [{
        'plot_no': 'S-1',
        'floor': 'सेकंड फ्लोर',
        'building_name': 'श्री साईं रेजीडेंसी - द्वितीय',
        'scheme': 'कृष्णापुरी',
        'village': 'बदरवास',
        'tehsil': '',
        'dist': 'जयपुर',
        'state': 'राजस्थान',
        'const_area': '1087.19',
        'const_unit': 'वर्गफ़ीट',
        'land_area': '183.33',
        'unit': 'वर्ग गज',
        'length_ew': '30 फ़ीट',
        'length_ns': '55 फ़ीट',
        'n': 'अन्य की भूमि',
        's': 'रोड 40 फ़ीट',
        'e': 'प्लाट नम्बर A-23',
        'w': 'प्लाट नम्बर A-25',
        'parking_type': 'common',
        'parking_number': '1'
    }],
    'title_chain': [
        {
            'event_type': 'ALLOTMENT',
            'executant_name': 'जेडीए',
            'claimant_name': 'श्रीमती राजबाला',
            'doc_name': 'पट्टा विलेख',
            'date': '17.04.2018',
            'reg_no': 'D-2341',
            'reg_office': 'उप-पंजीयक जयपुर-VII',
            'reg_date': '19.04.2018',
            'reg_book': '1', 'reg_vol': '464', 'reg_page': '98', 'reg_add_book': '1', 'reg_add_vol': '1855', 'reg_add_page': '1026-1039'
        },
        {
            'event_type': 'SALE_DEED',
            'executant_name': 'श्रीमती राजबाला',
            'claimant_name': 'मेसर्स स्नेहा बिल्डिंग',
            'doc_name': 'विक्रय पत्र',
            'date': '23.04.2018',
            'reg_office': 'उप-पंजीयक जयपुर-VII',
            'reg_date': '23.04.2018',
            'reg_book': '1', 'reg_vol': '465', 'reg_page': '24', 'reg_add_book': '1', 'reg_add_vol': '1858', 'reg_add_page': '494-507'
        },
        {
            'event_type': 'CONSTRUCTION',
            'executant_name': 'मेसर्स स्नेहा बिल्डिंग'
        },
        {
            'event_type': 'SALE_DEED',
            'executant_name': 'मेसर्स स्नेहा बिल्डिंग',
            'claimant_name': 'श्री विवेक सक्सेना व श्रीमती सुनीता सक्सेना',
            'doc_name': 'विक्रय पत्र',
            'date': '11.07.2019',
            'reg_office': 'उप-पंजीयक जयपुर-VII',
            'reg_date': '11.07.2019',
            'reg_book': '1', 'reg_vol': '544', 'reg_page': '140', 'reg_add_book': '1', 'reg_add_vol': '2176', 'reg_add_page': '796-813'
        }
    ],
    'ws': [
        {'n': 'श्री विश्वनाथ', 'relation_text': 'पुत्र श्री भगवान सिंह', 'adr': 'फ्लैट न- 007 बी, 2 ब्लॉक, अनुपम अपार्टमेंट, प्रताप नगर, सांगानेर', 'id': '5818 8631 0579'},
        {'n': 'श्री पवन कुमार', 'relation_text': 'पुत्र श्री दाऊदयाल', 'adr': 'फ्लैट न- एल जी-1 लोवर, विनायक अपार्टमेंट, विनायक विहार, जयपुर', 'id': '3730 5620 3432'}
    ]
}

context = data.copy()
context['w1'] = data['ws'][0]
context['w2'] = data['ws'][1]
context['chain_text'] = generate_chain_narrative(context['title_chain'])

for k in ['ss', 'bs', 'ws']:
    for p in context[k]:
        p['address'] = p.get('adr', '')
        p['aadhaar'] = p.get('id', '')
context['w1']['address'] = context['w1'].get('adr','')
context['w1']['aadhaar'] = context['w1'].get('id','')
context['w2']['address'] = context['w2'].get('adr','')
context['w2']['aadhaar'] = context['w2'].get('id','')

context['sale'] = {'payment_details': f"{data['amount_words']} रुपये ({data['amount']}/-)"}
context['deed'] = {'execution_date': context['rd']}

e = SDDataExtractor()
p = context['ps'][0]
p['full_address'] = e.generate_full_property_address(p, property_type='Flat')
p['dimension_text'] = e.generate_dimension_text(p)
p['boundary_text'] = e.generate_boundary_text(p)

context['d'] = context.copy()

tpl = DocxTemplate(r'templates\SALE_DEED\SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat_unicode (1)_devlys.docx')
tpl.render(context)
tpl.save(r'Test\Final_AI_Test.docx')
print('Generated Test\Final_AI_Test.docx')
