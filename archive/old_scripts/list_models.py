import sys
sys.path.insert(0, '.')
from extractor import DataExtractor

e = DataExtractor(api_keys=[
    os.getenv("GEMINI_API_KEY_1")
])

print("Available models:")
models = e.get_available_models()
for m in sorted(models):
    if 'flash' in m.lower() or 'pro' in m.lower():
        print(" ", m)
