import sys
import os
import json
import re
from docx import Document

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extractor import DataExtractor
from template_tools.builder_core import DocManipulator, get_discovery_prompt, clean_mapping

def extract_json_robust(text):
    if not text: return None
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        mapping_str = m.group(0)
        # Escape double quotes inside DevLys JSON keys and values
        cleaned_lines = []
        for line in mapping_str.splitlines():
            line_stripped = line.strip()
            if line_stripped in ('{', '}', '[', ']', '') or not line_stripped.startswith('"'):
                cleaned_lines.append(line)
                continue
            match_val = re.search(r':\s*(("(.*)"|null|true|false|\d+)\s*(,?)\s*)$', line_stripped)
            if not match_val:
                cleaned_lines.append(line)
                continue
            key_part = line_stripped[:match_val.start()].strip()
            val_part = match_val.group(1).strip()
            if key_part.startswith('"') and key_part.endswith('"'):
                raw_key = key_part[1:-1]
                escaped_key = raw_key.replace('\\"', '"').replace('"', '\\"')
                key_part = f'"{escaped_key}"'
            raw_val_match = re.match(r'^"(.*)"(,?)$', val_part)
            if raw_val_match:
                raw_val = raw_val_match.group(1)
                comma = raw_val_match.group(2)
                escaped_val = raw_val.replace('\\"', '"').replace('"', '\\"')
                val_part = f'"{escaped_val}"{comma}'
            indent = line[:len(line) - len(line.lstrip())]
            cleaned_lines.append(f'{indent}{key_part}: {val_part}')
        cleaned_mapping_str = "\n".join(cleaned_lines)
        try:
            return json.loads(cleaned_mapping_str)
        except Exception as e:
            print("Cleanup JSON parse failed, trying raw...", e)
            try:
                return json.loads(mapping_str)
            except Exception as e2:
                print("Raw JSON parse failed:", e2)
    return None

def main():
    path = "templates/SALE_DEED/SD-Vivek Saxena,  Sunita Saxena - Vijay Laxmi - JDA+2SD+Flat.docx"
    
    # Read raw AI response from file to avoid re-querying
    raw_path = "scratch/raw_ai_response.txt"
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} not found")
        return
        
    with open(raw_path, "r", encoding="utf-8") as f:
        raw = f.read()
        
    mapping = extract_json_robust(raw)
    if not mapping:
        print("Error: Could not extract JSON from response")
        return
        
    clean = clean_mapping(mapping)
    print(f"Success. Mapped {len(clean)} fields.")
    
    with open("scratch/fresh_discovery_mappings.json", "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=4, ensure_ascii=False)
    print("Mappings saved to scratch/fresh_discovery_mappings.json")

if __name__ == "__main__":
    main()
