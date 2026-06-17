import os
from google import genai

API_KEYS = [
    "AIzaSyBKkvXn_tTX2YVK_YzQPkm7FUDtYju43hc",
    "AIzaSyAXF1GYok40JQPkzg3rv2b_CGVJjDsaze8",
    "AQ.Ab8RN6LT45vwhXCygf42E1_cCExGjyFvD95qNo1vQ37hC3ZnBQ",
    "AIzaSyDs32YIJx35FDhb9qOa3vTcWDtU-RpL5_w"
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
