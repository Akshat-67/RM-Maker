import re
import google.generativeai as genai
from num2words import num2words
import json
import os
from PIL import Image

class DataExtractor:
    def __init__(self, api_key=None):
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def amount_to_words(self, amount_str):
        try:
            clean_str = re.sub(r'[^\d.]', '', amount_str)
            amount = float(clean_str)
            return num2words(amount, lang='en_IN', to='currency').replace('euro', 'Rupees').replace('cents', 'Paise')
        except:
            return ""

    def extract_with_ai(self, file_paths):
        if not self.model:
            return {"error": "AI model not configured."}

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
            {"n": "LAN No", "a": "Amount", "w": "Amount in words"}
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
                return {"error": "Invalid AI response", "raw": response.text}
        except Exception as e:
            return {"error": str(e)}
