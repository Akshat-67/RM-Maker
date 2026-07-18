import pytest
from modules.sd.narrative import generate_chain_narrative

def test_pawan_agarwal_chain():
    # Society -> 3 Sale Deeds
    chain = [
        {
            "event_type": "ALLOTMENT",
            "template_key": "ALLOTMENT_SOCIETY",
            "document_name": "आवंटन पत्र",
            "date": "08-08-1996",
            "executant_name": "वाटिका गृह निर्माण सहकारी समिति लिमिटेड, जयपुर",
            "claimant_name": "श्री सुरेश जांगिड़ पुत्र श्री रामेश्वर जांगिड़",
            "receipt_no": "4347",
            "receipt_date": "08-08-1996",
            "source_text": "पंजीयन क्रमांक 2632/एल द्वारा श्री सुरेश जांगिड़ पुत्र श्री रामेश्वर जांगिड़ को दिनांक 08-08-1996 को जरिये आवंटन पत्र आवंटित की गयी थी तथा उक्त रसीद संख्या 4347",
            "is_registered": "false"
        },
        {
            "event_type": "SALE_DEED",
            "template_key": "SALE_DEED_PLOT",
            "document_name": "विक्रय पत्र",
            "date": "11-10-2019",
            "executant_name": "श्री सुरेश जांगिड़ पुत्र श्री रामेश्वर जांगिड़",
            "claimant_name": "श्रीमती सुरज्ञान पत्नी श्री हरिनारायण बैरवा",
            "reg_office": "कार्यालय, उप पंजीयक सांगानेर-द्वितीय, जयपुर",
            "reg_date": "11-10-2019",
            "reg_book": "1",
            "reg_vol": "423",
            "reg_page": "16",
            "reg_no": "201903025103775",
            "reg_add_book": "1",
            "reg_add_vol": "1688",
            "reg_add_page": "364-375",
            "is_registered": "true",
            "source_text": "पंजीकृत विक्रय पत्र दिनांक 11-10-2019"
        }
    ]
    
    paras = generate_chain_narrative(chain)
    assert len(paras) == 2
    
    # Check "काबिज" is present in suffix
    assert "मालिक स्वामी काबिज व अधिकारी हुआ" in paras[0]
    assert "मालिक स्वामी काबिज व अधिकारी हुई" in paras[1]
    
    # Check dynamic gender connectors (का/की/के)
    assert "उक्त सम्पत्ति का एकमात्र" in paras[0]  # Male
    assert "उक्त सम्पत्ति की एकमात्र" in paras[1]  # Female
    
    # Check registration office word order and cleanups
    assert "कार्यालय, उप पंजीयक सांगानेर-द्वितीय, जयपुर" in paras[1]
    assert "कार्यालय कार्यालय" not in paras[0]
    assert "कार्यालय कार्यालय" not in paras[1]

def test_priyanka_jadon_partition_sale():
    # Partition and Sale deed (Case 3 Priyanka Jadon style)
    chain = [
        {
            "event_type": "SALE_DEED",
            "template_key": "PARTITION_SALE",
            "document_name": "विक्रय पत्र",
            "date": "10-02-2021",
            "executant_name": "श्रीमती आशा देवी",
            "claimant_name": "श्रीमती प्रियंका जादौन",
            "is_registered": "true",
            "reg_office": "कार्यालय, उप पंजीयक जयपुर",
            "reg_date": "10-02-2021",
            "reg_book": "1",
            "reg_vol": "500",
            "reg_page": "50",
            "reg_no": "202103021102554",
            "reg_add_book": "1",
            "reg_add_vol": "2000",
            "reg_add_page": "100-110",
            "source_text": "श्रीमती आशा देवी ने प्लाट न- 19 व प्लाट न- 20, क्षेत्रफल 400 वर्गगज को विभाजित कर लिया तथा विभाजित क्षेत्रफल 200 वर्गगज को जरिये पंजीकृत विक्रय पत्र दिनांक 10-02-2021 के द्वारा श्रीमती प्रियंका जादौन को विक्रय कर दिया।"
        }
    ]
    
    paras = generate_chain_narrative(chain)
    assert len(paras) == 1
    
    # Verify regex extracted details
    assert "प्लाट न- 19 व प्लाट न- 20" in paras[0]
    assert "क्षेत्रफल 400 वर्गगज" in paras[0]
    assert "विभाजित क्षेत्रफल 200 वर्गगज" in paras[0]
    assert "की एकमात्र मालिक स्वामी काबिज व अधिकारी हुई" in paras[0]

def test_dinesh_khandelwal_transfer_construction():
    # Transfer letter and construction flat (Case 4 Dinesh style)
    chain = [
        {
            "event_type": "TRANSFER",
            "template_key": "TRANSFER_CERTIFICATE",
            "document_name": "हस्तान्तरण पत्र",
            "document_number": "डी-11556",
            "date": "05-08-2008",
            "executant_name": "कार्यालय जयपुर विकास प्राधिकरण",
            "claimant_name": "श्री दिनेश कुमार खण्डेलवाल",
            "is_registered": "true",
            "source_text": "हस्तान्तरण पत्र क्रमांक डी-11556 दिनांक 05-08-2008 को श्री दिनेश कुमार खण्डेलवाल के नाम से जारी किया गया।"
        },
        {
            "event_type": "CONSTRUCTION",
            "template_key": "CONSTRUCTION_FLAT",
            "executant_name": "मैसर्स हरी ओम एन्टर प्राईजेज",
            "project_name": "गोकुल एन्क्लेव",
            "is_registered": "false",
            "source_text": "मैसर्स हरी ओम एन्टर प्राईजेज ने प्लाट न- 159, क्षेत्रफल 252 वर्गमीटर भूमि पर आवासीय छः यूनिटो व बेसमेन्ट का निर्माण करवा लिया।"
        }
    ]
    
    property_details = {"flat_no": "S-1", "land_area": "252", "unit": "वर्गमीटर"}
    context = {
        "bs": [{"n": "विवेक सक्सैना"}],
        "ss": [{"n": "हरी ओम एन्टर प्राईजेज"}]
    }
    paras = generate_chain_narrative(chain, property_details=property_details, context=context)
    assert len(paras) == 2
    
    # Verify TRANSFER_CERTIFICATE rendering
    assert "हस्तान्तरण पत्र क्रमांक डी-11556" in paras[0]
    assert "का एकमात्र मालिक स्वामी काबिज व अधिकारी हुआ" in paras[0]
    
    # Verify CONSTRUCTION_FLAT rendering and regex extraction
    assert "प्लाट न- 159" in paras[1]
    assert "252 वर्गमीटर" in paras[1]
    assert "छः यूनिटो व बेसमेन्ट" in paras[1]

def test_empty_registration_fields_guarding():
    # Registration is True but reg_no is missing
    chain = [
        {
            "event_type": "SALE_DEED",
            "template_key": "SALE_DEED_PLOT",
            "document_name": "विक्रय पत्र",
            "date": "12-12-2020",
            "executant_name": "श्री राम लाल",
            "claimant_name": "श्री श्याम लाल",
            "is_registered": "true",
            "reg_office": "",
            "reg_no": "",  # missing reg_no
            "source_text": "विक्रय पत्र दिनांक 12-12-2020"
        }
    ]
    
    paras = generate_chain_narrative(chain)
    # Registration clause should be stripped out completely
    assert "पुस्तक संख्या" not in paras[0]
    assert "जिल्द संख्या" not in paras[0]
    assert "क्रम संख्या" not in paras[0]
    assert "पंजीबद्ध" not in paras[0]
