# modules/sd/chain_templates.py
import os
import json

CHAIN_TEMPLATES = {
    # --- Mother Title (First Event) Templates ---
    # JDA Plot Allotment
    "ALLOTMENT_PLOT": "यह कि सर्वप्रथम उक्त सम्पत्ति बाबत् {claimant} ने कार्यालय {authority_name} में नियमन राशि व लीज राशि नियमानुसार जमा करवा दी जिसके पश्चात् उक्त सम्पत्ति बाबत् कार्यालय {authority_name} ने पृथवीराज नगर योजना के सम्बन्ध में राज्य सरकार द्वारा जारी आदेशो के अर्न्तगत आवसीय पट्टा विलेख आवंटन/विक्रय पत्र क्रमांक-{document_no} दिनांक {date} ईस्वी को {claimant} के हित में निष्पादित कर दिया, उक्त पट्टा-विलेख आवंटन/विक्रय-पत्र का पंजीयन {reg_office} के यहां दिनांक {reg_date} को पुस्तक संख्या {reg_book}, जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book}, जिल्द संख्या {reg_add_vol} के पृष्ठ संख्या {reg_add_page_start} से {reg_add_page_end} पर चस्पा किया गया। इस प्रकार {claimant} उक्त सम्पत्ति {owner_suffix}",
    
    # RIICO Plot Allotment
    "ALLOTMENT_PLOT_NO_DEPOSIT": "यह कि सर्वप्रथम उक्त सम्पत्ति बाबत् {claimant}, ने कार्यालय {authority_name} में नियमानुसार राशि जमा करवा दी, जिसके पश्चात् उक्त सम्पत्ति बाबत् {authority_name} ने पट्टा विलेख/ आवंटन/ विक्रय-पत्र संख्या {document_no} दिनाँकित {date} ईस्वी को {claimant} के नाम से एवं हित में निष्पादित कर जारी कर दिया, उक्त पट्टा-विलेख/ आवंटन/ विक्रय-पत्र का पंजीयन {reg_office} के यहां दिनांक {reg_date} को पुस्तक संख्या {reg_book}, जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book}, जिल्द संख्या {reg_add_vol} के पृष्ठ संख्या {reg_add_page_start} से {reg_add_page_end} पर चस्पा किया गया है। इस प्रकार {claimant} उक्त सम्पत्ति {owner_suffix}",
    
    # JDA Flat Allotment
    "ALLOTMENT_FLAT": "यह कि सर्वप्रथम {full_address} जिसकी चारो सीमाओे में पूर्व की ओर {boundary_east}, पश्चिम की ओर {boundary_west}, उत्तर की ओर {boundary_north} एवं् दक्षिण की ओर {boundary_south} स्थित हैं, जिसका कुल क्षेत्रफल {total_area} {area_unit} है, जिसे उक्त इकरारनामा में ‘‘उक्त मूल सम्पत्ति’’ कहा गया है। उक्त मूल सम्पत्ति बाबत् {claimant} ने कार्यालय {authority_name} में नियमन राशि व लीज राशि नियमानुसार जमा करवा दी जिसके पश्चात् उक्त सम्पत्ति बाबत् {claimant} के नाम से कार्यालय {authority_name} ने पट्टा विलेख आवंटन/विक्रय-पत्र संख्या {document_no} दिनांक {date} ईस्वी को {claimant} के हित में निष्पादित कर दिया, उक्त पट्टा-विलेख आवंटन/विक्रय-पत्र का पंजीयन {reg_office} के यहां दिनांक {reg_date} को पुस्तक संख्या {reg_book}, जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book}, जिल्द संख्या {reg_add_vol} के पृष्ठ संख्या {reg_add_page_start} से {reg_add_page_end} पर चस्पा किया गया। इस प्रकार {claimant} उक्त मूल सम्पत्ति {owner_suffix}",
    
    # UIT Flat Allotment (Nagar Nigam / UIT)
    "ALLOTMENT_FLAT_NO_DEPOSIT": "यह कि सर्वप्रथम {full_address} जिसकी नाप पूर्व से पश्चिम {east_to_west} एवं उत्तर से दक्षिण {north_to_south} है, जिसका कुल क्षेत्रफल {total_area} {area_unit} है, जिसकी चारों सीमाओें में पूर्व की ओर {boundary_east}, पश्चिम की ओर {boundary_west}, उत्तर की ओर {boundary_north} एवं दक्षिण की ओर {boundary_south} है, जिसे उक्त विक्रय पत्र में ‘‘उक्त प्रथम सम्पत्ति’’ कहा गया है, बाबत् {claimant} ने कार्यालय {authority_name} में नियमन राशि व लीज राशि नियमानुसार जमा करवा दी, जिसके पश्चात् कार्यालय {authority_name} ने पट्टा विलेख आवंटन/विक्रय-पत्र संख्या {document_no} दिनाँक {date} ईस्वी को {claimant} के हित में निष्पादित कर जारी कर दिया, उक्त पट्टा-विलेख आवंटन/विक्रय-पत्र का पंजीयन {reg_office} के यहां दिनांक {reg_date} को पुस्तक संख्या {reg_book} जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book} जिल्द संख्या {reg_add_vol} के पृष्ठ संख्या {reg_add_page_start} से {reg_add_page_end} पर चस्पा किया गया। इस प्रकार {claimant} उक्त प्रथम सम्पत्ति {owner_suffix}",
    
    # NNJ Plot Allotment (Municipal Board)
    "ALLOTMENT_MUNICIPAL_PLOT": "यह कि सर्वप्रथम उक्त सम्पत्ति का आंवटन बाबत् {claimant} ने कार्यालय {authority_name} में नियमन राशि व लीज राशि नियमानुसार जमा करवा दी, जिसके पश्चात् कार्यालय {authority_name} ने पट्टा विलेख/ आवंटन/विक्रय-पत्र संख्या {document_no} दिनाँक {date} ईस्वी को {claimant} के हित में निष्पादित कर जारी कर दिया, इस प्रकार {claimant} उक्त सम्पत्ति {owner_suffix}",
    
    # NNJ Flat Allotment
    "ALLOTMENT_MUNICIPAL_FLAT": "यह कि सर्वप्रथम {full_address} जिसकी नाप पूर्व से पश्चिम {east_to_west} एवं उत्तर से दक्षिण {north_to_south} है, जिसका कुल क्षेत्रफल {total_area} {area_unit} है, जिसकी चारों सीमाओं में पूर्व की ओर {boundary_east}, पश्चिम की ओर {boundary_west}, उत्तर की ओर {boundary_north} एवं दक्षिण की ओर {boundary_south} स्थित है, जिसे उक्त विक्रय पत्र में ‘‘उक्त मूल सम्पत्ति’’ कहा गया है, बाबत् {claimant} ने कार्यालय {authority_name} में नियमन राशि व लीज राशि नियमानुसार जमा करवा दी एवं कार्यालय {authority_name} ने पट्टा विलेख/ आवंटन/ विक्रय-पत्र संख्या {document_no} दिनाँकित {date} ईस्वी को {claimant} के हित में निष्पादित कर जारी कर दिया, उक्त पट्टा-विलेख आवंटन/विक्रय-पत्र का पंजीयन {reg_office} के यहां दिनांक {reg_date} ईस्वी को पुस्तक संख्या {reg_book} जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book} जिल्द संख्या {reg_add_vol} के पृष्ठ संख्या {reg_add_page_start} से {reg_add_page_end} पर चस्पा किया गया। इस प्रकार {claimant} उक्त मूल सम्पत्ति {owner_suffix}",
    
    # Cooperative Society Allotment
    "ALLOTMENT_SOCIETY": "यह कि सर्वप्रथम उक्त सम्पत्ति {authority_name} (पंजीयन क्रमांक {society_reg_no}) द्वारा {claimant} को जरिये आवंटन पत्र दिनांकित {date} द्वारा आवंटित किया गया था तथा उक्त सम्पत्ति की मांगी गई समस्त राशियाँ {claimant} ने जरिये रसीद संख्या {receipt_no} दिनांकित {receipt_date} को जमा करवा कर उक्त सम्पत्ति का कब्जा वास्तविक मौके पर मय साइट प्लान के साथ प्राप्त कर लिया। इस प्रकार {claimant} उक्त सम्पत्ति {owner_suffix}",
    
    # RHB Plot Allotment (Lease Deed)
    "LEASE_DEED": "यह कि सर्वप्रथम उक्त सम्पत्ति का आवंटन कार्यालय {authority_name} द्वारा {claimant} के नाम से जरिये आवंटन पत्र संख्या {document_no} दिनांकित {date} द्वारा आवंटित किया गया था, तत्पश्चात् कार्यालय {authority_name} द्वारा उक्त सम्पत्ति का कब्जा जरिये कब्जा पत्र संख्या {possession_no} दिनांकित {possession_date} को {claimant} को सम्भला दिया। तत्पश्चात् {claimant} ने कार्यालय {authority_name} द्वारा उक्त सम्पत्ति की चाही गयी समस्त राशियां जमा करवा दी तथा कार्यालय {authority_name} द्वारा उक्त सम्पत्ति बाबत अदेय प्रमाण पत्र दिनांकित {nodues_date} {claimant} के हित में जारी कर दिया। तत्पश्चात् कार्यालय {authority_name} द्वारा उक्त सम्पत्ति की परपेचुअल लीज (Perpetual Lease) दिनांकित {lease_date} एवं कन्वेयन्स डीड-अलॉटी (Conveyance Deed Allottee) दिनांकित {conveyance_date} को {claimant} के नाम से जारी कर दिये, जिसमें से परपेचुअल लीज डीड का पंजीयन {reg_office} के यहाँ दिनांक {reg_date} ईस्वी को पुस्तक संख्या {reg_book} जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध हुआ तथा अतिरिक्त पुस्तक संख्या {reg_add_book} जिल्द संख्या {reg_add_vol} सीरियल नम्बर {reg_add_serial} के पृष्ठ संख्या {reg_add_page_start} से {reg_add_page_end} पर चस्पा हुई एवं कन्वेयन्स डीड का पंजीयन {reg_office} के यहाँ दिनांक {reg_date} ईस्वी को पुस्तक संख्या {conv_reg_book} जिल्द संख्या {conv_reg_vol} में पृष्ठ संख्या {conv_reg_page} क्रम संख्या {conv_reg_no} पर पंजीबद्ध हुआ तथा अतिरिक्त पुस्तक संख्या {conv_reg_add_book} जिल्द संख्या {conv_reg_add_vol} सीरियल नम्बर {conv_reg_add_serial} के पृष्ठ संख्या {conv_reg_add_page_start} से {conv_reg_add_page_end} पर चस्पा हुई। इस प्रकार {claimant} उक्त सम्पत्ति {owner_suffix}",
    
    # Part Sale (JDA default)
    "PART_SALE": "यह कि सर्वप्रथम  प्लाट नम्बर-40, छत्रसाल नगर ब्लॉक सी, नन्दपुरी, मालवीय नगर, जयपुर, राजस्थान में स्थित है, जिसकी नाप पूर्व से पश्चिम 60  फीट एवं उत्तर से दक्षिण 15  फीट है, जिसका कुल क्षेत्रफल 150.00  वर्गगज है, इसकी चारों सीमाओं में पूर्व की ओर प्लाट नम्बर 39, पश्चिम की ओर प्लाट नम्बर 41, उत्तर की ओर रोड़ 30  फीट चौड़ी आमद्रफत् सरकारी एवं दक्षिण की ओर प्लाट नम्बर 38 स्थित है, जिसे उक्त विक्रय पत्र में आगे ‘‘उक्त मूल सम्पत्ति’’ कहा गया है, बाबत {claimant} ने कार्यालय {authority_name} में नियमन राशि व लीज राशि नियमानुसार जमा करवा दी, जिसके पश्चात् उक्त मूल सम्पत्ति बाबत् कार्यालय {authority_name} ने पट्टा विलेख आवंटन/विक्रय-पत्र संख्या {document_no} दिनाँक {date} ईस्वी को {claimant} के नाम से एवं हित में निष्पादित कर जारी कर दिया, उक्त पट्टा-विलेख आवंटन/विक्रय-पत्र का पंजीयन {reg_office} के यहां दिनांक {reg_date} को पुस्तक संख्या {reg_book} जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book} जिल्द संख्या {reg_add_vol} के पृष्ठ संख्या {reg_add_page_start} से {reg_add_page_end} पर चस्पा किया गया। इस प्रकार {claimant} उक्त मूल सम्पत्ति {owner_suffix}",
    
    # Part Sale Society
    "TRANSFER_PLOT": "यह कि सर्वप्रथम {full_address} जिसकी नाप पूर्व से पश्चिम {east_to_west} एंव उत्तर से दक्षिण {north_to_south} है। जिसका कुल क्षेत्रफल {total_area} {area_unit} है। इसकी चारों सीमाओं में पूर्व की ओर {boundary_east}, पश्चिम की ओर {boundary_west}, उत्तर की ओर {boundary_north}, एंव दक्षिण की ओर {boundary_south} स्थित है, जिसे उक्त विक्रय पत्र में आगे ‘‘उक्त मूल सम्पत्ति’’ कहा गया है को {authority_name} द्वारा {claimant}, को जरिये आवंटन पत्र आंवटित किया गया था तथा उक्त मूल सम्पत्ति की मांगी गई समस्त राशियाँ उक्त समिति में जरिये रसीद जमा करवा कर उक्त मूल सम्पत्ति का कब्जा वास्तविक मोके पर मय साइट प्लान के साथ प्राप्त कर लिया। इस प्रकार प्रथमपक्ष {claimant} उक्त मूल सम्पत्ति {owner_suffix}",
    
    # Part Sale NNJ
    "TRANSFER_FLAT": "यह कि सर्वप्रथम {full_address} जिसका कुल क्षेत्रफल {total_area} {area_unit} है, जिसकी चारों सीमाओं में पूर्व की ओर {boundary_east}, पश्चिम की ओर {boundary_west}, उत्तर की ओर {boundary_north} एवं दक्षिण की ओर {boundary_south} स्थित है, जिसे उक्त विक्रय पत्र में आगे ‘‘उक्त मूल सम्पत्ति’’ कहा गया है, बाबत् {claimant} ने कार्यालय {authority_name} में नियमन राशि व लीज राशि नियमानुसार जमा करवा दी, जिसके पश्चात् उक्त मूल सम्पत्ति बाबत् कार्यालय {authority_name} ने पट्टा विलेख/विक्रय-पत्र संख्या-{document_no} दिनाँकित {date} ईस्वी को {claimant} के नाम से एवं हित में निष्पादित कर जारी कर दिया, उक्त पट्टा-विलेख/विक्रय-पत्र का पंजीयन {reg_office} के यहां दिनांक {reg_date} को पुस्तक संख्या {reg_book} जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book} जिल्द संख्या {reg_add_vol} के पृष्ठ संख्या {reg_add_page_start} से {reg_add_page_end} पर चस्पा किया गया। इस प्रकार {claimant} उक्त मूल सम्पत्ति {owner_suffix}",
 
    # --- Subsequent Event (Standard) Templates ---
    # Subsequent Sale Deed (Plot)
    "SALE_DEED_PLOT": "यह कि तत्पश्चात् {executant} ने उक्त सम्पत्ति को जरिये पंजीकृत विक्रय पत्र दिनांक {date} के द्वारा {claimant} को विक्रय कर दिया, जिसके विक्रय पत्र का पंजीयन {reg_office} के यहां दिनांक {reg_date} को पुस्तक संख्या {reg_book}, जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book}, जिल्द संख्या {reg_add_vol} के पृष्ठ संख्या {reg_add_page_start} से {reg_add_page_end} पर चस्पा किया गया। इस प्रकार {claimant} उक्त सम्पत्ति {owner_suffix}",
    
    # Subsequent Sale Deed (Flat)
    "SALE_DEED_FLAT": "यह कि तत्पश्चात् {executant} ने उक्त फ्लैट को जरिये पंजीकृत विक्रय पत्र दिनांक {date} के द्वारा {claimant} को विक्रय कर दिया, जिसके विक्रय पत्र का पंजीयन {reg_office} के यहां दिनांक {reg_date} को पुस्तक संख्या {reg_book}, जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book}, जिल्द संख्या {reg_add_vol} के पृष्ठ संख्या {reg_add_page_start} से {reg_add_page_end} पर चस्पा किया गया। इस प्रकार {claimant} उक्त फ्लैट {owner_suffix}",
 
    # Gift Deed
    "GIFT_DEED": "यह कि तत्पश्चात् {executant} ने उक्त सम्पत्ति को {claimant} को दिनांक {date} को निष्पादित बख्शीशनामा/दान पत्र के जरिये उपहार स्वरूप दे दिया, जिसका पंजीयन {reg_office} के यहां दिनांक {reg_date} को पुस्तक संख्या {reg_book}, जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book}, जिल्द संख्या {reg_add_vol} के पृष्ठ संख्या {reg_add_page_start} से {reg_add_page_end} पर चस्पा किया गया। इस प्रकार {claimant} उक्त सम्पत्ति {owner_suffix}",
    
    # Hak Tyag (Relinquishment)
    "HAK_TYAG": "यह कि तत्पश्चात् {executant} ने उक्त सम्पत्ति में से अपने संपूर्ण हिस्से, हक व अधिकारों का परित्याग {claimant} के पक्ष में दिनांक {date} को निष्पादित हकत्याग पत्र के जरिये कर दिया, जिसका पंजीयन {reg_office} के यहां दिनांक {reg_date} को पुस्तक संख्या {reg_book}, जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book}, जिल्द संख्या {reg_add_vol} के पृष्ठ संख्या {reg_add_page_start} से {reg_add_page_end} पर चस्पा किया गया। इस प्रकार {claimant} उक्त सम्पत्ति {owner_suffix}",
    
    # Will
    "WILL": "यह कि तत्पश्चात् {executant} ने अपने जीवनकाल में उक्त सम्पत्ति के सम्बन्ध में एक वसीयतनामा दिनांकित {date} को {claimant} के पक्ष में निष्पादित कर दिया था। तत्पश्चात् वसीयतकर्ता {executant} की मृत्यु हो जाने के बाद उक्त वसीयतनामा के आधार पर {claimant} उक्त सम्पत्ति {owner_suffix}",
    
    # Death / Succession
    "DEATH_HEIRS_SINGLE": "यह कि तत्पश्चात् उक्त सम्पत्ति के स्वामी {executant} की मृत्यु दिनांक {death_date} को हो गई, जिसके पश्चात् उनके विधिक उत्तराधिकारी के रूप में {claimant} उक्त सम्पत्ति {owner_suffix}",
    "DEATH_HEIRS_WITH_SPOUSE": "यह कि तत्पश्चात् उक्त सम्पत्ति के स्वामी {executant} की मृत्यु दिनांक {death_date} को हो गई, जिसके पश्चात् उनके विधिक उत्तराधिकारी के रूप में {claimant} उक्त सम्पत्ति {owner_suffix}",
    "DEATH_DIVIDED": "यह कि तत्पश्चात् उक्त सम्पत्ति के स्वामी {executant} की मृत्यु दिनांक {death_date} को हो गई, जिसके पश्चात् उनके विधिक उत्तराधिकारी के रूप में {claimant} उक्त सम्पत्ति {owner_suffix}",

    # Construction / Development
    "CONSTRUCTION_FLAT": "यह कि तत्पश्चात् {executant} ने अपने अधिकारों का प्रयोग करते हुए उक्त सम्पत्ति {plot_ref} क्षेत्रफल {area} भूमि पर {unit_details} का निर्माण करवा लिया तथा उसका नाम “{project_name}” रख दिया।",
    "CONSTRUCTION_FLAT_NO_NAME": "यह कि तत्पश्चात् {executant} ने अपने अधिकारों का प्रयोग करते हुए उक्त सम्पत्ति {plot_ref} क्षेत्रफल {area} भूमि पर {unit_details} का निर्माण करवा लिया।",

    # Partition / Subdivision & Sale Combined (Case 3 Priyanka Jadon style)
    "PARTITION_SALE": "यह कि तत्पश्चात् {executant} ने उक्त सम्पत्ति {parent_plots} संयुक्त क्षेत्रफल {parent_area} को विभाजित कर लिया तथा विभाजित क्षेत्रफल {divided_area} को जरिये पंजीकृत विक्रय पत्र दिनांक {date} के द्वारा {claimant} को विक्रय कर दिया, जिसके विक्रय पत्र का पंजीयन {reg_office} के यहां दिनांक {reg_date} को पुस्तक संख्या {reg_book}, जिल्द संख्या {reg_vol} में पृष्ठ संख्या {reg_page} क्रम संख्या {reg_no} पर पंजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या {reg_add_book}, जिल्द संख्या {reg_add_vol} के पृष्ठ संख्या {reg_add_page_start} से {reg_add_page_end} पर चस्पा किया गया। इस प्रकार {claimant} उक्त सम्पत्ति {owner_suffix}",

    # Transfer Letter / Certificate (Case 4 Dinesh Khandelwal style)
    "TRANSFER_CERTIFICATE": "यह कि तत्पश्चात् {claimant} ने उक्त सम्पत्ति के बाबत हस्तान्तरण राशि के रूपये नियमानुसार कार्यालय {authority_name} में जमा कराये, जिसके पश्चात् कार्यालय {authority_name} द्वारा हस्तान्तरण पत्र क्रमांक {document_no} दिनांक {date} को {claimant} के नाम से जारी किया गया। इस प्रकार {claimant} उक्त सम्पत्ति {owner_suffix}",

    # Unused / fallback templates
    "AGRICULTURAL_ALLOTMENT": "",
    "POA_AGRICULTURAL": "",
    "COLONY_DEVELOPMENT": "",
    "POA_NON_AGRICULTURAL": "",
    "DEVELOPER_AGREEMENT": "",
    "PARTITION": ""
}

REGISTRATION_TEMPLATES = {
    "ALLOTMENT": "",
    "GENERAL": ""
}

CHAIN_TEMPLATE_METADATA = {
    "ALLOTMENT_PLOT": {
        "label": "Allotment (Plot, JDA)",
        "description": "Original allotment of a residential/commercial plot by JDA, mentioning deposit of regulation/lease fees.",
        "event_type": "ALLOTMENT"
    },
    "ALLOTMENT_PLOT_NO_DEPOSIT": {
        "label": "Allotment (Plot, RIICO)",
        "description": "Original allotment of a plot by RIICO, mentioning fee deposit details.",
        "event_type": "ALLOTMENT"
    },
    "ALLOTMENT_FLAT": {
        "label": "Allotment (Flat, JDA)",
        "description": "Original allotment of a flat/apartment by JDA, mentioning fee deposit.",
        "event_type": "ALLOTMENT"
    },
    "ALLOTMENT_FLAT_NO_DEPOSIT": {
        "label": "Allotment (Flat, NNJ/UIT)",
        "description": "Original allotment of a flat/apartment by NNJ or UIT, mentioning fee deposit.",
        "event_type": "ALLOTMENT"
    },
    "ALLOTMENT_MUNICIPAL_PLOT": {
        "label": "Municipal Allotment (Plot, NNJ)",
        "description": "Allotment of a plot by a local Municipal Board / Corporation (नगर निगम).",
        "event_type": "ALLOTMENT"
    },
    "ALLOTMENT_MUNICIPAL_FLAT": {
        "label": "Municipal Allotment (Flat, NNJ)",
        "description": "Allotment of a flat/apartment by a local Municipal Corporation (नगर निगम).",
        "event_type": "ALLOTMENT"
    },
    "ALLOTMENT_SOCIETY": {
        "label": "Cooperative Society Allotment (1 Receipt)",
        "description": "Allotment of a plot by a housing cooperative society (गृह निर्माण सहकारी समिति) with receipt.",
        "event_type": "ALLOTMENT"
    },
    "LEASE_DEED": {
        "label": "RHB Allotment (Lease Deed)",
        "description": "Perpetual Lease Deed and Conveyance Deed executed by Rajasthan Housing Board.",
        "event_type": "ALLOTMENT"
    },
    "PART_SALE": {
        "label": "Partial Share Sale (JDA)",
        "description": "Sale deed transferring a specific undivided fraction/share of the property (JDA).",
        "event_type": "SALE_DEED"
    },
    "TRANSFER_PLOT": {
        "label": "Partial Share Sale (Society)",
        "description": "Sale deed transferring a specific undivided fraction/share of the property (Society).",
        "event_type": "SALE_DEED"
    },
    "TRANSFER_FLAT": {
        "label": "Partial Share Sale (NNJ)",
        "description": "Sale deed transferring a specific undivided fraction/share of the property (NNJ).",
        "event_type": "SALE_DEED"
    },
    "SALE_DEED_PLOT": {
        "label": "Sale Deed (Plot)",
        "description": "Standard registered sale deed (विक्रय पत्र) transferring ownership of a plot.",
        "event_type": "SALE_DEED"
    },
    "SALE_DEED_FLAT": {
        "label": "Sale Deed (Flat)",
        "description": "Standard registered sale deed transferring ownership of a flat/apartment.",
        "event_type": "SALE_DEED"
    },
    "GIFT_DEED": {
        "label": "Gift Deed (दान पत्र)",
        "description": "Registered Gift Deed (बख्शीशनामा/दानपत्र) transferring ownership.",
        "event_type": "GIFT_DEED"
    },
    "HAK_TYAG": {
        "label": "Hak Tyag (Relinquishment)",
        "description": "Relinquishment of undivided rights/shares (हकत्याग पत्र) in a property.",
        "event_type": "HAK_TYAG"
    },
    "WILL": {
        "label": "Will (वसीयतनामा)",
        "description": "Transfer of property through a registered or unregistered Will.",
        "event_type": "WILL"
    },
    "DEATH_HEIRS_SINGLE": {
        "label": "Inheritance (Succession)",
        "description": "Succession of property to legal heirs after the demise of the owner.",
        "event_type": "DEATH"
    },
    "PARTITION_SALE": {
        "label": "Partition and Sale Deed",
        "description": "Subdivision/partition of plot(s) followed by immediate sale deed.",
        "event_type": "SALE_DEED"
    },
    "TRANSFER_CERTIFICATE": {
        "label": "Transfer Certificate/Letter (हस्तान्तरण पत्र)",
        "description": "Transfer letter/certificate issued by local authority.",
        "event_type": "TRANSFER"
    }
}

# Try to load custom templates and metadata from local JSON if available
JSON_PATH = os.path.join(os.path.dirname(__file__), "custom_chain_templates.json")
if os.path.exists(JSON_PATH):
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                if "templates" in data:
                    CHAIN_TEMPLATES.update(data["templates"])
                if "metadata" in data:
                    CHAIN_TEMPLATE_METADATA.update(data["metadata"])
    except Exception as e:
        print(f"Warning: Failed to load custom_chain_templates.json: {e}")
