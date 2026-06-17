import ast
import re

with open('utils/devlys_converter.py', 'r', encoding='utf-8') as f:
    text = f.read()

m1 = re.search(r'array_one\s*=\s*(\[.*?\])', text, re.DOTALL)
m2 = re.search(r'array_two\s*=\s*(\[.*?\])', text, re.DOTALL)

try:
    a1 = ast.literal_eval(m1.group(1))
    a2 = ast.literal_eval(m2.group(1))
    print(f'Length 1: {len(a1)}')
    print(f'Length 2: {len(a2)}')
    for i in range(min(len(a1), len(a2))):
        print(f"'{a1[i]}' -> '{a2[i]}'")
    
    if len(a1) != len(a2):
        print("ARRAYS DO NOT MATCH IN LENGTH")
except Exception as e:
    print(e)
