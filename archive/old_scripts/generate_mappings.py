import re
import ast

def main():
    with open('utils/devlys_converter.py', 'r', encoding='latin-1') as f:
        content = f.read()

    a1_match = re.search(r'array_one\s*=\s*(\[.*?\])', content, re.DOTALL)
    a2_match = re.search(r'array_two\s*=\s*(\[.*?\])', content, re.DOTALL)
    if not a1_match or not a2_match:
        print("Could not find array_one or array_two in utils/devlys_converter.py")
        return

    a1 = ast.literal_eval(a1_match.group(1))
    a2 = ast.literal_eval(a2_match.group(1))
    
    # Invert mapping
    pairs = []
    seen_keys = set()
    
    # Add manual/special mappings that are handled by custom logic in devlys_converter.py
    # like 'f' -> 'ि', or any others
    pairs.append(('f', 'ि'))
    seen_keys.add('f')
    
    for uni, dev in zip(a1, a2):
        dev_clean = dev.strip() if dev else ""
        uni_clean = uni.strip() if uni else ""
        
        # Don't overwrite if we already added a mapping for this key
        if dev and dev not in seen_keys:
            pairs.append((dev, uni))
            seen_keys.add(dev)
            
    # Also sort them by length of devlys string descending, and then alphabetically
    pairs.sort(key=lambda x: (len(x[0]), x[0]), reverse=True)
    
    print("MAPPING_PAIRS = [")
    for k, v in pairs:
        # Escape backslashes for python string literal print
        k_escaped = k.replace('\\', '\\\\').replace('"', '\\"')
        v_escaped = v.replace('\\', '\\\\').replace('"', '\\"')
        print(f'    ("{k_escaped}", "{v_escaped}"),')
    print("]")

if __name__ == "__main__":
    main()
