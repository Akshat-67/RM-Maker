import json

case_path = 'cases/case_1781374115/session.json'
with open(case_path, "r", encoding="utf-8") as f:
    sess = json.load(f)

if "ps" in sess["data"] and len(sess["data"]["ps"]) > 0:
    sess["data"]["ps"][0]["landmark"] = "अजमेर रोड"

with open(case_path, "w", encoding="utf-8") as f:
    json.dump(sess, f, ensure_ascii=False, indent=2)
print("Session ps[0].landmark updated.")
