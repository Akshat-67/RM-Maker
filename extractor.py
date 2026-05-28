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
            s = str(amount_str).upper()
            s = re.sub(r'RS\.', '', s)
            s = re.sub(r'RS', '', s)
            s = s.replace(',', '')
            match = re.search(r'(\d+\.?\d*)', s)
            if not match: return ""

            clean_str = match.group(1)
            amount = float(clean_str)
            main_val = int(amount)
            fraction = int(round((amount - main_val) * 100))

            words = num2words(main_val, lang='en_IN')
            result = f"Rupees {words}"
            if fraction > 0:
                fraction_words = num2words(fraction, lang='en_IN')
                result += f" and {fraction_words} Paise"

            final = f"{result} Only"
            final = final.replace("  ", " ").strip().title()
            return final
        except Exception as e:
            print(f"Error converting amount to words: {e}")
            return ""

    def get_available_models(self):
        if not self.client: return []
        try:
            models = self.client.models.list()
            return [m.name for m in models if 'generateContent' in m.supported_actions]
        except Exception:
            return []

    def raw_generate(self, prompt, model_name):
        if not self.client: return None
        try:
            # Strip "models/" prefix if present (new SDK returns full names like "models/gemini-2.5-flash")
            clean_name = model_name.replace("models/", "", 1) if model_name else model_name
            response = self.client.models.generate_content(model=clean_name, contents=prompt)
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
        # ds_text: the complete title chain / first schedule as a single text block
        # This replaces the old ds[] list to handle variable numbers of documents.
        # If the AI returns ds as a list (backward compatible), join it into text.
        # If it returns ds_text directly (new format), use that.
        if "ds_text" in data:
            raw_ds_text = data["ds_text"]
            if isinstance(raw_ds_text, list):
                data["ds_text"] = "\n".join([str(x.get("t","") if isinstance(x,dict) else x).strip() for x in raw_ds_text if x])
            else:
                data["ds_text"] = str(raw_ds_text).strip() if raw_ds_text else ""
        else:
            raw_ds = data.get("ds", None)
            if isinstance(raw_ds, list):
                lines = []
                for item in raw_ds:
                    t = item.get("t", "") if isinstance(item, dict) else str(item)
                    if t.strip():
                        lines.append(t.strip())
                data["ds_text"] = "\n".join(lines)
            elif isinstance(raw_ds, str) and raw_ds.strip():
                data["ds_text"] = raw_ds.strip()
            else:
                data["ds_text"] = ""

        # second_schedule: the complete "Documents to be collected" section from legal report
        data["second_schedule"] = "" if data.get("second_schedule") is None else str(data.get("second_schedule", "")).strip()

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
          "ds_text": "COMPLETE FIRST SCHEDULE / TITLE CHAIN as a single text block. See rule 8 below.",
          "second_schedule": "COMPLETE 'Documents to be collected' section from the legal scrutiny report. See rule 9 below."
        }

        STRICT EXTRACTION RULES:
        1. ZERO HALLUCINATION: If a field is not found, use "".
        2. COUNT CONTROL:
           - Return exactly the selected borrower count in "bs".
           - Return exactly the selected loan account count in "ls".
           - Return exactly 2 witnesses in "ws".
        3. PROPERTY BOUNDARIES: Extract 'North', 'South', 'East', 'West' exactly from the property schedule.
        4. DATES: Extract dates exactly as they appear (e.g., "this 24th day of March 2024").
        5. ROLE SEPARATION IS MANDATORY: Borrowers in "bs", witnesses in "ws", bank signatory in "bsign".
        6. NAME ACCURACY: Extract the full person name exactly.
        7. BORROWER SOURCE PRIORITY: Legal report > sale deed > loan application.
        8. FIRST SCHEDULE (ds_text): Extract ALL title deeds / documents from the FIRST SCHEDULE
           as ONE SINGLE TEXT BLOCK into "ds_text". Join each document description with a newline.
           Do NOT use ds[] list format. Just one string. This handles any number of documents.
        9. SECOND SCHEDULE — CRITICAL: Look for these exact or similar headings in the legal scrutiny report:
           - "Documents to be collected by {Bank Name} at the time of disbursement as per Annexure-II"
           - "Following documents needs to be submitted at the time of disbursement"
           - "Documents required post disbursal" (if any)
           Under this section, find ALL bullet points / items that START WITH the word "Original"
           (e.g. "Original Sale Deed", "Original Title Deed", "Original Allotment Letter", etc.).
           COPY the ENTIRE block of "Original" items as a single continuous text into "second_schedule".
           Preserve the exact wording, line breaks, and formatting as in the document.
           DO NOT extract individual placeholders for each item — it is one single block.
           If the bank is ICICI and the sale deed is pending/unexecuted, still extract the Original items
           that are listed as required.
           If "second_schedule" section is not found, return "".
        """

        try:
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