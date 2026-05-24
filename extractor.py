import re
from google import genai
from num2words import num2words
import json
import os

class DataExtractor:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            self.client = genai.Client(api_key=api_key)

    def amount_to_words(self, amount_str):
        try:
            clean_str = re.sub(r'[^\d.]', '', str(amount_str))
            if not clean_str: return ""
            amount = float(clean_str)

            main_val = int(amount)
            fraction = round((amount - main_val) * 100)

            words = num2words(main_val, lang='en_IN')
            words = words.replace('thousand', 'Thousand').replace('lakh', 'Lakh').replace('crore', 'Crore')

            result = f"Rupees {words}"
            if fraction > 0:
                fraction_words = num2words(fraction, lang='en_IN')
                result += f" and {fraction_words} Paise"

            return f"{result} Only".title().replace("  ", " ")
        except Exception as e:
            print(f"Error converting amount to words: {e}")
            return ""

    def get_available_models(self):
        """Returns a list of models using the new genai client."""
        if not self.client: return []
        try:
            # Listing models in the new SDK
            models = self.client.models.list()
            # The new SDK uses 'supported_actions'
            return [m.name for m in models if 'generateContent' in m.supported_actions]
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

        from google.genai import types
        import mimetypes

        contents = []
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            mime_type, _ = mimetypes.guess_type(path)

            if ext in ['.jpg', '.jpeg', '.png', '.pdf']:
                with open(path, 'rb') as f:
                    data = f.read()
                contents.append(types.Part.from_bytes(data=data, mime_type=mime_type or 'application/octet-stream'))
            elif ext == '.txt':
                with open(path, 'r', encoding='utf-8') as f:
                    contents.append(types.Part.from_text(text=f.read()))

        prompt = """
        CRITICAL TASK: Extract EXACT data from the provided legal documents.
        Return ONLY a JSON object. NO conversational text.

        STRUCTURE:
        {
          "rd": "RM Execution Date (character-perfect, e.g. 10th May 2024)",
          "ad": "Loan Agreement Date",
          "bs": [
            {
              "s": "Mr./Ms.", "n": "Full Name", "a": "Age",
              "r": "Relation (S/o, W/o)", "rn": "Relative Name",
              "adr": "Address", "id": "Aadhar/ID"
            }
          ],
          "ls": [
            {"n": "LAN No", "a": "Amount Figures", "w": "Amount Words", "t": "Tenure"}
          ],
          "ps": [
            {"adr": "Address", "n": "North", "s": "South", "e": "East", "w": "West"}
          ],
          "bsign": {"n": "Bank Signatory", "r": "Rel", "rn": "Rel Name"},
          "ws": [
            {"n": "Name", "r": "Rel", "rn": "Rel Name", "adr": "Address"}
          ],
          "ds": [
            {"t": "Document Description"}
          ]
        }

        RULES:
        1. Accuracy is 100% required. Do not guess.
        2. If multiple borrowers or loans, include all.
        3. For 'ds', list title deeds mentioned in LSR.
        4. Leave empty strings for missing data.
        """

        try:
            # New SDK generate_content syntax
            # Note: contents and prompt are joined
            # Ensuring prompt is the last Part for context
            final_contents = contents + [types.Part.from_text(text=prompt)]

            response = self.client.models.generate_content(
                model=selected_model,
                contents=final_contents
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
