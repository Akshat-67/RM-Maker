import json
import sys
sys.path.insert(0, '.')
from modules.sd.narrative import generate_chain_narrative

d = json.load(open('cases/case_1781374115/session.json', encoding='utf-8')).get('data', {})
chain = d.get('title_chain', [])
ps0 = d.get('ps', [{}])[0]

paras = generate_chain_narrative(chain, property_details=ps0)
out = {
    "chain_0": chain[0] if chain else None,
    "paras": paras
}
json.dump(out, open('scratch/debug_out.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
