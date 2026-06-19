import os
from google import genai

API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4")
]

for i, key in enumerate(API_KEYS):
    print(f"\nTesting Key Index {i} ({key[:10]}...) on gemini-2.5-flash:")
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="hello"
        )
        print(f"  [SUCCESS] {response.text.strip()}")
    except Exception as e:
        print(f"  [FAIL] {e}")
