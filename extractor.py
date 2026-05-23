import re
import google.generativeai as genai
from num2words import num2words
import json
import os
from PIL import Image

class DataExtractor:
    def __init__(self, api_key=None):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)

    def amount_to_words(self, amount_str):
        try:
            clean_str = re.sub(r'[^\d.]', '', amount_str)
            amount = float(clean_str)
            return num2words(amount, lang='en_IN', to='currency').replace('euro', 'Rupees').replace('cents', 'Paise')
        except:
            return ""

    def get_available_models(self):
        """Discovers which models this specific API key is allowed to use."""
        try:
            # Attempt to list models. This itself might fail if key is bad.
            models = genai.list_models()
            return [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        except Exception:
            return []

    def extract_with_ai(self, file_paths):
        if not self.api_key:
            return {"error": "API Key Missing"}

        # Discovery phase
        available = self.get_available_models()

        # Priority list
        target_models = [
            'models/gemini-1.5-flash-latest',
            'models/gemini-1.5-flash',
            'models/gemini-2.0-flash-exp',
            'models/gemini-1.5-flash-8b',
            'models/gemini-pro'
        ]

        selected_model = None
        for target in target_models:
            if target in available:
                selected_model = target
                break

        if not selected_model:
            if available:
                selected_model = available[0] # Take the first one available
            else:
                # Last ditch effort if listing failed
                selected_model = 'models/gemini-1.5-flash'

        contents = []
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                contents.append(Image.open(path))
            elif ext == '.pdf':
                with open(path, "rb") as f:
                    contents.append({"mime_type": "application/pdf", "data": f.read()})
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
            model = genai.GenerativeModel(selected_model)
            response = model.generate_content(contents)
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                # Ensure amounts are converted
                for loan in data.get('ls', []):
                    if not loan.get('w'): loan['w'] = self.amount_to_words(loan.get('a', '0'))
                return data
            return {"error": "AI returned non-JSON response", "raw": response.text}

        except Exception as e:
            err = str(e)
            if "404" in err:
                return {"error": f"Model '{selected_model}' failed with 404. This API key may not have access to Flash. Found: {available}"}
            if "429" in err:
                return {"error": "Quota full. Wait 60s."}
            return {"error": f"AI Error: {err}"}
