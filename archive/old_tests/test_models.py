import os
from google import genai

API_KEYS = [
    "AIzaSyBKkvXn_tTX2YVK_YzQPkm7FUDtYju43hc",
    "AIzaSyAXF1GYok40JQPkzg3rv2b_CGVJjDsaze8",
    "AQ.Ab8RN6LT45vwhXCygf42E1_cCExGjyFvD95qNo1vQ37hC3ZnBQ",
    "AIzaSyDs32YIJx35FDhb9qOa3vTcWDtU-RpL5_w"
]

MODELS = [
    'gemini-2.5-flash-lite',
    'gemini-2.0-flash-lite',
    'gemini-3.1-flash-lite',
    'gemini-3.5-flash',
    'gemini-flash-lite-latest',
    'gemini-flash-latest',
    'gemini-3-flash-preview',
    'gemini-2.5-flash'
]

for i, key in enumerate(API_KEYS):
    print(f"\n--- Testing Key Index {i}: {key[:10]}...{key[-4:]} ---")
    for model in MODELS:
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model=model,
                contents="hello"
            )
            print(f"  [SUCCESS] {model}: {response.text.strip()}")
        except Exception as e:
            err_msg = str(e)
            if "RESOURCE_EXHAUSTED" in err_msg:
                print(f"  [FAIL] {model}: RESOURCE_EXHAUSTED")
            else:
                print(f"  [FAIL] {model}: {err_msg[:100]}")
