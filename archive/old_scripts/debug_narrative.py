import json
import sys
sys.path.insert(0, '.')
from modules.sd.narrative import generate_chain_narrative

d = json.load(open('cases/case_1781374115/session.json', encoding='utf-8')).get('data', {})
chain = d.get('title_chain', [])
ps0 = d.get('ps', [{}])[0]

print("Title Chain length:", len(chain))
print("First event:", json.dumps(chain[0], ensure_ascii=False))

paras = generate_chain_narrative(chain, property_details=ps0)
print("Generated paragraphs:", len(paras))
for p in paras:
    print(p[:50])
