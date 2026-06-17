import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import inspect
import ast
import utils.devlys_converter

def main():
    source = inspect.getsource(utils.devlys_converter.unicode_to_devlys)
    tree = ast.parse(source)
    
    array_one = None
    array_two = None
    
    # Traverse AST to find array_one and array_two assignments
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == 'array_one':
                        array_one = ast.literal_eval(node.value)
                    elif target.id == 'array_two':
                        array_two = ast.literal_eval(node.value)
                        
    if array_one and array_two:
        pairs = []
        seen = set()
        
        # Add manual mappings
        pairs.append(('f', 'ि'))
        seen.add('f')
        
        for u, d in zip(array_one, array_two):
            if d and d not in seen:
                pairs.append((d, u))
                seen.add(d)
                
        # Sort long-to-short
        pairs.sort(key=lambda x: (len(x[0]), x[0]), reverse=True)
        
        print(f"Generated {len(pairs)} mapping pairs.")
        with open('scratch/generated_pairs.txt', 'w', encoding='utf-8') as f:
            f.write("MAPPING_PAIRS = [\n")
            for k, v in pairs:
                k_esc = k.replace('\\', '\\\\').replace('"', '\\"')
                v_esc = v.replace('\\', '\\\\').replace('"', '\\"')
                f.write(f'    ("{k_esc}", "{v_esc}"),\n')
            f.write("]\n")
        print("Mappings written to scratch/generated_pairs.txt")
    else:
        print("Could not extract arrays from source.")

if __name__ == "__main__":
    main()
