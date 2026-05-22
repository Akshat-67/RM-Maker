import re
import google.generativeai as genai
from num2words import num2words
import json

class DataExtractor:
    def __init__(self, api_key=None):
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def extract_with_regex(self, text):
        data = {}

        # Aadhar Number (XXXX XXXX XXXX or XXXXXXXXXXXX)
        aadhar_match = re.search(r'\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b', text)
        if aadhar_match:
            data['aadhar_no'] = aadhar_match.group(0)

        # Dates (DD/MM/YYYY or DD-MM-YYYY)
        date_matches = re.findall(r'\b\d{2}/\d{2}/\d{4}\b|\b\d{2}-\d{2}-\d{4}\b', text)
        if date_matches:
            data['dates'] = date_matches

        # PAN Number (Simplified)
        pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', text)
        if pan_match:
            data['pan_no'] = pan_match.group(0)

        return data

    def amount_to_words(self, amount_str):
        try:
            # Remove commas and currency symbols
            amount = float(re.sub(r'[^\d.]', '', amount_str))
            return num2words(amount, lang='en_IN', to='currency').replace('euro', 'Rupees').replace('cents', 'Paise')
        except:
            return ""

    def extract_with_ai(self, all_text_content):
        if not self.model:
            # Basic fallback extraction if no AI
            basic_data = self.extract_with_regex(all_text_content)
            return {
                "Borrowers": [{"name": "Check OCR File", "age": "", "father_or_husband_name": "", "address": ""}],
                "Loan Details": {
                    "loan_account_no": basic_data.get('pan_no', ''),
                    "loan_amount": "0",
                    "sanction_date": basic_data.get('dates', [''])[0]
                },
                "Documents List": ["Please paste documents from LSR here"]
            }

        prompt = f"""
        Extract the following information from the OCR text provided below.
        Return ONLY a JSON object.

        Fields to extract:
        1. Borrowers: List of objects containing (name, age, father_or_husband_name, address).
        2. Loan Details: (loan_account_no, loan_amount, sanction_date, tenure_months).
        3. Property Details: (address, area, unit_no, floor).
        4. Documents List: A list of all legal documents mentioned in the LSR or Sanction letter with their dates and registration details. This is for the "Second Schedule" of a mortgage deed.

        OCR TEXT:
        {all_text_content}
        """

        try:
            response = self.model.generate_content(prompt)
            # Attempt to find JSON in response
            json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group(0)
            return json.loads(json_str)
        except Exception as e:
            return {"error": f"Failed to parse AI response: {str(e)}", "raw": getattr(response, 'text', 'No response')}

if __name__ == "__main__":
    # Test logic
    pass
