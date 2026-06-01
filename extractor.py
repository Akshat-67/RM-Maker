import re
import base64
import mimetypes
from google import genai
from num2words import num2words
import json
import os

class DataExtractor:
    def __init__(self, api_key=None, api_keys=None, provider="gemini", *args, **kwargs):
        """
        api_key : single Gemini API key (string)
        api_keys: list of Gemini API keys (list of strings)
        """
        self.provider = "gemini"
        
        if api_keys:
            self.api_keys = api_keys
        elif api_key:
            self.api_keys = [api_key]
        else:
            self.api_keys = []
            
        self.active_key_index = 0
        self.client = None
        self._init_client()

    def _init_client(self):
        if self.api_keys and self.active_key_index < len(self.api_keys):
            key = self.api_keys[self.active_key_index]
            self.client = genai.Client(api_key=key)
        else:
            self.client = None

    def _rotate_key(self):
        if not self.api_keys:
            return False
        self.active_key_index = (self.active_key_index + 1) % len(self.api_keys)
        print(f"[FAILOVER] Rotating Gemini API key to index {self.active_key_index}...")
        self._init_client()
        return True

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

<<<<<<< HEAD
    def format_indian_currency(self, amount_str):
        if not amount_str:
            return ""
        try:
            s = re.sub(r'[^\d.]', '', str(amount_str))
            if not s:
                return amount_str
            
            if '.' in s:
                parts = s.split('.')
                integer_part = parts[0]
                decimal_part = '.' + parts[1]
            else:
                integer_part = s
                decimal_part = ''
                
            n = len(integer_part)
            if n <= 3:
                return integer_part + decimal_part
                
            last_three = integer_part[-3:]
            remaining = integer_part[:-3]
            
            groups = []
            while remaining:
                groups.append(remaining[-2:])
                remaining = remaining[:-2]
                
            groups.reverse()
            formatted_integer = ",".join(groups) + "," + last_three
            return formatted_integer + decimal_part
=======
    def get_available_models(self):
        """Returns a list of models using the new genai client."""
        if not self.client: return []
        try:
            # Listing models in the new SDK
            models = self.client.models.list()
            # The new SDK uses 'supported_actions'
            return [m.name for m in models if 'generateContent' in m.supported_actions]
>>>>>>> 3c8ef3700876862f09e11a95b6a2e9e767d3567e
        except Exception:
            return amount_str

    def format_date_with_dots(self, date_str):
        if not date_str:
            return ""
        s = str(date_str).strip()
        s = re.sub(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})', r'\1.\2.\3', s)
        return s

    def clean_aadhar_address(self, address_str):
        if not address_str:
            return ""
        s = str(address_str).strip()
        pattern = r'^(?:S/o|W/o|D/o|C/o|H/o|Care\s+of|Son\s+of|Wife\s+of|Daughter\s+of)\b[:\s]*(?:Mr\.?|Mrs\.?|Ms\.?|Shri|Smt\.?|Sh\.?)?\s*[^,]+,\s*'
        s = re.sub(pattern, '', s, flags=re.IGNORECASE)
        return s.strip()

    def normalize_relative_salutation(self, name, relation):
        if not name:
            return ""
        s = str(name).strip()
        s = re.sub(r'\s+', ' ', s)
        
        if re.match(r'^(?:Mr\.?|Mrs\.?|Ms\.?|Shri|Smt\.?|Sh\.?)\b', s, re.IGNORECASE):
            m = re.match(r'^([a-z\.\:]+)\b(.*)', s, re.IGNORECASE)
            if m:
                sal = m.group(1).lower().rstrip('.')
                rest = m.group(2)
                if sal == "mr": s = "Mr." + rest
                elif sal == "mrs": s = "Mrs." + rest
                elif sal == "ms": s = "Ms." + rest
                elif sal == "shri": s = "Shri" + rest
                elif sal == "smt": s = "Smt." + rest
                elif sal == "sh": s = "Sh." + rest
            return s
            
        rel_lower = str(relation or "").strip().casefold()
        if any(x in rel_lower for x in ["mother", "m/o", "mother of", "husband", "husband of", "h/o"]) and not any(x in rel_lower for x in ["wife", "w/o", "father"]):
            s = "Mrs. " + s
        else:
            s = "Mr. " + s
        return s

    def normalize_name_salutation(self, name, relation=None, default_to_male=True):
        if not name:
            return ""
        s = str(name).strip()
        s = re.sub(r'\s+', ' ', s)
        
        if re.match(r'^(?:Mr\.?|Mrs\.?|Ms\.?|Shri|Smt\.?|Sh\.?)\b', s, re.IGNORECASE):
            m = re.match(r'^([a-z\.\:]+)\b(.*)', s, re.IGNORECASE)
            if m:
                sal = m.group(1).lower().rstrip('.')
                rest = m.group(2)
                if sal == "mr": s = "Mr." + rest
                elif sal == "mrs": s = "Mrs." + rest
                elif sal == "ms": s = "Ms." + rest
                elif sal == "shri": s = "Shri" + rest
                elif sal == "smt": s = "Smt." + rest
                elif sal == "sh": s = "Sh." + rest
            return s
            
        is_female = False
        if relation:
            rel_lower = str(relation).strip().casefold()
            if any(x in rel_lower for x in ["w/o", "wife of", "wife", "mother", "m/o", "mother of", "d/o", "daughter of", "daughter"]):
                is_female = True
                
        if is_female:
            s = "Mrs. " + s
        else:
            if default_to_male:
                s = "Mr. " + s
        return s

    def get_available_models(self):
        """Returns available models for Gemini with failover rotation."""
        if not self.api_keys:
            return []
            
        attempts = 0
        max_attempts = len(self.api_keys)
        
        while attempts < max_attempts:
            if not self.client:
                self._init_client()
            if not self.client:
                return []
            try:
                models = self.client.models.list()
                return [m.name for m in models if 'generateContent' in m.supported_actions]
            except Exception as e:
                print(f"[FAILOVER WARNING] Gemini list models failed with key index {self.active_key_index}: {e}")
                self._rotate_key()
                attempts += 1
                
        return []

    def raw_generate(self, prompt, model_name):
<<<<<<< HEAD
        """Low-level single-prompt generation with key failover."""
        if not self.api_keys:
=======
        if not self.client: return None
        try:
            response = self.client.models.generate_content(model=model_name, contents=prompt)
            return response.text
        except Exception as e:
            print(f"Extraction Error: {e}")
>>>>>>> 3c8ef3700876862f09e11a95b6a2e9e767d3567e
            return None
        clean_name = model_name.replace("models/", "", 1) if model_name else model_name
        attempts = 0
        max_attempts = len(self.api_keys)
        while attempts < max_attempts:
            if not self.client:
                self._init_client()
            if not self.client:
                return None
            try:
                response = self.client.models.generate_content(model=clean_name, contents=prompt)
                return response.text
            except Exception as e:
                print(f"[raw_generate] Key index {self.active_key_index} failed: {e}")
                self._rotate_key()
                attempts += 1
        print("[raw_generate] All API keys exhausted.")
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

    def _normalize_response(self, data, expected_borrowers=None, expected_loans=None, expected_witnesses=2, borrower_hints="", witness_hints="", doc_type=None, expected_sellers=None, expected_buyers=None, seller_hints="", buyer_hints=""):
        if not isinstance(data, dict):
            return {"error": "AI returned JSON, but it was not an object"}

        # Auto-detect doc_type if not explicitly provided
        if not doc_type:
            if "sellers" in data or "buyers" in data:
                doc_type = "SD"
            else:
                doc_type = "RM"

        # Always set execution date (rd) to today's date
        import datetime
        data["rd"] = datetime.date.today().strftime("%d.%m.%Y")

        if doc_type == "SD":
            self._normalize_list(data, "sellers", ["s", "n", "a", "r", "rn", "caste", "adr", "id", "pan"])
            self._normalize_list(data, "buyers", ["s", "n", "a", "r", "rn", "caste", "adr", "id", "pan"])
            self._normalize_list(data, "ps", ["flat_no", "floor", "building", "adr", "area", "area_unit", "parking", "e", "w", "n", "s"])
            self._normalize_list(data, "ws", ["n", "r", "rn", "adr"])
            self._normalize_list(data, "unassigned_aadhars", ["s", "n", "a", "r", "rn", "adr", "id"])
            self._normalize_list(data, "chain", ["seller", "buyer", "date", "book", "vol", "page", "kram"])

            # Clean parentage prefixes from addresses
            for s in data.get("sellers", []):
                if s.get("adr"): s["adr"] = self.clean_aadhar_address(s["adr"])
            for b in data.get("buyers", []):
                if b.get("adr"): b["adr"] = self.clean_aadhar_address(b["adr"])
            for w in data.get("ws", []):
                if w.get("adr"): w["adr"] = self.clean_aadhar_address(w["adr"])
            for ua in data.get("unassigned_aadhars", []):
                if ua.get("adr"): ua["adr"] = self.clean_aadhar_address(ua["adr"])

            # Prefix salutations ('Mr.', 'Mrs.') to relative and witness names if missing
            for s in data.get("sellers", []):
                if s.get("rn"): s["rn"] = self.normalize_relative_salutation(s["rn"], s.get("r"))
            for b in data.get("buyers", []):
                if b.get("rn"): b["rn"] = self.normalize_relative_salutation(b["rn"], b.get("r"))
            for w in data.get("ws", []):
                if w.get("n"): w["n"] = self.normalize_name_salutation(w["n"], w.get("r"))
                if w.get("rn"): w["rn"] = self.normalize_relative_salutation(w["rn"], w.get("r"))
            for ua in data.get("unassigned_aadhars", []):
                if ua.get("n"): ua["n"] = self.normalize_name_salutation(ua["n"], ua.get("r"))
                if ua.get("rn"): ua["rn"] = self.normalize_relative_salutation(ua["rn"], ua.get("r"))

            # Strictly clear seller/buyer details programmatically if no physical ID card (Aadhaar or PAN) was processed
            for s in data.get("sellers", []):
                if not s.get("id") and not s.get("pan"):
                    for k in ["s", "n", "a", "r", "rn", "caste", "adr", "id", "pan"]:
                        s[k] = ""
            for b in data.get("buyers", []):
                if not b.get("id") and not b.get("pan"):
                    for k in ["s", "n", "a", "r", "rn", "caste", "adr", "id", "pan"]:
                        b[k] = ""

            self._force_count(data, "sellers", ["s", "n", "a", "r", "rn", "caste", "adr", "id", "pan"], expected_sellers)
            self._force_count(data, "buyers", ["s", "n", "a", "r", "rn", "caste", "adr", "id", "pan"], expected_buyers)
            self._force_count(data, "ws", ["n", "r", "rn", "adr"], expected_witnesses)

            # Property details default empty entry if missing
            if not data.get("ps"):
                data["ps"] = [{field: "" for field in ["flat_no", "floor", "building", "adr", "area", "area_unit", "parking", "e", "w", "n", "s"]}]
            
            # Format boundaries to have dot or fallback
            for p in data.get("ps", []):
                for k in ["e", "w", "n", "s"]:
                    if p.get(k): p[k] = str(p[k]).strip()

            return data

        # Default RM handling
        # Format loan agreement date (ad) with dots
        raw_ad = "" if data.get("ad") is None else str(data.get("ad", "")).strip()
        data["ad"] = self.format_date_with_dots(raw_ad)

        self._normalize_list(data, "bs", ["s", "n", "a", "r", "rn", "adr", "id", "pan"])
        self._normalize_list(data, "ls", ["n", "a", "w", "t"])
        self._normalize_list(data, "ps", ["adr", "n", "s", "e", "w"])
        self._normalize_list(data, "ws", ["n", "r", "rn", "adr"])
<<<<<<< HEAD
        self._normalize_list(data, "unassigned_aadhars", ["s", "n", "a", "r", "rn", "adr", "id"])
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
=======
        self._normalize_list(data, "ds", ["t"])
>>>>>>> 3c8ef3700876862f09e11a95b6a2e9e767d3567e

        if data["second_schedule"]:
            # Automatically insert a newline before every 'Original' or 'Certified Copy' 
            # if they are clumped together in a single paragraph.
            val = str(data["second_schedule"])
            val = re.sub(r'(?<=\S)\s+(Original\b|Certified Copy\b)', r'\n\1', val, flags=re.IGNORECASE)
            data["second_schedule"] = val

        # Clean "Proposed" prefix from First Schedule and Second Schedule deeds
        for key in ["ds_text", "second_schedule"]:
            if data.get(key):
                val = str(data[key])
                val = re.sub(r'\bProposed\s+(Sale\s+Deed|SD|Title\s+Deed|Deed)\b', r'\1', val, flags=re.IGNORECASE)
                data[key] = val

        # Clean parentage prefixes from addresses
        for b in data.get("bs", []):
            if b.get("adr"): b["adr"] = self.clean_aadhar_address(b["adr"])
        for w in data.get("ws", []):
            if w.get("adr"): w["adr"] = self.clean_aadhar_address(w["adr"])
        for ua in data.get("unassigned_aadhars", []):
            if ua.get("adr"): ua["adr"] = self.clean_aadhar_address(ua["adr"])

        # Prefix salutations ('Mr.', 'Mrs.') to relative and witness names if missing
        for b in data.get("bs", []):
            if b.get("rn"): b["rn"] = self.normalize_relative_salutation(b["rn"], b.get("r"))
        for w in data.get("ws", []):
            if w.get("n"): w["n"] = self.normalize_name_salutation(w["n"], w.get("r"))
            if w.get("rn"): w["rn"] = self.normalize_relative_salutation(w["rn"], w.get("r"))
        for ua in data.get("unassigned_aadhars", []):
            if ua.get("n"): ua["n"] = self.normalize_name_salutation(ua["n"], ua.get("r"))
            if ua.get("rn"): ua["rn"] = self.normalize_relative_salutation(ua["rn"], ua.get("r"))

        bsign = data.get("bsign", {})
        # Strictly clear signatory details programmatically if no physical ID card (Aadhaar or PAN) was processed
        if not bsign.get("id") and not bsign.get("pan"):
            bsign = {"n":"", "a":"", "r":"", "rn":"", "pan":"", "id":""}
        else:
            if bsign.get("n"):
                bsign["n"] = self.normalize_name_salutation(bsign["n"], bsign.get("r"))
            if bsign.get("rn"):
                bsign["rn"] = self.normalize_relative_salutation(bsign["rn"], bsign.get("r"))
        data["bsign"] = self._normalize_person(bsign, ["n", "a", "r", "rn", "pan", "id"])

        self._apply_person_hints(data, borrower_hints, witness_hints)

        # Strictly clear borrower details programmatically if no physical ID card (Aadhaar or PAN) was processed
        for b in data.get("bs", []):
            if not b.get("id") and not b.get("pan"):
                for k in ["s", "n", "a", "r", "rn", "adr", "id", "pan"]:
                    b[k] = ""

        witness_names = {w["n"].casefold() for w in data["ws"] if w.get("n")}
        data["bs"] = [
            b for b in data["bs"]
            if not (b.get("n", "").casefold() in witness_names and not b.get("id"))
        ]

        self._force_count(data, "bs", ["s", "n", "a", "r", "rn", "adr", "id", "pan"], expected_borrowers)
        self._force_count(data, "ls", ["n", "a", "w", "t"], expected_loans)
        self._force_count(data, "ws", ["n", "r", "rn", "adr"], expected_witnesses)

        for loan in data.get("ls", []):
            if loan.get("a"):
                loan["a"] = self.format_indian_currency(str(loan["a"]))
            if not loan.get("w") or loan["w"].casefold() in {"amount in words", "not found"}:
                loan["w"] = self.amount_to_words(str(loan.get("a", "0")))
            
            # Normalize tenure to months programmatically
            if loan.get("t"):
                t_val = str(loan["t"]).strip()
                # Check for "years", "year", "yrs", "yr"
                match = re.search(r'(\d+)\s*(?:years?|yrs?|y/o)', t_val, re.IGNORECASE)
                if match:
                    years = int(match.group(1))
                    months = years * 12
                    loan["t"] = f"{months} Months"
                elif t_val.isdigit():
                    loan["t"] = f"{t_val} Months"

        return data

    def _build_prompt(self, bank_name, expected_borrowers, expected_loans, expected_witnesses, borrower_hints, witness_hints, current_data):
        """Build the extraction prompt string (shared by both providers)."""
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
                # Only pass names and roles context, avoid dumping huge text fields like ds_text
                previously_identified_instruction = f"""
        EXISTING ROLES (Map new documents to these names):
        {json.dumps(clean_current)}
        """

        prompt = """
        Extract data for Registered Mortgage (RM). Return ONLY a JSON object.
        """ + count_instruction + previously_identified_instruction + """
        JSON STRUCTURE:
        {
          "ad": "Loan Date (e.g. '15.04.2024')",
          "bs": [{"s":"Mr./Ms./Mrs.", "n":"Name", "a":"Age", "r":"Relation (S/o, W/o)", "rn":"Relative Name", "adr":"Address", "id":"Aadhar ID", "pan":"PAN Card No"}],
          "ls": [{"n":"LAN", "a":"Amount (digits)", "w":"Amount in words", "t":"Tenure (MUST be in Months, e.g. '180 Months')"}],
          "ps": [{"adr":"Property Address", "n":"North", "s":"South", "e":"East", "w":"West"}],
          "bsign": {"n":"Signatory Name", "a":"Age", "r":"Relation", "rn":"Relative Name", "pan":"PAN Card No", "id":"Aadhar ID"},
          "ws": [{"n":"Name", "r":"Relation", "rn":"Relative Name", "adr":"Address"}],
          "unassigned_aadhars": [{"s":"Mr/Mrs/Ms", "n":"Name", "a":"Age", "r":"Relation", "rn":"Relative", "adr":"Address (exact Aadhar print)", "id":"Aadhar Number"}],
          "second_schedule": "Documents to be collected section."
        }

        RULES:
        1. NO HALLUCINATION. If missing, use "".
        2. COUNTS: "bs" exactly selected count. "ls" selected count. "ws" exactly 2.
        3. DATES & BOUNDARIES: Extract exactly as printed.
        4. AADHAAR CARDS: Extract ALL details from uploaded Aadhaar cards (including name, age, relation, relative name, address, and ID) EXCLUSIVELY into 'unassigned_aadhars'. DO NOT map them directly to 'bs', 'ws', or 'bsign'. They will be mapped manually later.
        5. AGE: Calculate numeric age as of 2026 from YOB/DOB (e.g. '38').
        6. SALUTATIONS: Prefix names. For 'rn' (relative name) with S/o or W/o, prefix male with 'Mr.' (e.g. S/o Mr. Lal), female with 'Mrs./Ms.'.
        7. ADDRESS: Extract exact Aadhaar back address. Strip S/o, W/o, C/o prefixes from the start.
        8. AUTHORISED SIGNATORY (bsign): STRICTLY DO NOT extract, infer, or fill any bank signatory details (including name 'n', age 'a', relation 'r', relative name 'rn', pan 'pan', or id 'id') from legal reports, title search reports, or sanction letters under any circumstances. You must ONLY extract these details if a physical ID card (Aadhaar card or PAN card) belonging to the bank signatory is present/uploaded in the files. If no physical ID card for the bank signatory is uploaded/present, you MUST return the entire 'bsign' dictionary completely empty/blank: {"n":"", "a":"", "r":"", "rn":"", "pan":"", "id":""}.
        9. SCHEDULE: For "second_schedule", if ICICI extract only 'Last Sale Deed' (or equivalent title deed) details, else extract all items that start with the word 'Original' (e.g. 'Original Sale Deed', 'Original Title Deed').
        10. INCREMENTAL: Do not re-extract existing fields. Focus on new documents.
        11. TENURE: Tenure MUST always be in months. Convert years to months if necessary (e.g. '15 Years' -> '180 Months').
        12. PAN CARDS: Extract PAN Card numbers (10 alphanumeric characters, e.g. ABCDE1234F) into 'pan' field for borrowers ('bs') or bank signatory ('bsign') if a PAN card image or document is uploaded/present.
        13. BORROWER DETAILS: STRICTLY DO NOT extract, infer, or fill ANY borrower details (including borrower name 'n', salutation 's', age 'a', relation 'r', relative name 'rn', address 'adr', aadhar ID 'id', and 'pan') from non-ID documents (like legal reports, title search reports, or sanction letters) because legal/sanction documents can be incorrect. The entire 'bs' list MUST be returned completely empty/blank (e.g. all fields as "") initially. Borrower details (including borrower names) must ONLY be populated when their official physical Aadhaar card or PAN card is uploaded, in which case they will be processed into 'unassigned_aadhars' or 'pan' and manually mapped.
        """
        return prompt

    def _build_sd_prompt(self, expected_sellers, expected_buyers, expected_witnesses, seller_hints, buyer_hints, current_data):
        """Build the extraction prompt string for Sale Deeds (Hindi/Devanagari outputs)."""
        count_instruction = f"""
        CASE: DocType: SaleDeed, Sellers:{expected_sellers if expected_sellers is not None else 'all'}, Buyers:{expected_buyers if expected_buyers is not None else 'all'}, Witnesses:{expected_witnesses}.
        Hints: Sellers: {seller_hints.strip() or 'none'}, Buyers: {buyer_hints.strip() or 'none'}
        """

        previously_identified_instruction = ""
        if current_data:
            clean_current = {}
            for k in ['sellers', 'buyers', 'ws', 'ps', 'chain']:
                if k in current_data and current_data[k]:
                    clean_current[k] = [{kk: vv for kk, vv in p.items() if vv} for p in current_data[k]]
                    clean_current[k] = [p for p in clean_current[k] if p]
            if any(clean_current.values()):
                previously_identified_instruction = f"""
        EXISTING ROLES (Map new documents to these names):
        {json.dumps(clean_current)}
        """

        prompt = """
        Extract data for Sale Deed. Return ONLY a JSON object.
        """ + count_instruction + previously_identified_instruction + """
        JSON STRUCTURE:
        {
          "sellers": [{"s":"Mr./Ms./Mrs.", "n":"Name (in Hindi/Devanagari)", "a":"Age", "r":"Relation (S/o, W/o)", "rn":"Relative Name (in Hindi/Devanagari)", "caste":"Caste/Religion (in Hindi, e.g. 'fgUnq' / 'हिन्दू')", "adr":"Address (in Hindi/Devanagari)", "id":"Aadhar ID", "pan":"PAN Card No"}],
          "buyers": [{"s":"Mr./Ms./Mrs.", "n":"Name (in Hindi/Devanagari)", "a":"Age", "r":"Relation (S/o, W/o)", "rn":"Relative Name (in Hindi/Devanagari)", "caste":"Caste/Religion (in Hindi)", "adr":"Address (in Hindi/Devanagari)", "id":"Aadhar ID", "pan":"PAN Card No"}],
          "ps": [{"flat_no":"Flat/Plot No", "floor":"Floor", "building":"Building/Project Name", "adr":"Property Address (in Hindi)", "area":"Super Built-up Area (digits only)", "area_unit":"Area Unit (e.g. 'varg foot', 'varg gaj', 'varg meter')", "parking":"Common parking presence (e.g. 'Yes' / 'No')", "e":"East Boundary (in Hindi)", "w":"West Boundary (in Hindi)", "n":"North Boundary (in Hindi)", "s":"South Boundary (in Hindi)"}],
          "ws": [{"n":"Name (in Hindi)", "r":"Relation", "rn":"Relative Name (in Hindi)", "adr":"Address (in Hindi)"}],
          "unassigned_aadhars": [{"s":"Mr/Mrs/Ms", "n":"Name (in Hindi)", "a":"Age", "r":"Relation", "rn":"Relative (in Hindi)", "adr":"Address (in Hindi)", "id":"Aadhar Number"}],
          "chain": [{"seller":"Prior Seller Name (in Hindi)", "buyer":"Prior Buyer Name (in Hindi)", "date":"Registry Date (e.g. '23.04.2018')", "book":"Book No", "vol":"Volume/Jild No", "page":"Page No", "kram":"Registration/Kram No"}]
        }

        RULES:
        1. HINDI TRANSLITERATION: You must extract and output all Name fields, Relative Names, Caste/Religion, Address fields, Boundaries, and prior owner names in Devanagari Hindi characters (e.g. "विवेक सक्सेना", "पुत्र", "हिन्दू", "अजमेर रोड"). If the source document has these names or addresses in English, you MUST transliterate them to standard Devanagari Hindi script.
        2. NO HALLUCINATION. If missing, use "".
        3. COUNTS: "sellers" exactly selected count. "buyers" exactly selected count. "ws" exactly 2.
        4. AADHAAR CARDS: Extract ALL details from uploaded Aadhaar cards (including name, age, relation, relative name, address, and ID) EXCLUSIVELY into 'unassigned_aadhars'. DO NOT map them directly to 'sellers', 'buyers', 'ws'. They will be mapped manually later.
        5. AGE: Calculate numeric age as of 2026 from YOB/DOB (e.g. '58').
        6. SALUTATIONS: Prefix names. For 'rn' (relative name) with S/o or W/o, prefix male with 'Mr.' (e.g. S/o Mr. Lal), female with 'Mrs./Ms.'.
        7. ADDRESS: Extract exact Aadhaar back address. Strip S/o, W/o, C/o prefixes from the start.
        8. PROPERTY & AREA: Extract property details, area size, and exact area unit (e.g., "वर्ग फुट" for Sq Ft, "वर्ग गज" for Sq Yards, "वर्ग मीटर" for Sq Meters) as stated in Pattas, Site Plans, previous deeds, or ATS.
        9. BOUNDARIES: Extract poorv (East), paschim (West), uttar (North), dakshin (South) boundaries in Devanagari Hindi.
        10. CHAIN OF TITLE: Scan the previous registry copies / previous sale deeds to find the historical chain: who sold to whom, the transaction date, and the registry metadata (Book number, Kram number, Volume/Jild number, Page number). Extract these chronologically.
        11. PAN CARDS: Extract PAN Card numbers (10 alphanumeric characters) into 'pan' field for sellers or buyers if a PAN card image or document is uploaded.
        """
        return prompt

    # ------------------------------------------------------------------
    # Extraction Logic (Google Gemini)
    # ------------------------------------------------------------------
    def extract_with_ai(self, file_paths, selected_model, bank_name="", expected_borrowers=None,
                        expected_loans=None, expected_witnesses=2, borrower_hints="",
                        witness_hints="", current_data=None, doc_type="RM",
                        expected_sellers=None, expected_buyers=None, seller_hints="", buyer_hints=""):
        """Extract data from files using Google Gemini API with failover key rotation retry."""
        if not self.api_keys:
            return {"error": "Gemini API Keys Missing"}

        from google.genai import types

        contents = []
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            mime_type, _ = mimetypes.guess_type(path)
            if ext in ['.jpg', '.jpeg', '.png', '.pdf']:
                with open(path, 'rb') as f:
                    raw = f.read()
                contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type or 'application/octet-stream'))
            elif ext == '.txt':
                with open(path, 'r', encoding='utf-8') as f:
                    contents.append(types.Part.from_text(text=f.read()))

<<<<<<< HEAD
        # Select prompt based on active document type
        if doc_type == "SD":
            prompt = self._build_sd_prompt(expected_sellers, expected_buyers,
                                           expected_witnesses, seller_hints, buyer_hints, current_data)
        else:
            prompt = self._build_prompt(bank_name, expected_borrowers, expected_loans,
                                        expected_witnesses, borrower_hints, witness_hints, current_data)
                                    
        attempts = 0
        max_attempts = len(self.api_keys)
        last_error = "Unknown Error"
        
        while attempts < max_attempts:
            if not self.client:
                self._init_client()
            if not self.client:
                return {"error": "Gemini API Client Initialization Failed"}
                
            try:
                final_contents = contents + [types.Part.from_text(text=prompt)]
                response = self.client.models.generate_content(
                    model=selected_model,
                    contents=final_contents
                )
                match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    return self._normalize_response(data, expected_borrowers, expected_loans,
                                                    expected_witnesses, borrower_hints, witness_hints,
                                                    doc_type=doc_type, expected_sellers=expected_sellers,
                                                    expected_buyers=expected_buyers, seller_hints=seller_hints,
                                                    buyer_hints=buyer_hints)
                return {"error": "AI returned non-JSON response", "raw": response.text}
            except Exception as e:
                last_error = str(e)
                print(f"[FAILOVER WARNING] Gemini extraction failed with key index {self.active_key_index}: {last_error}")
                self._rotate_key()
                attempts += 1
                
        return {"error": f"Gemini AI Failover Error: All API keys failed. Last error: {last_error}"}
=======
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
>>>>>>> 3c8ef3700876862f09e11a95b6a2e9e767d3567e
