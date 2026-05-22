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
            # Handle potential currency symbols and commas
            clean_str = re.sub(r'[^\d.]', '', amount_str)
            amount = float(clean_str)
            # Use Indian English for Rupees/Lakhs
            return num2words(amount, lang='en_IN', to='currency').replace('euro', 'Rupees').replace('cents', 'Paise')
        except:
            return "Zero Rupees"

    def extract_with_ai(self, file_paths):
        """
        file_paths: List of paths to .txt, .jpg, .png, or .pdf files.
        We send them all in one single call to save requests.
        """
        if not self.model:
            return {"error": "AI model not configured. Please enter a Gemini API Key."}

        contents = []

        # Prepare the files for Gemini
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                img = Image.open(path)
                contents.append(img)
            elif ext == '.pdf':
                # Gemini 1.5 Flash supports PDF directly via API
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
        You are a legal document assistant. Analyze the provided documents (images, PDFs, and text)
        which include Aadhar cards, sanction letters, and Legal Scrutiny Reports (LSR).

        Extract the following information accurately. Even if the images are blurry, use your reasoning
        to identify the key legal details.

        Return ONLY a JSON object with this structure:
        {
          "Borrowers": [
            {"name": "...", "age": "...", "father_or_husband_name": "...", "address": "..."}
          ],
          "Loan Details": {
            "loan_account_no": "...",
            "loan_amount": "...",
            "sanction_date": "...",
            "tenure_months": "..."
          },
          "Documents List": [
             "List every legal document mentioned in the LSR or Sanction Letter for the 'Second Schedule'.
              Include the date, registration number (R.S. No), Book No, Vol No, and Page numbers for each."
          ]
        }

        OCR and extraction should be precise. If multiple borrowers exist, list them all.
        """

        contents.append(prompt)

        try:
            response = self.model.generate_content(contents)
            # Attempt to find JSON in response
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            else:
                return {"error": "AI did not return a valid JSON object.", "raw": response.text}
        except Exception as e:
            return {"error": f"Failed to process documents: {str(e)}"}

if __name__ == "__main__":
    pass
