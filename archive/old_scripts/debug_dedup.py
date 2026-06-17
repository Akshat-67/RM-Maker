# scratch/debug_dedup.py
import json
import sys
sys.path.insert(0, '.')
from modules.sd.narrative import deduplicate_chain, generate_chain_narrative

with open(r'cases\case_1781374115\session.json', 'r', encoding='utf-8') as f:
    session = json.load(f)

context = session.get('data', {})
chain = context.get('title_chain', [])

with open(r'scratch\dedup_debug_out.txt', 'w', encoding='utf-8') as f:
    f.write('=== BEFORE DEDUPLICATION ===\n')
    for idx, evt in enumerate(chain):
        f.write(f"{idx+1}: type={evt.get('event_type')} exec={evt.get('executant_name')} claim={evt.get('claimant_name')}\n")

    deduped = deduplicate_chain(chain)
    f.write('\n=== AFTER DEDUPLICATION ===\n')
    for idx, evt in enumerate(deduped):
        f.write(f"{idx+1}: type={evt.get('event_type')} exec={evt.get('executant_name')} claim={evt.get('claimant_name')}\n")

    f.write('\n=== NARRATIVE OUTPUT ===\n')
    ps0 = context.get('ps', [{}])[0]
    paras = generate_chain_narrative(chain, property_details=ps0, context=context)
    f.write(f"Number of paras: {len(paras)}\n")
    for idx, p in enumerate(paras):
        f.write(f"\nPara {idx+1}:\n{p}\n")

print("SUCCESS")
