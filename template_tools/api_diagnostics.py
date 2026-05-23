import google.generativeai as genai
import sys

def run_diagnostics(api_key):
    print(f"--- LegalDoc API Diagnostics ---")
    print(f"Testing Key: {api_key[:5]}...{api_key[-4:]}")

    try:
        genai.configure(api_key=api_key)
        print("\n1. Listing Available Models:")
        models = genai.list_models()
        count = 0
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"  [OK] {m.name}")
                count += 1
        if count == 0:
            print("  [!!] No models found that support generateContent.")

        print("\n2. Simple Connectivity Test (Gemini 1.5 Flash):")
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content("Hello, respond with 'Connected'")
            print(f"  [OK] Response: {res.text.strip()}")
        except Exception as e:
            print(f"  [FAIL] gemini-1.5-flash failed: {str(e)}")

        print("\n3. Testing Beta vs v1 (Metadata check):")
        # genai SDK currently hides endpoint details, but checking model names gives a hint.
        print("  SDK Version:", genai.__version__ if hasattr(genai, '__version__') else "unknown")

    except Exception as e:
        print(f"\n[FATAL ERROR] API connection failed: {str(e)}")
        print("\nPossible Solutions:")
        print("- Check if 'Generative Language API' is enabled in Google Cloud Console.")
        print("- Ensure your project is linked to a billing account (even for free tier).")
        print("- Check for internet restrictions or proxies.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_diagnostics(sys.argv[1])
    else:
        print("Usage: python api_diagnostics.py YOUR_API_KEY")
