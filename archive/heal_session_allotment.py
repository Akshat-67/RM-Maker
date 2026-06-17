import json

case_path = 'cases/case_1781374115/session.json'
with open(case_path, "r", encoding="utf-8") as f:
    sess = json.load(f)

# Allotment doc number
sess["data"]["title_chain"][0]["document_number"] = "डी-2341"

with open(case_path, "w", encoding="utf-8") as f:
    json.dump(sess, f, ensure_ascii=False, indent=2)
print("Session healed with Allotment doc number.")
