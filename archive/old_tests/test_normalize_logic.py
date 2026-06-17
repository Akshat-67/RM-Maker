import sys
import os
sys.path.append(os.getcwd())

import json
from modules.sd.extractor import SDDataExtractor

session_path = r"cases/case_1781374115/session.json"
with open(session_path, "r", encoding="utf-8") as f:
    session = json.load(f)

data = session.get("data", {})

extractor = SDDataExtractor()

out = []
out.append("Before normalization:")
for idx, evt in enumerate(data.get("title_chain", [])):
    out.append(f"Event {idx+1}: executant={evt.get('executant_name')}, claimant={evt.get('claimant_name')}, project_name={evt.get('project_name')}")

# Call _normalize_sd_response
normalized = extractor._normalize_sd_response(data, 1, 1, 2)

out.append("\nAfter normalization:")
for idx, evt in enumerate(normalized.get("title_chain", [])):
    out.append(f"Event {idx+1}: executant={evt.get('executant_name')}, claimant={evt.get('claimant_name')}, project_name={evt.get('project_name')}")

with open("scratch/test_normalize_logic_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("Done writing to scratch/test_normalize_logic_output.txt")
