import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.devlys_to_unicode import MAPPING_PAIRS as current_pairs

def load_generated():
    gen_pairs = []
    with open('scratch/generated_pairs.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple parse of the file
    import re
    matches = re.findall(r'\(\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\)', content)
    for k, v in matches:
        # Unescape
        k_unesc = k.replace('\\\\', '\\').replace('\\"', '"')
        v_unesc = v.replace('\\\\', '\\').replace('\\"', '"')
        gen_pairs.append((k_unesc, v_unesc))
    return gen_pairs

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    gen_pairs = load_generated()
    current_dict = dict(current_pairs)
    gen_dict = dict(gen_pairs)
    
    print(f"Current pairs: {len(current_pairs)}, Generated pairs: {len(gen_pairs)}")
    
    # Missing keys in current_pairs
    missing_keys = []
    for k in gen_dict:
        if k not in current_dict:
            missing_keys.append(k)
            
    print("\nKeys present in generated mapping but missing from current mapping:")
    for k in sorted(missing_keys, key=len, reverse=True):
        print(f"  {k!r} -> {gen_dict[k]!r}")
        
    # Keys present in current_pairs but missing from generated
    extra_keys = []
    for k in current_dict:
        if k not in gen_dict:
            extra_keys.append(k)
            
    print("\nKeys present in current mapping but missing from generated mapping:")
    for k in sorted(extra_keys, key=len, reverse=True):
        print(f"  {k!r} -> {current_dict[k]!r}")

    # Differences in values
    diff_keys = []
    for k in current_dict:
        if k in gen_dict and current_dict[k] != gen_dict[k]:
            diff_keys.append(k)
            
    print("\nDifferent mappings (current value vs generated value):")
    for k in sorted(diff_keys):
        print(f"  {k!r}: Current={current_dict[k]!r} | Generated={gen_dict[k]!r}")

if __name__ == "__main__":
    main()
