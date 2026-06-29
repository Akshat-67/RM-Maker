import json
from modules.sd.narrative import generate_chain_narrative

sess = json.load(open('cases/case_1781374115/session.json', encoding='utf-8'))
paras = generate_chain_narrative(sess['data']['title_chain'])
with open('tests/test_chain_output.txt', 'w', encoding='utf-8') as f:
    for p in paras:
        f.write(p + "\n\n")
print("Successfully generated chain narrative and wrote to tests/test_chain_output.txt")
