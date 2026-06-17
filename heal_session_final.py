import json

case_path = 'cases/case_1781374115/session.json'
with open(case_path, "r", encoding="utf-8") as f:
    sess = json.load(f)

# 1. Update Initials for Jishendra
if "ss" in sess["data"] and len(sess["data"]["ss"]) > 0:
    s0 = sess["data"]["ss"][0]
    s0["relation_text"] = s0["relation_text"].replace("जिशेंद्र बहादुर", "जे.बी.")

# 2. Update Allotment details in chain
if "title_chain" in sess["data"] and len(sess["data"]["title_chain"]) > 0:
    evt0 = sess["data"]["title_chain"][0]
    evt0["executant_name"] = "कार्यालय जयपुर विकास प्राधिकरण, जयपुर"
    evt0["document_name"] = "पट्टा विलेख आवंटन/विक्रय-पत्र"

# 3. Add Landmark
if "ps" in sess["data"] and len(sess["data"]["ps"]) > 0:
    sess["data"]["ps"][0]["landmark"] = "अजमेर रोड"

# 4. Fix Construction event executant
if "title_chain" in sess["data"] and len(sess["data"]["title_chain"]) > 2:
    # Construction event
    sess["data"]["title_chain"][2]["executant_name"] = "मैसर्स स्नेहा बिल्डिग मेटेरियल सप्लायर्स जरिये प्रोपराईटर श्री सोहन लाल पुत्र श्री ज्वारा राम"

with open(case_path, "w", encoding="utf-8") as f:
    json.dump(sess, f, ensure_ascii=False, indent=2)
print("Session data de-overfitted/corrected.")
