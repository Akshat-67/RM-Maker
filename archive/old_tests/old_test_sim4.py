import sys, json, difflib

with open('scratch/debug_sim.json', encoding='utf-8') as f:
    d = json.load(f)

ai_text = '\n'.join(d['ai'])
act_text = '\n'.join(d['actual'])

matcher = difflib.SequenceMatcher(None, ai_text, act_text)
diffs = []

for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
    if opcode == 'equal': continue
    ai_chunk = ai_text[a0:a1]
    act_chunk = act_text[b0:b1]
    
    # Heuristics for Section and Root Cause
    section = "Unknown"
    cause = "Unknown"
    
    if "विक्रय पत्र आज दिनांक" in ai_text[max(0, a0-50):a1+50]:
        section = "Preamble (Execution Date)"
        cause = "Missing Extraction Field"
    elif "श्री विवेक सक्सैना" in ai_chunk or "जे.बी. सक्सैना" in act_chunk:
        section = "First Party Details"
        if "आयु" in ai_chunk or "जाति" in ai_chunk: cause = "Missing Extraction Field"
        else: cause = "Missing Template Logic"
    elif "विजय लक्ष्मी" in ai_chunk or "धर्मेन्द्र सिंह" in act_chunk:
        section = "Second Party Details"
        if "आयु" in ai_chunk or "जाति" in ai_chunk: cause = "Missing Extraction Field"
        else: cause = "Missing Template Logic"
    elif "सुपर बिल्टअप एरिया" in ai_chunk or "फ्लैट नम्बर" in ai_chunk or "आवासीय" in act_chunk:
        section = "Property Description"
        cause = "Missing Property Detail"
    elif "तत्पश्चात्" in ai_chunk or "तत्पष्चात्" in act_chunk:
        section = "Title Chain Event"
        if "राजबाला" in ai_chunk and "स्नेहा बिल्िडंग" in act_chunk:
            cause = "Missing Chain Event (Wrong Executant)"
        else:
            cause = "Missing Validation Rule"
    elif "2000000" in ai_chunk or "20,00,000" in act_chunk:
        section = "Consideration Amount Clause"
        cause = "Missing Generation Logic"
    
    diff_len = max(len(ai_chunk), len(act_chunk))
    diffs.append({
        'section': section,
        'diff_len': diff_len,
        'cause': cause,
        'ai_snippet': ai_chunk.replace('\n', ' ')[:50] + '...' if ai_chunk else '',
        'act_snippet': act_chunk.replace('\n', ' ')[:50] + '...' if act_chunk else ''
    })

diffs.sort(key=lambda x: x['diff_len'], reverse=True)

with open('scratch/top_10_diffs.json', 'w', encoding='utf-8') as f:
    json.dump(diffs[:10], f, ensure_ascii=False, indent=2)

print("Done")
