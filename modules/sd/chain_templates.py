# modules/sd/chain_templates.py

CHAIN_TEMPLATES = {
    "ALLOTMENT_PLOT": "{prefix}{full_address} में स्थित है, {dimension_text}, {boundary_text}, जिसे उक्त विक्रय पत्र में ‘‘उक्त मूल सम्पत्ित’’ कहा गया है, बाबत् {claimant} ने {executant} में नियमन राष्िा व लीज राश्िा नियमानुसार जमा करवा दी, जिसके पश्चात् {executant} ने {document_name_str}{document_number_phrase} दिनाँक {date} ईस्वी को {claimant} के हित में निष्पादित कर जारी कर दिया, {reg_details}इस प्रकार {claimant} उक्त मूल सम्पत्ित के एकमात्र मालिक, स्वामी व अध्िाकारी हुर्इ ।",

    "ALLOTMENT_PLOT_NO_DEPOSIT": "{prefix}{full_address} में स्थित है, {dimension_text}, {boundary_text}, जिसे उक्त विक्रय पत्र में ‘‘उक्त मूल सम्पत्ित’’ कहा गया है, जिसके पश्चात् {executant} ने {document_name_str}{document_number_phrase} दिनाँक {date} ईस्वी को {claimant} के हित में निष्पादित कर जारी कर दिया, {reg_details}इस प्रकार {claimant} उक्त मूल सम्पत्ित के एकमात्र मालिक, स्वामी व अध्िाकारी हुर्इ ।",

    "ALLOTMENT_FLAT": "{prefix}{full_address} में स्थित है, {dimension_text}, {boundary_text}, जिसे उक्त विक्रय पत्र में ‘‘उक्त मूल सम्पत्ित’’ कहा गया है, बाबत् {claimant} ने {executant} में नियमन राष्िा व लीज राश्िा नियमानुसार जमा करवा दी, जिसके पश्चात् {executant} ने {document_name_str}{document_number_phrase} दिनाँक {date} ईस्वी को {claimant} के हित में निष्पादित कर जारी कर दिया, {reg_details}इस प्रकार {claimant} उक्त फ्लैट के एकमात्र मालिक, स्वामी व अध्िाकारी हुर्इ ।",

    "ALLOTMENT_FLAT_NO_DEPOSIT": "{prefix}{full_address} में स्थित है, {dimension_text}, {boundary_text}, जिसे उक्त विक्रय पत्र में ‘‘उक्त मूल सम्पत्ित’’ कहा गया है, जिसके पश्चात् {executant} ने {document_name_str}{document_number_phrase} दिनाँक {date} ईस्वी को {claimant} के हित में निष्पादित कर जारी कर दिया, {reg_details}इस प्रकार {claimant} उक्त फ्लैट के एकमात्र मालिक, स्वामी व अध्िाकारी हुर्इ ।",

    "CONSTRUCTION_FLAT": "{prefix}{executant} ने अपने अध्िाकारो का प्रयोग करते हुये उक्त मूल सम्पत्ित पर अपार्टमेन्ट/यूनिट्स/फ्लेट्स का निर्माण करवा लिया तथा उक्त यूनिट्स/फ्लेट्स को अलग-अलग नम्बरों से चिन्िहत कर दिया तथा उसका नाम ‘‘{project_name}’’ रख दिया।",

    "CONSTRUCTION_FLAT_NO_NAME": "{prefix}{executant} ने अपने अध्िाकारो का प्रयोग करते हुये उक्त मूल सम्पत्ित पर अपार्टमेन्ट/यूनिट्स/फ्लेट्स का निर्माण करवा लिया तथा उक्त यूनिट्स/फ्लेट्स को अलग-अलग नम्बरों से चिन्िहत कर दिया।",

    "SALE_DEED_PLOT": "{prefix}{executant} ने उक्त मूल सम्पत्ित को जरिये {document_name_str} दिनांकित {date} {amount_str}द्वारा {claimant} को विक्रय कर दिया, {reg_details}इस प्रकार {claimant} उक्त मूल सम्पत्ित के एकमात्र मालिक, स्वामी व अध्िाकारी हुए।",

    "SALE_DEED_FLAT": "{prefix}{executant} ने उक्त मूल सम्पत्ित, जिसका कुल क्षेत्रफल {total_area} {area_unit} है, पर निमर्ित उपरोक्त अपार्टमेन्ट/यूनिट्स/फ्लेट्स में से एक यूनिट्/फ्लेट, को जरिये {document_name_str} दिनांकित {date} {amount_str}द्वारा {claimant} को विक्रय कर दिया, {reg_details}इस प्रकार {claimant} उक्त यूनिट/फ्लेट के मालिक, स्वामी व अध्िाकारी हुए।",

    "TRANSFER_PLOT": "{prefix}{executant} ने उक्त मूल सम्पत्ित को जरिये {document_name_str} दिनांकित {date} {amount_str}द्वारा {claimant} को हस्तान्तरित कर दिया, {reg_details}इस प्रकार {claimant} उक्त मूल सम्पत्ित के एकमात्र मालिक, स्वामी व अध्िाकारी हुए।",

    "TRANSFER_FLAT": "{prefix}{executant} ने उक्त फ्लैट को जरिये {document_name_str} दिनांकित {date} {amount_str}द्वारा {claimant} को हस्तान्तरित कर दिया, {reg_details}इस प्रकार {claimant} उक्त फ्लैट के एकमात्र मालिक, स्वामी व अध्िाकारी हुए।"
}

REGISTRATION_TEMPLATES = {
    "ALLOTMENT": "उक्त {document_name} का पंजीयन {office_phrase}{date_phrase}पुस्तक संख्या {reg_book} जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book} जिल्द संख्या {reg_add_vol} {reg_add_page_str} पर चस्पा किया गया।",
    "GENERAL": "जिसका पंजीयन {office_phrase}{date_phrase}पुस्तक संख्या {reg_book} जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book} जिल्द संख्या {reg_add_vol} {reg_add_page_str} पर चस्पा किया गया।"
}
