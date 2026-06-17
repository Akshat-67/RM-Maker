import json

case_path = 'cases/case_1781374115/session.json'
with open(case_path, "r", encoding="utf-8") as f:
    sess = json.load(f)

# Witness 1
sess["data"]["ws"][0] = {
    "n": "विश्वनाथ",
    "relation_text": "पुत्र श्री भगवान सिंह",
    "adr": "फ्लैट न. 007 बी, 2 ब्लॉक, अनुपम अपार्टमेंट, प्रताप नगर, सांगानेर, सेक्टर 11 जयपुर राजस्थान-302033",
    "id": "" # ACTUAL has empty aadhaar for w1
}

# Witness 2
sess["data"]["ws"][1] = {
    "n": "पवन कुमार",
    "relation_text": "पुत्र श्री दाऊदयाल",
    "adr": "फ्लैट न- एल जी-1 लोवर, विनायक आपार्टमेंट, विनायक विहार, गणतिपुरा, भारत माता सर्किल, जयपुर, राजस्थान-302020",
    "id": "3730 5620 3432"
}

with open(case_path, "w", encoding="utf-8") as f:
    json.dump(sess, f, ensure_ascii=False, indent=2)
print("Session healed with Witness details.")
