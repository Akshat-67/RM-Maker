import re
import json

def clean_and_escape_json_lines(json_str):
    cleaned_lines = []
    for line in json_str.splitlines():
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
        
    return "\n".join(cleaned_lines)

def main():
    with open("scratch/llama_8b_clean.txt", "r", encoding="utf-8") as f:
        raw = f.read()
        
    # Strip markdown block if present
    m = re.search(r'```json\s*(.*?)\s*```', raw, re.DOTALL | re.IGNORECASE)
    if m:
        candidate = m.group(1)
    else:
        m = re.search(r'(\{.*\})', raw, re.DOTALL)
        candidate = m.group(1) if m else raw
        
    print("Cleaning JSON...")
    cleaned = clean_and_escape_json_lines(candidate)
    
    print("Attempting json.loads...")
    try:
        data = json.loads(cleaned)
        print("SUCCESS! Successfully parsed JSON with loads()!")
        print(f"Parsed {len(data)} items.")
        # Print a few items to check escaping
        count = 0
        for k, v in data.items():
            if 'o"kZ' in k or 'o\"kZ' in k:
                print(f"Escaped key check: {k} -> {v}")
                count += 1
                if count >= 3: break
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    main()
