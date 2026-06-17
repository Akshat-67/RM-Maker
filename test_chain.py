import json
from modules.sd.narrative import generate_chain_narrative

sess = json.load(open('cases/case_1781374115/session.json', encoding='utf-8'))
paras = generate_chain_narrative(sess['data']['title_chain'])
print(paras[3])
