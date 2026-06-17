import json, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\aksha\Documents\RM Generator\RM-Maker')
from utils.helpers import KrutiDev_to_Unicode

with open(r'C:\Users\aksha\Documents\RM Generator\RM-Maker\Test\ai_paras.json', encoding='utf-8') as f:
    ai = json.load(f)
with open(r'C:\Users\aksha\Documents\RM Generator\RM-Maker\Test\actual_paras.json', encoding='utf-8') as f:
    actual = json.load(f)

def decode(t):
    t = t.replace('~~HL~~','')
    try: return KrutiDev_to_Unicode(t)
    except: return t

print('=== PROPERTY DESCRIPTION (para about current flat) ===')
print('AI [5]:', decode(ai.get('5','')))
print()
print('ACTUAL [26]:', decode(actual.get('26','')))
print()

print('=== ORIGINAL PROPERTY + DIMENSIONS + BOUNDARIES (chain start) ===')
print('AI [6]:', decode(ai.get('6','')))
print()
print('ACTUAL [28]:', decode(actual.get('28','')))
print()

print('=== CHAIN EVENT 2 - first sale deed ===')
print('AI [8]:', decode(ai.get('8','')))
print()
print('ACTUAL [30]:', decode(actual.get('30','')))
print()

print('=== CHAIN EVENT 3 - builder construction + naming ===')
print('ACTUAL [32]:', decode(actual.get('32','')))
print()

print('=== CHAIN EVENT 4 - sale to current sellers ===')
print('AI [10]:', decode(ai.get('10','')))
print()
print('ACTUAL [34]:', decode(actual.get('34','')))
print()

print('=== PROPERTY SCHEDULE ===')
print('AI [28]:', decode(ai.get('28','')))
print()
print('ACTUAL [61]:', decode(actual.get('61','')))
