from google import genai
import sys

def run_diagnostics(api_key):
    print(f"--- LegalDoc API Diagnostics (New SDK) ---")
    print(f"Testing Key: {api_key[:5]}...{api_key[-4:]}")

    try:
        client = genai.Client(api_key=api_key)

        print("\n1. Listing Available Models:")
        models = client.models.list()
        count = 0
        for m in models:
            if 'generateContent' in m.supported_actions:
                print(f"  [OK] {m.name}")
                count += 1
        if count == 0:
            print("  [!!] No models found that support generateContent.")

        print("\n2. Simple Connectivity Test (gemini-1.5-flash):")
        try:
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents="Hello, respond with 'Connected'"
            )
            print(f"  [OK] Response: {response.text.strip()}")
        except Exception as e:
            print(f"  [FAIL] gemini-1.5-flash failed: {str(e)}")

        print("\n3. Testing Connectivity (gemini-1.5-pro):")
        try:
            response = client.models.generate_content(
                model='gemini-1.5-pro',
                contents="Hello, respond with 'Connected'"
            )
            print(f"  [OK] Response: {response.text.strip()}")
        except Exception as e:
            print(f"  [FAIL] gemini-1.5-pro failed: {str(e)}")

    except Exception as e:
        print(f"\n[FATAL ERROR] API connection failed: {str(e)}")
        print("\nPossible Solutions:")
        print("- Check if your API key is valid.")
        print("- Check for internet restrictions or proxies.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_diagnostics(sys.argv[1])
    else:
        print("Usage: python api_diagnostics.py YOUR_API_KEY")
