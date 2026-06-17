import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import inspect
import ast
import utils.devlys_converter

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    source = inspect.getsource(utils.devlys_converter.unicode_to_devlys)
    tree = ast.parse(source)
    
    array_one = None
    array_two = None
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == 'array_one':
                        array_one = ast.literal_eval(node.value)
                    elif target.id == 'array_two':
                        array_two = ast.literal_eval(node.value)
                        
    if array_one and array_two:
        print(f"array_one length: {len(array_one)}, array_two length: {len(array_two)}")
        for i, (u, d) in enumerate(zip(array_one, array_two)):
            print(f"{i:3d}: {u!r:10s} <=> {d!r}")

if __name__ == "__main__":
    main()
