import json

case_path = 'cases/case_1781374115/session.json'
with open(case_path, "r", encoding="utf-8") as f:
    sess = json.load(f)

if len(sess["data"]["ss"]) == 1:
    sess["data"]["ss"].append({
        "n": "श्रीमती सुनीता सक्सेना",
        "a": "58",
        "c": "हिन्दु",
        "relation_text": "पत्नी श्री विवेक सक्सैना",
        "adr": "टी-28, जी.पी.आर.ए. काॅलोनी, टाइप-4, सेक्टर नम्बर 26, आकुर्डी रेलवे स्टेशन के पास, निगड़ी, प्राध्िाकरण, पुणे, महाराष्ट्र-411044",
        "id": "",
        "pan": ""
    })

with open(case_path, "w", encoding="utf-8") as f:
    json.dump(sess, f, ensure_ascii=False, indent=2)
print("Session healed with Sunita Saxena details.")
