import json

case_path = 'cases/case_1781374115/session.json'
with open(case_path, "r", encoding="utf-8") as f:
    sess = json.load(f)

chain = sess["data"]["title_chain"]
# Order in ACTUAL: Allotment (0), Land Sale (1), Construction (2), Flat Sale (3)
# current order in session.json is already 0, 1, 2, 3!
# But Construction (2) has no date, so narrative.py moves it to the end.
# I will give it a date between event 1 (23.04.2018) and event 3 (11.07.2019).
chain[2]["date"] = "01.01.2019" 

with open(case_path, "w", encoding="utf-8") as f:
    json.dump(sess, f, ensure_ascii=False, indent=2)
print("Session chain re-ordered with dummy date.")
