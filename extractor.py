import re
from google import genai
from num2words import num2words
import json
import os
from PIL import Image

class DataExtractor:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            self.client = genai.Client(api_key=api_key)

    def amount_to_words(self, amount_str):
        try:
            clean_str = re.sub(r'[^\d.]', '', amount_str)
            amount = float(clean_str)
            return num2words(amount, lang='en_IN', to='currency').replace('euro', 'Rupees').replace('cents', 'Paise')
        except:
            return ""

    def get_available_models(self):
        """Returns a list of models using the new genai client."""
        if not self.client: return []
        try:
            # Listing models in the new SDK
            models = self.client.models.list()
            return [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        except Exception:
            return []

    def raw_generate(self, prompt, model_name):
        if not self.client: return None
        try:
            response = self.client.models.generate_content(model=model_name, contents=prompt)
            return response.text
        except Exception as e:
            print(f"Extraction Error: {e}")
            return None

    def extract_with_ai(self, file_paths, selected_model):
        if not self.client:
            return {"error": "API Key Missing"}

        contents = []
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                contents.append(Image.open(path))
            elif ext == '.pdf':
                # New SDK handles PDF bytes directly
                with open(path, "rb") as f:
                    pdf_data = f.read()
                contents.append({
                    "mime_type": "application/pdf",
                    "data": pdf_data
                })
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

        try:
            # New SDK generate_content syntax
            # Note: contents and prompt are joined
            final_content = contents + [prompt]
            response = self.client.models.generate_content(
                model=selected_model,
                contents=final_content
            )

            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                # Data cleanup for loan amounts
                for loan in data.get('ls', []):
                    if not loan.get('w') or loan['w'] == "Amount in words":
                        loan['w'] = self.amount_to_words(str(loan.get('a', '0')))
                return data
            return {"error": "AI returned non-JSON response", "raw": response.text}

        except Exception as e:
            return {"error": f"AI Error: {str(e)}"}
