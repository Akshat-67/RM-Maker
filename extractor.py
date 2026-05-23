import re
import google.generativeai as genai
from num2words import num2words
import json
import os
from PIL import Image

class DataExtractor:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.model = None
        if api_key:
            genai.configure(api_key=api_key)
            # We will initialize the model dynamically in extract_with_ai
            # to allow for fallback logic.

    def amount_to_words(self, amount_str):
        try:
            clean_str = re.sub(r'[^\d.]', '', amount_str)
            amount = float(clean_str)
            return num2words(amount, lang='en_IN', to='currency').replace('euro', 'Rupees').replace('cents', 'Paise')
        except:
            return ""

    def get_best_model(self):
        """Attempts to find an available Flash model using the provided API key."""
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Preference order
            preferences = [
                'models/gemini-1.5-flash-latest',
                'models/gemini-1.5-flash',
                'models/gemini-flash-latest'
            ]
            for pref in preferences:
                if pref in available_models:
                    return pref
            # Fallback to anything with 'flash' in it
            for m in available_models:
                if 'flash' in m.lower():
                    return m
            return 'models/gemini-1.5-flash' # Absolute fallback
        except Exception:
            return 'models/gemini-1.5-flash-latest'

    def extract_with_ai(self, file_paths):
        if not self.api_key:
            return {"error": "AI model not configured. Please enter a Gemini API Key."}

        # Dynamically select the best model name to avoid 404
        model_name = self.get_best_model()
        self.model = genai.GenerativeModel(model_name)

        contents = []
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                contents.append(Image.open(path))
            elif ext == '.pdf':
                with open(path, "rb") as f:
                    pdf_data = f.read()
                contents.append({"mime_type": "application/pdf", "data": pdf_data})
            elif ext == '.txt':
                with open(path, 'r', encoding='utf-8') as f:
                    contents.append(f.read())

        prompt = """
        Analyze these legal documents. Return ONLY a JSON object with this structure:
        {
          "rd": "RM Date",
          "ad": "Loan Agreement Date",
          "bs": [
            {"s": "Mr./Mrs.", "n": "Name", "a": "Age", "r": "S/o, W/o", "rn": "Relative Name", "adr": "Address"}
          ],
          "ls": [
            {"n": "LAN No", "a": "Amount", "w": "Amount in words", "t": "Tenure"}
          ],
          "ps": [
            {"adr": "Prop Address", "n": "North", "s": "South", "e": "East", "w": "West"}
          ],
          "bsign": {"n": "Bank Signatory", "r": "S/o", "rn": "Father Name"},
          "ws": [
            {"n": "Name", "r": "S/o", "rn": "Relative", "adr": "Address"}
          ],
          "ds": [
            {"t": "Document description from LSR"}
          ]
        }
        """

        contents.append(prompt)

        try:
            response = self.model.generate_content(contents)
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                for loan in data.get('ls', []):
                    if not loan.get('w'):
                        loan['w'] = self.amount_to_words(loan.get('a', '0'))
                return data
            else:
                return {"error": "Invalid AI response. The AI didn't return a valid JSON.", "raw": response.text}
        except Exception as e:
            err_msg = str(e)
            if "404" in err_msg:
                return {"error": f"Model '{model_name}' not found (404). This usually means the model name is incorrect or the API version is deprecated. Try a different API key or check Google Cloud settings."}
            if "403" in err_msg:
                return {"error": "Permission Denied (403). Ensure your API Key is valid and 'Generative Language API' is enabled in your Google Cloud project."}
            if "429" in err_msg:
                return {"error": "Rate Limit Exceeded (429). Please wait a few seconds before trying again."}
            if "billing" in err_msg.lower():
                return {"error": "Billing Issue. Your Google Cloud project may need an active billing account even for the free tier."}
            return {"error": f"AI System Error: {err_msg}"}
