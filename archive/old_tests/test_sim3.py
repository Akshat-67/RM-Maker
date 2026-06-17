import sys, json, difflib
with open('scratch/debug_sim.json', encoding='utf-8') as f:
    d = json.load(f)

ai = d['ai']
act = d['actual']

with open('scratch/diff_report.txt', 'w', encoding='utf-8') as f:
    matcher = difflib.SequenceMatcher(None, ai, act)
    for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
        if opcode == 'equal': continue
        f.write(f"\n[{opcode}] AI[{a0}:{a1}] vs ACTUAL[{b0}:{b1}]\n")
        f.write(f"  AI: {ai[a0][:100] if a1>a0 else '---'}\n")
        f.write(f"  ACTUAL: {act[b0][:100] if b1>b0 else '---'}\n")
