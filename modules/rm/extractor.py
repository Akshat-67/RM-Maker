import re
import os
import base64
import mimetypes
import json
from utils.config import get_nvidia_api_key
from google import genai
from google.genai import types
from google.genai.errors import APIError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from utils.helpers import (
    amount_to_words,
    format_indian_currency,
    format_date_with_dots,
    clean_aadhar_address,
    normalize_name_salutation,
    parse_relation_text,
    normalize_relation_prefix,
    parse_and_format_chain,
    convert_hindi_digits_to_english
)

from services.ai_client import AIClient

class RMDataExtractor:
    def __init__(self, api_key=None, api_keys=None, provider="gemini", *args, **kwargs):
        self.provider = "gemini"
        if api_keys:
            self.api_keys = api_keys
        elif api_key:
            self.api_keys = [api_key]
        else:
            self.api_keys = []
        self.ai_client = AIClient(api_keys=self.api_keys)

    @property
    def client(self):
        return self.ai_client.client

    @property
    def active_key_index(self):
        return self.ai_client.active_key_index

    def _init_client(self):
        if hasattr(self, 'ai_client'):
            self.ai_client._init_client()

    def _rotate_key(self):
        if hasattr(self, 'ai_client'):
            return self.ai_client._rotate_key()
        return False

    def get_available_models(self):
        return self.ai_client.list_models()

    def generate_full_property_address(self, prop, property_type="Plot"):
        """Compiles components into a formal address string for RM."""
        if not isinstance(prop, dict): return ""
        components = []
        order = ["plot_no", "scheme", "ward", "village", "tehsil", "dist", "state"]
        for key in order:
            val = str(prop.get(key, "")).strip()
            if val and val.lower() not in ["none", "null", "na", "-"]:
                if key == "plot_no" and not val.lower().startswith(("plot", "p-no", "p.", "flat", "f-no", "f.", "unit", "u-no")):
                    if property_type == "Flat":
                        components.append(f"Flat No. {val}")
                    else:
                        components.append(f"Plot No. {val}")
                elif key == "tehsil" and not val.lower().startswith("tehsil"):
                    components.append(f"Tehsil {val}")
                elif key == "dist" and not val.lower().startswith("dist"):
                    components.append(f"District {val}")
                else:
                    components.append(val)
        res = ", ".join(components)
        pattern = r'^(आवासीय|vkoklh;|Residential)\s*[-–—:]*\s*'
        res = re.sub(pattern, '', res, flags=re.IGNORECASE).strip()
        return res

    def extract_buckets_with_ai(self, buckets, selected_model, expected_borrowers=None, expected_loans=None,
                                expected_witnesses=2, borrower_hints="", witness_hints="",
                                current_data=None, **kwargs):
        """Process each RM document bucket independently to ensure strict source isolation."""
        if not self.api_keys:
            return {"error": "Gemini API Keys Missing"}

        target_bucket = kwargs.get("target_bucket")
        merged_data = current_data or {}
        session_extractions = {}
        session_confidence = {}

        # 1. KYC - Extract Aadhaar/PAN ONLY from 'kyc' files
        if buckets.get("kyc") and len(buckets["kyc"]) > 0 and (not target_bucket or target_bucket == "kyc"):
            kyc_prompt = self._build_kyc_prompt(expected_borrowers, expected_witnesses)
            kyc_res = self._run_gemini_extraction(buckets["kyc"], selected_model, kyc_prompt)
            if kyc_res and not kyc_res.get("error"):
                merged_data["unassigned_aadhars"] = kyc_res.get("unassigned_aadhars", [])
                if "extractions" in kyc_res:
                    session_extractions.update(kyc_res["extractions"])
                if "confidence_scores" in kyc_res:
                    session_confidence.update(kyc_res["confidence_scores"])

        # 2. Case Info (Legal/ATS/OCR) - Extract metadata from non-KYC documents
        case_files = []
        for b_name in ["legal", "ats", "ocr"]:
            if buckets.get(b_name):
                case_files.extend(buckets[b_name])
                
        if case_files and (not target_bucket or target_bucket in ("legal", "ats", "ocr")):
            # Extract everything except unassigned_aadhars
            case_prompt = self._build_case_prompt(
                kwargs.get("bank_name", "") or bank_name, expected_borrowers, expected_loans, expected_witnesses,
                borrower_hints, witness_hints, current_data
            )
            case_res = self._run_gemini_extraction(case_files, selected_model, case_prompt)
            if case_res and not case_res.get("error"):
                for k in ["bank", "borrower_count", "loan_count", "properties_count", "ad", "ls", "ps", "bsign", "second_schedule"]:
                    if k in case_res:
                        merged_data[k] = case_res[k]
                if "extractions" in case_res:
                    session_extractions.update(case_res["extractions"])
                if "confidence_scores" in case_res:
                    session_confidence.update(case_res["confidence_scores"])

        # Add extractions & confidence_scores to final dict so callers get them
        merged_data["extractions"] = session_extractions
        merged_data["confidence_scores"] = session_confidence

        return self._normalize_response(merged_data, expected_borrowers, expected_loans, expected_witnesses, borrower_hints, witness_hints)

    def _run_gemini_extraction(self, file_paths, selected_model, prompt):
        contents = []
        from utils.helpers import select_relevant_pdf_pages, extract_pdf_pages_text
        pdf_keywords = ["boundaries", "khasra", "plot", "flat", "covenant", "schedule", "witness", "loan", "amount", "borrower", "signatory", "interest", "emi", "tenure"]
        
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            mime_type, _ = mimetypes.guess_type(path)
            filename = os.path.basename(path)
            if ext == '.pdf':
                selected_pages = select_relevant_pdf_pages(path, pdf_keywords)
                if selected_pages:
                    extracted_text = extract_pdf_pages_text(path, selected_pages)
                    contents.append(types.Part.from_text(text=f"[Document: {filename} (Filtered Pages: {[p+1 for p in selected_pages]})]\n{extracted_text}"))
                else:
                    with open(path, 'rb') as f:
                        raw = f.read()
                    contents.append(types.Part.from_text(text=f"[PDF File: {filename}]"))
                    contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type or 'application/octet-stream'))
            elif ext in ['.jpg', '.jpeg', '.png']:
                with open(path, 'rb') as f:
                    raw = f.read()
                contents.append(types.Part.from_text(text=f"[Image File: {filename}]"))
                contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type or 'application/octet-stream'))
            elif ext == '.txt':
                with open(path, 'r', encoding='utf-8') as f:
                    contents.append(types.Part.from_text(text=f"[Text File: {filename}]\n{f.read()}"))

        try:
            final_contents = contents + [types.Part.from_text(text=prompt)]
            raw_text = self.ai_client.generate_text(
                contents=final_contents,
                model=selected_model.replace("models/", "", 1) if selected_model else "gemini-2.5-flash"
            )
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return convert_hindi_digits_to_english(data)
            return {"error": "AI returned non-JSON response", "raw": raw_text}
        except Exception as e:
            return {"error": f"Gemini AI Error: {str(e)}"}

    def _build_kyc_prompt(self, expected_borrowers, expected_witnesses):
        prompt = f"""
        Extract identity details ONLY from uploaded KYC files (Aadhaar cards, PAN cards, Driving Licenses, etc.).
        Return ONLY a JSON object with this exact structure:
        {{
          "unassigned_aadhars": [{{
             "s": "Mr/Mrs/Ms",
             "n": "Name",
             "a": "Age",
             "dob": "Date of Birth (DD/MM/YYYY or YYYY)",
             "relation_text": "Complete Relation Phrase (e.g. 'S/o Mr. Vinod Malhotra')",
             "adr": "Address (exact Aadhar print)",
             "id": "Aadhar Number",
             "pan": "PAN Card Number (if a PAN card is uploaded)",
             "files": [{{"file": "exact filename", "type": "aadhar_front|aadhar_back|pan"}}]
          }}]
        }}
        
        RULES:
        1. NO HALLUCINATION. If missing, use "".
        2. SALUTATIONS: Separate salutations from names. Use 's' field for 'Mr./Ms./Mrs.' and DO NOT prefix the name in the 'n' field or relative name in the 'relation_text' field with any salutation. Use 'Mr.' (with one dot) for males, 'Mrs.' for females.
        3. ADDRESS & RELATIONS: The first line on the back of an Aadhaar card is often the relation (e.g. S/o, C/o, W/o, D/o). YOU MUST SEPARATE THIS. Put the relation entirely in `relation_text` and only put the actual address in `adr`.
        4. DOB & AGE: Extract the actual Date of Birth (DOB) as printed (e.g. '20/02/1993' or '1993' if only year is printed) into 'dob' field, and calculate numeric age as of 2026 from YOB/DOB into 'a' field (e.g. '33').
        5. MANDATORY ENGLISH SCRIPT: You MUST use English script for ALL descriptive text including names ('n'), relations ('relation_text'), and addresses ('adr'). DO NOT USE HINDI/Devanagari script for these fields.
        6. SOURCE ATTRIBUTION: Include a top-level JSON key "extractions" which is an object mapping each extracted key path (e.g. "unassigned_aadhars.0.n") to an object containing: "source_file" (string, the exact filename), "page_number" (integer, 1-indexed), "extracted_text" (string, exact raw text), and "bounding_box" (always null).
        7. CONFIDENCE SCORES: Include a top-level JSON key "confidence_scores" which is an object mapping each extracted key path to: "score" (float 0.0-1.0) and "reason" (string or null).
        8. AADHAAR PAIRING RULE: Users upload Aadhaar cards as separate front and back files. If a back image does not print the Aadhaar number, you MUST visually and semantically pair it with its matching front image. Look at: 1) The father's/relative's name mentioned on the front vs the relation name (e.g. S/o, W/o) on the back. 2) Shared surnames or family names. 3) Filename proximity. Merge them into a single entry in 'unassigned_aadhars'.
        """
        return prompt

    def _build_case_prompt(self, bank_name, expected_borrowers, expected_loans, expected_witnesses, borrower_hints, witness_hints, current_data):
        count_instruction = f"""
        CASE: Bank:{bank_name or 'none'}, B:{expected_borrowers if expected_borrowers is not None else 'all'}, L:{expected_loans if expected_loans is not None else 'all'}, W:{expected_witnesses}.
        Hints: B: {borrower_hints.strip() or 'none'}, W: {witness_hints.strip() or 'none'}
        """
        previously_identified_instruction = ""
        if current_data:
            clean_current = {}
            for k in ['bs', 'ws', 'ls', 'ps']:
                if k in current_data and current_data[k]:
                    clean_current[k] = [{kk: vv for kk, vv in p.items() if vv} for p in current_data[k]]
                    clean_current[k] = [p for p in clean_current[k] if p]
            if 'bsign' in current_data and current_data['bsign']:
                clean_current['bsign'] = {kk: vv for kk, vv in current_data['bsign'].items() if vv}
            
            if any(clean_current.values()):
                previously_identified_instruction = f"""
        EXISTING ROLES (Map new documents to these names):
        {json.dumps(clean_current)}
        """

        prompt = """
        Extract data for Registered Mortgage (RM) case documents (Sanction letter, Legal reports, Technical reports).
        Return ONLY a JSON object.
        """ + count_instruction + previously_identified_instruction + """
        JSON STRUCTURE:
        {{
          "bank": "The name of the bank/mortgagee (e.g. 'ICICI Bank', 'Capri Global', 'Wood Capital') extracted from sanction letter or proposed mortgage deed statement in legal report",
          "borrower_count": "Extracted integer number of borrowers",
          "loan_count": "Extracted integer number of loans",
          "properties_count": "Extracted integer number of properties",
          "ad": "Loan Date (e.g. '15.04.2024')",
          "ls": [{{"n":"LAN", "a":"Amount (digits)", "w":"Amount in words", "t":"Tenure (MUST be in Months, e.g. '180 Months')", "emi":"EMI Amount (digits, e.g. '96013')", "emi_w":"EMI Amount in words (e.g. 'Ninety Six Thousand Thirteen')", "r_rate":"Applicable interest rate as on date (percentage, e.g. '12.00%')"}}],
          "ps": [{{"adr":"Property Address", "lease_deed_no":"Lease Deed Number", "n":"North", "s":"South", "e":"East", "w":"West", "lat":"Latitude from the location map of the technical report (e.g. '26.949441')", "lng":"Longitude from the location map of the technical report (e.g. '75.678939')"}}],
          "bsign": {{"n":"Signatory Name"}},
          "second_schedule": "Documents to be collected section."
        }}

        RULES:
        1. NO HALLUCINATION. If missing, use "".
        2. STRICTLY DO NOT extract "unassigned_aadhars", "bs", "ws" (witnesses), or detailed bank signatory details from these non-KYC documents.
        3. PROPERTY ADDRESS SOURCES: The property address (ps[0].adr) and property details (such as boundaries, plot/flat number, lease deed number, etc.) MUST be extracted from the Legal Scrutiny Report (LSR) or Search Report if one is uploaded. If no Legal Report/Search Report is present in the uploaded files, you MUST extract the property address and details from the Technical Scrutiny Report (usually located on the 1st or 2nd page under '3. VISIT DETAILS' or similar section). Under NO circumstances should you extract the property address or details from the Sanction Letter, as the Sanction Letter often contains abbreviated, incorrect, or incomplete property addresses.
        4. AUTHORISED SIGNATORY (bsign): Extract the bank officer's full name into 'bsign.n' if it is mentioned in the sanction letter.
        5. SCHEDULE: For "second_schedule", extract all items that start with 'Original' or 'Endorsed copy' (including 'Original Proposed Registered sale deed' but excluding other proposed documents like proposed mortgage deed).
        6. TENURE: Always in months.
        7. MANDATORY ENGLISH SCRIPT: You MUST use English script for ALL descriptive text.
        8. SOURCE ATTRIBUTION: Include a top-level JSON key "extractions" which is an object mapping each extracted key path to: "source_file", "page_number", "extracted_text", "bounding_box" (always null).
        9. CONFIDENCE SCORES: Include a top-level JSON key "confidence_scores" which is an object mapping each extracted key path to: "score" and "reason".
        """
        return prompt

    def extract_with_ai(self, file_paths, selected_model, bank_name="", expected_borrowers=None,
                        expected_loans=None, expected_witnesses=2, borrower_hints="", witness_hints="",
                        current_data=None, **kwargs):
        """Extract data from files using Google Gemini API with PDF page pre-filtering."""
        if not self.api_keys:
            return {"error": "Gemini API Keys Missing"}

        contents = []
        from utils.helpers import select_relevant_pdf_pages, extract_pdf_pages_text
        pdf_keywords = ["boundaries", "khasra", "plot", "flat", "covenant", "schedule", "witness", "loan", "amount", "borrower", "signatory", "interest", "emi", "tenure"]
        
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            mime_type, _ = mimetypes.guess_type(path)
            filename = os.path.basename(path)
            if ext == '.pdf':
                selected_pages = select_relevant_pdf_pages(path, pdf_keywords)
                if selected_pages:
                    print(f"[RM Extractor] Searchable PDF detected: {filename}. Sending selected pages text: {selected_pages}")
                    extracted_text = extract_pdf_pages_text(path, selected_pages)
                    contents.append(types.Part.from_text(text=f"[Document: {filename} (Filtered Pages: {[p+1 for p in selected_pages]})]\n{extracted_text}"))
                else:
                    print(f"[RM Extractor] Scanned/non-searchable PDF: {filename}. Sending full file bytes.")
                    with open(path, 'rb') as f:
                        raw = f.read()
                    contents.append(types.Part.from_text(text=f"[PDF File: {filename}]"))
                    contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type or 'application/octet-stream'))
            elif ext in ['.jpg', '.jpeg', '.png']:
                with open(path, 'rb') as f:
                    raw = f.read()
                contents.append(types.Part.from_text(text=f"[Image File: {filename}]"))
                contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type or 'application/octet-stream'))
            elif ext == '.txt':
                with open(path, 'r', encoding='utf-8') as f:
                    contents.append(types.Part.from_text(text=f"[Text File: {filename}]\n{f.read()}"))

        prompt = self._build_prompt(bank_name, expected_borrowers, expected_loans,
                                    expected_witnesses, borrower_hints, witness_hints, current_data)
                                    
        try:
            final_contents = contents + [types.Part.from_text(text=prompt)]
            raw_text = self.ai_client.generate_text(
                contents=final_contents,
                model=selected_model.replace("models/", "", 1) if selected_model else "gemini-2.5-flash"
            )
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                norm_data = self._normalize_response(data, expected_borrowers, expected_loans,
                                                expected_witnesses, borrower_hints, witness_hints)
                return convert_hindi_digits_to_english(norm_data)
            return {"error": "AI returned non-JSON response", "raw": raw_text}
        except Exception as e:
            return {"error": f"Gemini AI Failover Error: {str(e)}"}

    def _build_prompt(self, bank_name, expected_borrowers, expected_loans, expected_witnesses, borrower_hints, witness_hints, current_data):
        count_instruction = f"""
        CASE: Bank:{bank_name or 'none'}, B:{expected_borrowers if expected_borrowers is not None else 'all'}, L:{expected_loans if expected_loans is not None else 'all'}, W:{expected_witnesses}.
        Hints: B: {borrower_hints.strip() or 'none'}, W: {witness_hints.strip() or 'none'}
        """

        previously_identified_instruction = ""
        if current_data:
            clean_current = {}
            for k in ['bs', 'ws', 'ls', 'ps']:
                if k in current_data and current_data[k]:
                    clean_current[k] = [{kk: vv for kk, vv in p.items() if vv} for p in current_data[k]]
                    clean_current[k] = [p for p in clean_current[k] if p]
            if 'bsign' in current_data and current_data['bsign']:
                clean_current['bsign'] = {kk: vv for kk, vv in current_data['bsign'].items() if vv}
            
            if any(clean_current.values()):
                previously_identified_instruction = f"""
        EXISTING ROLES (Map new documents to these names):
        {json.dumps(clean_current)}
        """

        prompt = """
        Extract data for Registered Mortgage (RM). Return ONLY a JSON object.
        """ + count_instruction + previously_identified_instruction + """
        JSON STRUCTURE:
        {
          "bank": "The name of the bank/mortgagee (e.g. 'ICICI Bank', 'Capri Global', 'Wood Capital') extracted from sanction letter or proposed mortgage deed statement in legal report",
          "borrower_count": "Extracted integer number of borrowers",
          "loan_count": "Extracted integer number of loans",
          "properties_count": "Extracted integer number of properties",
          "ad": "Loan Date (e.g. '15.04.2024')",
          "bs": [{"s":"Mr./Ms./Mrs.", "n":"Name", "a":"Age", "dob":"Date of Birth as printed (e.g. '20/02/1993' or '1993')", "relation_text":"Complete Relation Phrase (e.g. 'S/o Mr. Vinod Malhotra')", "adr":"Address", "id":"Aadhar ID", "pan":"PAN Card No"}],
          "ls": [{"n":"LAN", "a":"Amount (digits)", "w":"Amount in words", "t":"Tenure (MUST be in Months, e.g. '180 Months')", "emi":"EMI Amount (digits, e.g. '96013')", "emi_w":"EMI Amount in words (e.g. 'Ninety Six Thousand Thirteen')", "r_rate":"Applicable interest rate as on date (percentage, e.g. '12.00%')"}],
          "ps": [{"adr":"Property Address", "lease_deed_no":"Lease Deed Number", "n":"North", "s":"South", "e":"East", "w":"West", "lat":"Latitude from the location map of the technical report (e.g. '26.949441')", "lng":"Longitude from the location map of the technical report (e.g. '75.678939')"}],
          "bsign": {"n":"Signatory Name", "a":"Age", "dob":"Date of Birth as printed (e.g. '20/02/1993' or '1993')", "relation_text":"Complete Relation Phrase (e.g. 'S/o Mr. Rajesh Nama')", "pan":"PAN Card No", "id":"Aadhar ID", "adr":"Address"},
          "ws": [{"n":"Name", "relation_text":"Complete Relation Phrase (e.g. 'S/o Mr. Gopal Singh')", "adr":"Address", "a":"Age (numeric, calculate from YOB/DOB as of 2026)", "dob":"Date of Birth as printed (e.g. '20/02/1993' or '1993')", "id":"Aadhar ID"}],
          "unassigned_aadhars": [{"s":"Mr/Mrs/Ms", "n":"Name", "a":"Age", "dob":"Date of Birth as printed (e.g. '20/02/1993' or '1993')", "relation_text":"Complete Relation Phrase", "adr":"Address (exact Aadhar print)", "id":"Aadhar Number", "pan":"PAN Card Number (if a PAN card is uploaded)", "files": [{"file": "exact filename", "type": "aadhar_front|aadhar_back|pan"}]}],
          "second_schedule": "Documents to be collected section."
        }

        RULES:
        1. NO HALLUCINATION. If missing, use "".
        2. COUNTS: "bs" exactly selected count. "ls" selected count. "ws" exactly 2.
        3. DATES & BOUNDARIES: Extract exactly as printed.
        4. AADHAAR & PAN CARDS: Extract details from ALL uploaded Aadhaar cards (including name, age, DOB, relation phrase, address, and ID) and PAN cards (including name and PAN number) EXCLUSIVELY into 'unassigned_aadhars' (whether they belong to borrowers, witnesses, or the bank signatory). For each card in this list, populate a 'files' array containing objects with 'file' (the exact filename from the '[Image/PDF/Text/Document File: filename]' headers) and 'type' (identifying if the file is 'aadhar_front', 'aadhar_back', or 'pan' based on visual contents; e.g. if you extract details from a front and back Aadhaar image and a PAN card, include three file objects). DO NOT map them directly to 'bs', 'ws', or 'bsign'. They will be mapped manually later.
        4b. WITNESS OCR ISOLATION: For the primary borrowers, witnesses, and bank officers, extract their physical Aadhaar/PAN cards into 'unassigned_aadhars' as specified in Rule 4. STRICTLY DO NOT automatically pre-populate the 'ws' (witnesses) array with any details from witness cards; witness cards must only exist in 'unassigned_aadhars' to be manually mapped in the UI.
        5. DOB & AGE: Extract the actual Date of Birth (DOB) as printed (e.g. '20/02/1993' or '1993' if only year is printed) into 'dob' field, and calculate numeric age as of 2026 from YOB/DOB into 'a' field (e.g. '33').
        6. SALUTATIONS: Separate salutations from names. Use 's' field for 'Mr./Ms./Mrs.' and DO NOT prefix the name in the 'n' field or relative name in the 'relation_text' field with any salutation. Use 'Mr.' (with one dot) for males, 'Mrs.' for females.
        7. ADDRESS & RELATIONS: The first line on the back of an Aadhaar card is often the relation (e.g. S/o, C/o, W/o, D/o). YOU MUST SEPARATE THIS. Put the relation entirely in `relation_text` and only put the actual address in `adr`.
        7b. STRICT RELATION FORMATTING: ALWAYS format relations using exact English (e.g. 'S/o Mr. ...', 'W/o Mr. ...', 'D/o Mr. ...'). DO NOT leave them as 'Son of' or 'Wife of' in the extracted output.
        8. AUTHORISED SIGNATORY (bsign): Extract the bank officer's full name into 'bsign.n' if it is mentioned in the sanction letter. STRICTLY DO NOT extract or fill any other bank signatory details (like Aadhaar, PAN, address, age) from legal reports or sanction letters; those other details must only be extracted from their physical ID card (Aadhaar or PAN) into 'unassigned_aadhars' as specified in Rule 4.
        9. SCHEDULE: For "second_schedule", extract all items that start with 'Original' or 'Endorsed copy' (including 'Original Proposed Registered sale deed' but excluding other proposed documents like proposed mortgage deed).
        10. INCREMENTAL: Do not re-extract existing fields. Focus on new documents.
        11. TENURE: Always in months.
        12. PAN CARDS: Extract 10-char alphanumeric PAN into 'pan' field.
        13. BORROWER DETAILS: STRICTLY DO NOT extract borrower details from non-ID documents. 'bs' list must be empty initially. Populate from Aadhaar/PAN processed into 'unassigned_aadhars' and manually map.
        14. MULTI-LOAN: If multiple sanction letters are present, extract ALL of them into the 'ls' list.
        15. PRECISION: EXTRACT ALL DIGITS OF THE LOAN AMOUNT AND EMI AMOUNT. DO NOT MISS ANY NUMBERS.
        16. MANDATORY ENGLISH SCRIPT: You MUST use English script for ALL descriptive text including names ('n'), relations ('relation_text'), and addresses ('adr'). DO NOT USE HINDI/Devanagari script for these fields.
        17. ENGLISH SOURCE PRIORITY: Always prefer extracting names and addresses natively from English text in the uploaded documents.
        18. SOURCE ATTRIBUTION: Include a top-level JSON key "extractions" which is an object mapping each extracted key path (e.g. "bs.0.n", "bs.0.id", "ls.0.n", "ps.0.adr", "ad") to an object containing: "source_file" (string, the exact filename of the source document where this fact was found), "page_number" (integer page number, 1-indexed, where found, default 1), "extracted_text" (string, the exact raw text that was matched/extracted), and "bounding_box" (always null).
        19. CONFIDENCE SCORES: Include a top-level JSON key "confidence_scores" which is an object mapping each extracted key path (e.g. "bs.0.n", "bs.0.id", "ad") to an object containing: "score" (a float between 0.0 and 1.0 representing extraction confidence) and "reason" (string, explaining why the score is less than 1.0, or null if the score is 1.0).
        20. PROPERTY ADDRESS SOURCES: The property address (ps[0].adr) and property details (such as boundaries, plot/flat number, lease deed number, etc.) MUST be extracted from the Legal Scrutiny Report (LSR) or Search Report if one is uploaded. If no Legal Report/Search Report is present in the uploaded files, you MUST extract the property address and details from the Technical Scrutiny Report (usually located on the 1st or 2nd page under '3. VISIT DETAILS' or similar section). Under NO circumstances should you extract the property address or details from the Sanction Letter, as the Sanction Letter often contains abbreviated, incorrect, or incomplete property addresses.
        """
        return prompt

    def _normalize_response(self, data, expected_borrowers, expected_loans, expected_witnesses, borrower_hints, witness_hints):
        if not isinstance(data, dict):
            return {"error": "AI returned JSON, but it was not an object"}

        data["ad"] = format_date_with_dots(data.get("ad", ""))
        
        # Normalize auto-watcher metadata
        data["bank"] = str(data.get("bank", "ICICI")).strip()
        
        try:
            data["borrower_count"] = int(data.get("borrower_count", 1))
        except Exception:
            data["borrower_count"] = 1
            
        try:
            data["loan_count"] = int(data.get("loan_count", 1))
        except Exception:
            data["loan_count"] = 1
            
        try:
            data["properties_count"] = int(data.get("properties_count", 1))
        except Exception:
            data["properties_count"] = 1

        self._normalize_list(data, "bs", ["s", "n", "a", "dob", "r", "rn", "relation_text", "adr", "id", "pan"])
        self._normalize_list(data, "ls", ["n", "a", "w", "t", "emi", "emi_w", "r_rate"])
        self._normalize_list(data, "ps", ["adr", "lease_deed_no", "n", "s", "e", "w", "lat", "lng"])
        self._normalize_list(data, "ws", ["n", "r", "rn", "relation_text", "adr", "a", "dob", "id"])
        self._normalize_list(data, "unassigned_aadhars", ["s", "n", "a", "dob", "r", "rn", "relation_text", "adr", "id", "pan", "files"])
        data = self._merge_unpaired_aadhars(data)

        if "bsign" in data and isinstance(data["bsign"], dict):
            bsign = data["bsign"]
            for f in ["n", "a", "dob", "relation_text", "pan", "id", "adr"]:
                bsign[f] = str(bsign.get(f, "")).strip()
        else:
            data["bsign"] = {"n":"", "a":"", "dob":"", "relation_text":"", "pan":"", "id":"", "adr":""}

        # Normalize relations
        doc_type = "RM"
        for key in ["bs", "ws"]:
            for person in data.get(key, []):
                if person.get("relation_text"):
                    person["relation_text"] = normalize_relation_prefix(person["relation_text"], doc_type)
        if data.get("bsign", {}).get("relation_text"):
            data["bsign"]["relation_text"] = normalize_relation_prefix(data["bsign"]["relation_text"], doc_type)

        raw_ds = ""
        if "second_schedule" in data:
            raw_ds = str(data["second_schedule"])
            m = re.search(r'Documents\s*to\s*be\s*collected\b[:\s]*(.*)', raw_ds, re.IGNORECASE)
            if m:
                raw_ds = m.group(1).strip()
            else:
                raw_ds = raw_ds.strip()

        formatted_chain, clean_docs = parse_and_format_chain(raw_ds)
        data["ds_text"] = formatted_chain
        data["second_schedule"] = formatted_chain
        data["ds"] = [{"t": doc} for doc in clean_docs]

        for b in data.get("bs", []):
            if b.get("adr"): b["adr"] = clean_aadhar_address(b["adr"])
        for w in data.get("ws", []):
            if w.get("adr"): w["adr"] = clean_aadhar_address(w["adr"])
        for ua in data.get("unassigned_aadhars", []):
            if ua.get("adr"): ua["adr"] = clean_aadhar_address(ua["adr"])

        # Import parse_relation_text to split relation_text for RM
        for b in data.get("bs", []):
            if b.get("relation_text"):
                norm_rel = normalize_relation_prefix(b["relation_text"], "RM")
                b["relation_text"] = norm_rel
                r, rn = parse_relation_text(norm_rel)
                b["r"] = r
                b["rn"] = rn
            if b.get("n"): b["n"] = normalize_name_salutation(b["n"], b.get("r"))
        for w in data.get("ws", []):
            if w.get("relation_text"):
                norm_rel = normalize_relation_prefix(w["relation_text"], "RM")
                w["relation_text"] = norm_rel
                r, rn = parse_relation_text(norm_rel)
                w["r"] = r
                w["rn"] = rn
            if w.get("n"): w["n"] = normalize_name_salutation(w["n"], w.get("r"))
        for ua in data.get("unassigned_aadhars", []):
            if ua.get("relation_text"):
                norm_rel = normalize_relation_prefix(ua["relation_text"], "RM")
                ua["relation_text"] = norm_rel
                r, rn = parse_relation_text(norm_rel)
                ua["r"] = r
                ua["rn"] = rn
            if ua.get("n"):
                ua["n"] = normalize_name_salutation(ua["n"], ua.get("r"))

        def split_sal(name_with_sal):
            if not name_with_sal: return "", ""
            s = name_with_sal.strip()
            salutations_pattern = r'^(?:M/s\.?|Messrs|Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Shri\.?|Shree\.?|Late\.?|LoxhZ;\.?|श्री|श्रीमती|सुश्री|डॉ\.?|स्व\.?|स्वर्गीय)\s*'
            match = re.match(salutations_pattern, s, re.IGNORECASE)
            if match:
                sal = match.group(0).strip()
                name_part = s[match.end():].strip()
                return sal, name_part
            return "", name_with_sal

        for b in data.get("bs", []):
            if b.get("n"):
                sal, name = split_sal(b["n"])
                b["s"] = sal
                b["n"] = name

        bsign = data.get("bsign", {})
        if not bsign.get("id") and not bsign.get("pan"):
            # Preserve the bank officer's name extracted in the first pass
            officer_name = bsign.get("n", "")
            bsign = {"n": officer_name, "a":"", "dob":"", "r":"", "rn":"", "relation_text":"", "pan":"", "id":"", "adr":""}
        else:
            if bsign.get("relation_text"):
                norm_rel = normalize_relation_prefix(bsign["relation_text"], "RM")
                bsign["relation_text"] = norm_rel
                r, rn = parse_relation_text(norm_rel)
                bsign["r"] = r
                bsign["rn"] = rn
            if bsign.get("n"):
                bsign["n"] = normalize_name_salutation(bsign["n"], bsign.get("r"))
                sal, name = split_sal(bsign["n"])
                bsign["s"] = sal
                bsign["n"] = name
        data["bsign"] = self._normalize_person(bsign, ["s", "n", "a", "dob", "r", "rn", "relation_text", "pan", "id", "adr"])

        self._apply_person_hints(data, borrower_hints, witness_hints)

        for b in data.get("bs", []):
            if not b.get("id") and not b.get("pan"):
                for k in ["s", "n", "a", "dob", "r", "rn", "relation_text", "adr", "id", "pan"]:
                    b[k] = ""

        # Witness OCR Isolation: Filter out witness names from unassigned_aadhars
        witness_names = set()
        for w in data.get("ws", []):
            name_val = w.get("n", "").strip().casefold()
            if name_val:
                witness_names.add(name_val)
                sans_sal = re.sub(r'^(mr|mrs|ms|shri|smt|sh)\.?\s+', '', name_val).strip()
                if sans_sal:
                    witness_names.add(sans_sal)

        filtered_ua = []
        for ua in data.get("unassigned_aadhars", []):
            ua_name = ua.get("n", "").strip().casefold()
            ua_sans_sal = re.sub(r'^(mr|mrs|ms|shri|smt|sh)\.?\s+', '', ua_name).strip()
            is_witness = False
            if ua_name in witness_names or ua_sans_sal in witness_names:
                is_witness = True
            for w_name in witness_names:
                if w_name and (w_name in ua_name or ua_name in w_name):
                    is_witness = True
                    break
            if not is_witness:
                filtered_ua.append(ua)
        data["unassigned_aadhars"] = filtered_ua

        # Filter borrowers that are witnesses
        data["bs"] = [
            b for b in data.get("bs", [])
            if not (b.get("n", "").casefold() in {w["n"].casefold() for w in data.get("ws", []) if w.get("n")} and not b.get("id"))
        ]

        def get_amount_float(a_str):
            try:
                clean = re.sub(r'[^\d.]', '', str(a_str))
                return float(clean) if clean else 0.0
            except:
                return 0.0

        if "ls" in data and isinstance(data["ls"], list):
            data["ls"].sort(key=lambda x: get_amount_float(x.get("a", 0)), reverse=True)

        self._force_count(data, "bs", ["s", "n", "a", "dob", "r", "rn", "relation_text", "adr", "id", "pan"], expected_borrowers)
        self._force_count(data, "ls", ["n", "a", "w", "t", "emi", "emi_w", "r_rate"], expected_loans)
        self._force_count(data, "ws", ["n", "r", "rn", "relation_text", "adr", "a", "dob", "id"], expected_witnesses)

        for loan in data.get("ls", []):
            if loan.get("a"):
                loan["a"] = format_indian_currency(str(loan["a"]))
            if not loan.get("w") or loan["w"].casefold() in {"amount in words", "not found"}:
                loan["w"] = amount_to_words(str(loan.get("a", "0")))
            
            if loan.get("emi"):
                loan["emi"] = format_indian_currency(str(loan["emi"]))
            if not loan.get("emi_w") or loan["emi_w"].casefold() in {"amount in words", "not found"}:
                loan["emi_w"] = amount_to_words(str(loan.get("emi", "0")))
                
            if loan.get("t"):
                t_val = str(loan["t"]).strip()
                match = re.search(r'(\d+)\s*(?:years?|yrs?|y/o)', t_val, re.IGNORECASE)
                if match:
                    years = int(match.group(1))
                    months = years * 12
                    loan["t"] = f"{months} Months"
                elif t_val.isdigit():
                    loan["t"] = f"{t_val} Months"

        return data

    def _merge_unpaired_aadhars(self, data):
        uadhars = data.get("unassigned_aadhars", [])
        if not isinstance(uadhars, list) or len(uadhars) <= 1:
            return data
        
        fronts = [
            u for u in uadhars 
            if any(f.get("type") == "aadhar_front" for f in u.get("files", []))
            and not any(f.get("type") == "aadhar_back" for f in u.get("files", []))
        ]
        backs = [
            u for u in uadhars 
            if any(f.get("type") == "aadhar_back" for f in u.get("files", []))
            and not any(f.get("type") == "aadhar_front" for f in u.get("files", []))
        ]
        
        def get_surname(name):
            parts = str(name).strip().split()
            return parts[-1].lower() if parts else ""

        merged_backs = []
        for f_item in fronts:
            f_name = f_item.get("n", "")
            f_surname = get_surname(f_name)
            f_files = [f.get("file") for f in f_item.get("files", [])]
            
            best_back = None
            for b_item in backs:
                b_id = b_item.get("id")
                if b_item in merged_backs:
                    continue
                # Don't pair if back card has a distinct name or ID that doesn't match front
                if b_id and f_item.get("id") and b_id != f_item.get("id"):
                    continue
                    
                b_rel_name = b_item.get("rn", "") or b_item.get("relation_text", "")
                b_rel_surname = get_surname(b_rel_name)
                b_files = [f.get("file") for f in b_item.get("files", [])]
                
                # Match 1: Surnames match (e.g. Meena vs Meena)
                if f_surname and b_rel_surname and f_surname == b_rel_surname:
                    best_back = b_item
                    break
                    
                # Match 2: Alphabetic/Proximity match of filenames
                if f_files and b_files:
                    f_base = os.path.basename(f_files[0])
                    b_base = os.path.basename(b_files[0])
                    # Check if filenames are highly similar or adjacent in listing
                    if len(os.path.commonprefix([f_base, b_base])) > 5:
                        best_back = b_item
                        break
                        
            if best_back:
                merged_backs.append(best_back)
                # Merge fields from back into front
                for key in ["adr", "relation_text", "r", "rn"]:
                    if not f_item.get(key) and best_back.get(key):
                        f_item[key] = best_back[key]
                # Merge files list
                existing_files = {f.get("file") for f in f_item.get("files", [])}
                for f_obj in best_back.get("files", []):
                    if f_obj.get("file") not in existing_files:
                        f_item["files"].append(f_obj)
                        
        # Filter out merged backs
        filtered_uadhars = [u for u in uadhars if u not in merged_backs]
        data["unassigned_aadhars"] = filtered_uadhars
        return data

    def _normalize_person(self, person, fields):
        return {f: str(person.get(f, "")).strip() for f in fields}

    def _apply_person_hints(self, data, borrower_hints, witness_hints):
        pass

    def _normalize_list(self, data, key, fields):
        items = data.get(key)
        if not isinstance(items, list):
            data[key] = []
            return
        
        clean_items = []
        for item in items:
            if not isinstance(item, dict): continue
            clean_item = {}
            for f in fields:
                val = item.get(f)
                if val is None:
                    clean_item[f] = ""
                elif isinstance(val, (dict, list)):
                    clean_item[f] = val
                else:
                    clean_item[f] = str(val).strip()
            if "date" in clean_item and isinstance(clean_item["date"], str):
                clean_item["date"] = format_date_with_dots(clean_item["date"])
            clean_items.append(clean_item)
        data[key] = clean_items

    def _force_count(self, data, key, fields, count):
        if count is None: return
        items = data.get(key, [])
        while len(items) < count:
            items.append({f: "" for f in fields})
        data[key] = items[:count]

    def raw_generate(self, prompt, model_name):
        """Low-level single-prompt generation with key rotation AND model fallback."""
        if model_name and "NVIDIA" in str(model_name):
            print(f"[DIRECT] Routing request directly to NVIDIA NIM: {model_name}")
            try:
                import requests
                nvidia_key = get_nvidia_api_key()
                nvidia_url = "https://integrate.api.nvidia.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {nvidia_key}",
                    "Content-Type": "application/json"
                }
                
                target_model = "nvidia/nemotron-3-ultra-550b-a55b" if "Nemotron" in str(model_name) else "meta/llama-3.1-8b-instruct"
                timeout_val = 300 if "Nemotron" in str(model_name) else 120
                
                payload = {
                    "model": target_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "top_p": 0.7,
                    "max_tokens": 4096
                }
                res = requests.post(nvidia_url, headers=headers, json=payload, timeout=timeout_val)
                if res.status_code == 200:
                    resp_json = res.json()
                    text = resp_json['choices'][0]['message']['content']
                    print(f"[SUCCESS] Direct NVIDIA NIM call for {model_name} ({target_model}) succeeded!")
                    return text
                else:
                    print(f"[ERROR] NVIDIA NIM direct call failed with status {res.status_code}: {res.text}")
            except Exception as nv_err:
                print(f"[ERROR] NVIDIA NIM direct call raised exception: {nv_err}")
            return None

        if not self.api_keys:
            print("[DIAGNOSTIC] raw_generate: No API keys provided.")
            return None
        
        primary_model = model_name.replace("models/", "", 1) if model_name else "gemini-2.5-flash"
        fallbacks = [primary_model, "gemini-3.5-flash", "gemini-2.5-flash"]
        
        fallback_queue = []
        for f in fallbacks:
            if f not in fallback_queue: fallback_queue.append(f)

        from google.genai import types

        for current_model in fallback_queue:
            try:
                print(f"[DIAGNOSTIC] raw_generate: Attempting model {current_model}...")
                contents = [types.Part.from_text(text=prompt)]
                res_text = self.ai_client.generate_text(
                    contents=contents,
                    model=current_model
                )
                if res_text:
                    return res_text
            except Exception as e:
                print(f"[FAILOVER WARNING] Gemini raw_generate failed for model {current_model}: {e}")
                continue
        # Fallback to NVIDIA NIM Llama 3.1 8B
        print("[FAILOVER] Gemini exhausted. Attempting fallback to NVIDIA NIM Llama 3.1 8B...")
        try:
            import requests
            nvidia_key = get_nvidia_api_key()
            nvidia_url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {nvidia_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "meta/llama-3.1-8b-instruct",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "top_p": 0.7,
                "max_tokens": 4096
            }
            res = requests.post(nvidia_url, headers=headers, json=payload, timeout=120)
            if res.status_code == 200:
                resp_json = res.json()
                text = resp_json['choices'][0]['message']['content']
                print("[SUCCESS] Fallback to NVIDIA NIM Llama 3.1 8B succeeded!")
                return text
            else:
                print(f"[FAILOVER WARNING] NVIDIA NIM fallback failed with status {res.status_code}: {res.text}")
        except Exception as nv_err:
            print(f"[FAILOVER WARNING] NVIDIA NIM fallback raised exception: {nv_err}")

        return None
