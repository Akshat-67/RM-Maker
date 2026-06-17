import os
from google import genai

API_KEYS = [
    "AIzaSyBKkvXn_tTX2YVK_YzQPkm7FUDtYju43hc",
    "AIzaSyAXF1GYok40JQPkzg3rv2b_CGVJjDsaze8",
    "AQ.Ab8RN6LT45vwhXCygf42E1_cCExGjyFvD95qNo1vQ37hC3ZnBQ",
    "AIzaSyDs32YIJx35FDhb9qOa3vTcWDtU-RpL5_w"
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
