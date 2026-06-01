import sys
sys.path.insert(0, '.')
from extractor import DataExtractor

e = DataExtractor(api_keys=[
    "AIzaSyBKkvXn_tTX2YVK_YzQPkm7FUDtYju43hc"
])

print("Available models:")
models = e.get_available_models()
for m in sorted(models):
    if 'flash' in m.lower() or 'pro' in m.lower():
        print(" ", m)
