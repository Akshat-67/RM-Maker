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

    def _normalize_person(self, value, fields):
        if not isinstance(value, dict):
            return {field: "" for field in fields}
        cleaned = {}
        for field in fields:
            item = value.get(field, "")
            cleaned[field] = "" if item is None else str(item).strip()
        return cleaned

    def _normalize_list(self, data, key, fields):
        values = data.get(key, [])
        if isinstance(values, dict):
            values = [values]
        if not isinstance(values, list):
            values = []
        normalized = [self._normalize_person(item, fields) for item in values]
        data[key] = [item for item in normalized if any(item.values())]

    def _hint_names(self, hints):
        if not hints:
            return []
        names = []
        for line in re.split(r"[\n,;]+", hints):
            name = line.strip().casefold()
            if name:
                names.append(name)
        return names

    def _matches_hint(self, person, hint_names):
        if not hint_names:
            return False
        name = person.get("n", "").casefold()
        return any(hint in name or name in hint for hint in hint_names if name)

    def _apply_person_hints(self, data, borrower_hints="", witness_hints=""):
        borrower_names = self._hint_names(borrower_hints)
        witness_names = self._hint_names(witness_hints)

        if borrower_names:
            preferred = [b for b in data["bs"] if self._matches_hint(b, borrower_names)]
            remaining = [b for b in data["bs"] if not self._matches_hint(b, borrower_names)]
            data["bs"] = preferred + remaining

        if witness_names:
            preferred = [w for w in data["ws"] if self._matches_hint(w, witness_names)]
            remaining = [w for w in data["ws"] if not self._matches_hint(w, witness_names)]
            data["ws"] = preferred + remaining

        if borrower_names and witness_names:
            data["bs"] = [b for b in data["bs"] if not self._matches_hint(b, witness_names)]
            data["ws"] = [w for w in data["ws"] if not self._matches_hint(w, borrower_names)]

    def _force_count(self, data, key, fields, expected_count):
        if expected_count is None:
            return
        values = data.get(key, [])
        data[key] = values[:expected_count]
        while len(data[key]) < expected_count:
            data[key].append({field: "" for field in fields})

    def _normalize_response(self, data, expected_borrowers=None, expected_loans=None, expected_witnesses=2, borrower_hints="", witness_hints=""):
        if not isinstance(data, dict):
            return {"error": "AI returned JSON, but it was not an object"}

        for key in ["rd", "ad"]:
            data[key] = "" if data.get(key) is None else str(data.get(key, "")).strip()

        self._normalize_list(data, "bs", ["s", "n", "a", "r", "rn", "adr", "id"])
        self._normalize_list(data, "ls", ["n", "a", "w", "t"])
        self._normalize_list(data, "ps", ["adr", "n", "s", "e", "w"])
        self._normalize_list(data, "ws", ["n", "r", "rn", "adr"])
        self._normalize_list(data, "ds", ["t"])

        bsign = data.get("bsign", {})
        data["bsign"] = self._normalize_person(bsign, ["n", "r", "rn"])

        self._apply_person_hints(data, borrower_hints, witness_hints)

        witness_names = {w["n"].casefold() for w in data["ws"] if w.get("n")}
        data["bs"] = [
            b for b in data["bs"]
            if not (b.get("n", "").casefold() in witness_names and not b.get("id"))
        ]

        self._force_count(data, "bs", ["s", "n", "a", "r", "rn", "adr", "id"], expected_borrowers)
        self._force_count(data, "ls", ["n", "a", "w", "t"], expected_loans)
        self._force_count(data, "ws", ["n", "r", "rn", "adr"], expected_witnesses)

        for loan in data.get("ls", []):
            if not loan.get("w") or loan["w"].casefold() in {"amount in words", "not found"}:
                loan["w"] = self.amount_to_words(str(loan.get("a", "0")))

        return data

    def extract_with_ai(self, file_paths, selected_model, bank_name="", expected_borrowers=None, expected_loans=None, expected_witnesses=2, borrower_hints="", witness_hints=""):
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

        count_instruction = f"""
        USER SELECTED CASE SETTINGS:
        - Selected bank: {bank_name or "not selected"}
        - Expected borrower count: {expected_borrowers if expected_borrowers is not None else "extract all true borrowers"}
        - Expected loan account count: {expected_loans if expected_loans is not None else "extract all true loan accounts"}
        - Expected witness count: {expected_witnesses}
        - User-confirmed borrower names/hints: {borrower_hints.strip() or "none provided"}
        - User-confirmed witness names/hints: {witness_hints.strip() or "none provided"}
        """

        prompt = """
        CRITICAL TASK: Extract EXACT data from the provided legal documents for Registered Mortgage (RM) generation.
        Return ONLY a valid JSON object. Do not include any markdown formatting or conversational text.
        """ + count_instruction + """

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
        2. COUNT CONTROL:
           - Return exactly the selected borrower count in "bs".
           - Return exactly the selected loan account count in "ls". If 2 Loan Accounts is selected, return 2 loan objects from the two sanction/KFS/loan letters. If one is not found, include a blank object for review.
           - Return exactly 2 witnesses in "ws". If one witness is not found, include a blank second witness object.
           - If user-confirmed borrower/witness hints are provided, use those names over guesses from signatures.
        3. PROPERTY BOUNDARIES: Extract 'North', 'South', 'East', 'West' exactly from the property schedule.
        4. DOCUMENT SCHEDULE (ds): This is crucial. Extract the full description of each document mentioned in the title deed list.
        5. DATES: Extract dates exactly as they appear (e.g., "this 24th day of March 2024").
        6. ROLE SEPARATION IS MANDATORY:
           - "bs" is only for the borrower/mortgagor/property owner.
           - The legal report is the highest priority source for borrower ownership.
           - If sale deed is not executed, use the legal report's "proposed owner"/"proposed purchaser" as borrower.
           - If sale deed/title is already done, use the latest title chain/current owner as borrower.
           - Do not use random signature names, witnesses, identifiers, deed writers, advocates, neighbors, or bank staff as borrowers.
           - "ws" is only for witnesses from witness/signature witness sections.
           - "bsign" is only the bank/authorized officer/signatory.
           - For "bsign.r" and "bsign.rn", extract the authorized signatory's relation marker and father/husband/relative name from text near the authorized signatory name (for example S/o, W/o, D/o and the name after it).
           - Never copy a witness name into "bs". If a person appears near the word "Witness", put them only in "ws".
           - Never copy the bank signatory into "bs" or "ws".
        7. NAME ACCURACY: Extract the full person name exactly. Do not swap a relative's name or witness name into the borrower name field.
        8. BORROWER SOURCE PRIORITY:
           A. Legal report proposed owner/proposed purchaser/current owner/title holder.
           B. Latest sale deed or title chain owner.
           C. Loan/KFS applicant only if it agrees with the ownership documents or legal report.
           D. Never choose witness/signatory names as fallback borrowers.
        9. DOCUMENT SCHEDULE / TITLE CHAIN RULES:
           - Look for legal scrutiny report headings like "Following documents needs to be submitted at the time of disbursement of the loan" and "Following documents are required post disbursal: (if any)".
           - If selected bank is ICICI, use only the last title document chain from the legal scrutiny report. If the sale deed is still to be executed/submitted before the RM, leave ds blank rather than using a pending sale deed as a completed title document.
           - If selected bank is not ICICI, copy the complete title chain under those legal scrutiny report headings exactly as written.
           - Preserve title document wording as-is in ds[].t. Do not summarize.
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
                return self._normalize_response(data, expected_borrowers, expected_loans, expected_witnesses, borrower_hints, witness_hints)
            return {"error": "AI returned non-JSON response", "raw": response.text}

        except Exception as e:
            return {"error": f"AI Error: {str(e)}"}
