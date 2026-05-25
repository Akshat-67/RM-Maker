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
            # 1. Remove common currency prefixes that might contain dots (e.g., "Rs.", "R.S.")
            s = str(amount_str).upper()
            s = re.sub(r'RS\.', '', s)
            s = re.sub(r'RS', '', s)

            # 2. Extract the numeric part (allowing for commas and one decimal point)
            # Remove commas first
            s = s.replace(',', '')
            # Find the first sequence of digits and dots
            match = re.search(r'(\d+\.?\d*)', s)
            if not match: return ""

            clean_str = match.group(1)
            amount = float(clean_str)
            main_val = int(amount)
            # Use decimal for precision to avoid floating point issues
            fraction = int(round((amount - main_val) * 100))

            words = num2words(main_val, lang='en_IN')

            # num2words with en_IN handles lakh/crore, but we want consistent Title Case
            result = f"Rupees {words}"
            if fraction > 0:
                fraction_words = num2words(fraction, lang='en_IN')
                result += f" and {fraction_words} Paise"

            # Cleanup and ensure "Only" at the end
            final = f"{result} Only"
            # Standardize capitalization for legal documents
            final = final.replace("  ", " ").strip().title()

            # Post-processing: "Rupees" and "Paise" should be capitalized correctly if .title() messed them up
            # (Though .title() usually works fine for these)
            return final
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
        CRITICAL TASK: Extract EXACT data from the provided legal documents for Registered Mortgage (RM) generation.
        Return ONLY a valid JSON object. Do not include any markdown formatting or conversational text.

        JSON STRUCTURE:
        {
          "rd": "RM Execution Date (Exact phrase from document, e.g., '10th day of May 2024')",
          "ad": "Loan Agreement Date (e.g., '15.04.2024')",
          "bs": [
            {
              "s": "Salutation (Mr./Ms./Mrs.)",
              "n": "Full Name",
              "a": "Age",
              "r": "Relationship type (S/o, W/o, D/o)",
              "rn": "Relative's Name",
              "adr": "Full Residential Address",
              "id": "Aadhar Number or ID"
            }
          ],
          "ls": [
            {
              "n": "Loan Account Number (LAN)",
              "a": "Loan Amount in Figures (e.g., 15,00,000)",
              "w": "Loan Amount in Words",
              "t": "Tenure (e.g., 180 Months)"
            }
          ],
          "ps": [
            {
              "adr": "Full Property Address as per Schedule",
              "n": "North Boundary",
              "s": "South Boundary",
              "e": "East Boundary",
              "w": "West Boundary"
            }
          ],
          "bsign": {
            "n": "Bank Signatory Name",
            "r": "Signatory Relation (if any)",
            "rn": "Signatory Relative Name (if any)"
          },
          "ws": [
            {
              "n": "Witness Name",
              "r": "Relation",
              "rn": "Relative Name",
              "adr": "Witness Address"
            }
          ],
          "ds": [
            {
              "t": "Detailed description of title deeds/documents from the List of Documents/Schedule"
            }
          ]
        }

        STRICT EXTRACTION RULES:
        1. ZERO HALLUCINATION: If a field is not found, use "".
        2. FULL ENTITY CAPTURE: If there are 2 borrowers, "bs" must have 2 objects. Same for "ls", "ps", "ws", and "ds".
        3. PROPERTY BOUNDARIES: Extract 'North', 'South', 'East', 'West' exactly from the property schedule.
        4. DOCUMENT SCHEDULE (ds): This is crucial. Extract the full description of each document mentioned in the title deed list.
        5. DATES: Extract dates exactly as they appear (e.g., "this 24th day of March 2024").
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
