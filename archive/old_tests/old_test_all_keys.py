import os
from google import genai

API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4")
]

for i, key in enumerate(API_KEYS):
    print(f"\n--- Testing Key Index {i}: {key[:10]}...{key[-4:]} ---")
    try:
        client = genai.Client(api_key=key)
        # Try connectivity with gemini-2.5-flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="hello"
        )
        print(f"  [SUCCESS] gemini-2.5-flash: {response.text.strip()}")
    except Exception as e:
        print(f"  [FAIL] gemini-2.5-flash: {e}")
        
    try:
        client = genai.Client(api_key=key)
        # Try connectivity with gemini-2.0-flash
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents="hello"
        )
        print(f"  [SUCCESS] gemini-2.0-flash: {response.text.strip()}")
    except Exception as e:
        print(f"  [FAIL] gemini-2.0-flash: {e}")
