import os
import time
from google import genai

key = os.getenv("GEMINI_API_KEY_1")
client = genai.Client(api_key=key)

print("Attempting to connect to gemini-flash-latest with retries...")
for attempt in range(5):
    try:
        print(f"Attempt {attempt+1}/5...")
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents="hello"
        )
        print(f"[SUCCESS] Response: {response.text.strip()}")
        break
    except Exception as e:
        print(f"[FAIL] {e}")
        if "503" in str(e):
            print("Server overloaded, waiting 5 seconds before retrying...")
            time.sleep(5)
        else:
            break
