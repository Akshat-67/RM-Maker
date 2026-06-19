import re
import os
import base64
import mimetypes
import json
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
    normalize_relation_prefix
)

class RMDataExtractor:
    def __init__(self, api_key=None, api_keys=None, provider="gemini", *args, **kwargs):
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

    def get_available_models(self):
        if not self.client:
            self._init_client()
        if not self.client:
            return ["gemini-2.5-flash"]
        try:
            models_list = self.client.models.list()
            valid_models = []
            for m in models_list:
                try:
                    if m.name:
                        valid_models.append(m.name)
                except Exception:
                    pass
            return valid_models if valid_models else ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]
        except Exception as e:
            print(f"[Extractor Warning] Failed to query Gemini models list: {e}")
            return ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]

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

    def extract_with_ai(self, file_paths, selected_model, bank_name="", expected_borrowers=None,
                        expected_loans=None, expected_witnesses=2, borrower_hints="", witness_hints="",
                        current_data=None, **kwargs):
        """Extract data from files using Google Gemini API."""
        if not self.api_keys:
            return {"error": "Gemini API Keys Missing"}

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
                
            @retry(
                wait=wait_exponential(multiplier=1, min=4, max=10),
                stop=stop_after_attempt(3),
                retry=retry_if_exception_type(APIError)
            )
            def _call_api_with_retry(client, model, contents):
                return client.models.generate_content(model=model, contents=contents)

            try:
                final_contents = contents + [types.Part.from_text(text=prompt)]
                response = _call_api_with_retry(self.client, selected_model, final_contents)
                match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    return self._normalize_response(data, expected_borrowers, expected_loans,
                                                    expected_witnesses, borrower_hints, witness_hints)
                return {"error": "AI returned non-JSON response", "raw": response.text}
            except Exception as e:
                last_error = str(e)
                print(f"[FAILOVER WARNING] Gemini extraction failed: {last_error}")
                self._rotate_key()
                attempts += 1
                
        return {"error": f"Gemini AI Failover Error: All API keys failed. Last error: {last_error}"}

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
          "ad": "Loan Date (e.g. '15.04.2024')",
          "bs": [{"s":"Mr./Ms./Mrs.", "n":"Name", "a":"Age", "relation_text":"Complete Relation Phrase (e.g. 'S/o Mr. Vinod Malhotra')", "adr":"Address", "id":"Aadhar ID", "pan":"PAN Card No"}],
          "ls": [{"n":"LAN", "a":"Amount (digits)", "w":"Amount in words", "t":"Tenure (MUST be in Months, e.g. '180 Months')"}],
          "ps": [{"adr":"Property Address", "lease_deed_no":"Lease Deed Number", "n":"North", "s":"South", "e":"East", "w":"West"}],
          "bsign": {"n":"Signatory Name", "a":"Age", "relation_text":"Complete Relation Phrase (e.g. 'S/o Mr. Rajesh Nama')", "pan":"PAN Card No", "id":"Aadhar ID"},
          "ws": [{"n":"Name", "relation_text":"Complete Relation Phrase (e.g. 'S/o Mr. Gopal Singh')", "adr":"Address"}],
          "unassigned_aadhars": [{"s":"Mr/Mrs/Ms", "n":"Name", "a":"Age", "relation_text":"Complete Relation Phrase", "adr":"Address (exact Aadhar print)", "id":"Aadhar Number"}],
          "second_schedule": "Documents to be collected section."
        }

        RULES:
        1. NO HALLUCINATION. If missing, use "".
        2. COUNTS: "bs" exactly selected count. "ls" selected count. "ws" exactly 2.
        3. DATES & BOUNDARIES: Extract exactly as printed.
        4. AADHAAR CARDS: Extract details from uploaded Aadhaar cards (including name, age, relation phrase, address, and ID) EXCLUSIVELY into 'unassigned_aadhars'. DO NOT map them directly to 'bs', 'ws', or 'bsign'. They will be mapped manually later.
        4b. WITNESS OCR ISOLATION: STRICTLY DO NOT extract witness details (names, addresses, Aadhaar, relation data) into 'unassigned_aadhars' or any other OCR sections. If an Aadhaar card belongs to a witness, do not extract it or include it in 'unassigned_aadhars'.
        5. AGE: Calculate numeric age as of 2026 from YOB/DOB (e.g. '38').
        6. SALUTATIONS: Separate salutations from names. Use 's' field for 'Mr./Ms./Mrs.' and DO NOT prefix the name in the 'n' field or relative name in the 'relation_text' field with any salutation. Use 'Mr.' (with one dot) for males, 'Mrs.' for females.
        7. ADDRESS & RELATIONS: The first line on the back of an Aadhaar card is often the relation (e.g. S/o, C/o, W/o, D/o). YOU MUST SEPARATE THIS. Put the relation entirely in `relation_text` and only put the actual address in `adr`.
        7b. STRICT RELATION FORMATTING: ALWAYS format relations using exact English (e.g. 'S/o Mr. ...', 'W/o Mr. ...', 'D/o Mr. ...'). DO NOT leave them as 'Son of' or 'Wife of' in the extracted output.
        8. AUTHORISED SIGNATORY (bsign): STRICTLY DO NOT extract, infer, or fill any bank signatory details from legal reports or sanction letters. ONLY extract if a physical ID card (Aadhaar or PAN) belonging to the bank signatory is present.
        9. SCHEDULE: For "second_schedule", extract all items that start with 'Original' or 'Endorsed copy'.
        10. INCREMENTAL: Do not re-extract existing fields. Focus on new documents.
        11. TENURE: Always in months.
        12. PAN CARDS: Extract 10-char alphanumeric PAN into 'pan' field.
        13. BORROWER DETAILS: STRICTLY DO NOT extract borrower details from non-ID documents. 'bs' list must be empty initially. Populate from Aadhaar/PAN processed into 'unassigned_aadhars' and manually map.
        14. MULTI-LOAN: If multiple sanction letters are present, extract ALL of them into the 'ls' list.
        15. PRECISION: EXTRACT ALL DIGITS OF THE LOAN AMOUNT. DO NOT MISS ANY NUMBERS. (Example: If it is 56,782, extract exactly 56782, NOT 5782).
        16. MANDATORY ENGLISH SCRIPT: You MUST use English script for ALL descriptive text including names ('n'), relations ('relation_text'), and addresses ('adr'). DO NOT USE HINDI/Devanagari script for these fields.
            - Correct Name: 'Ramkumar Sharma' (NOT 'रामकुमार शर्मा')
            - Correct Address: '123, Malviya Nagar, Jaipur' (NOT '१२३, मालवीय नगर, जयपुर')
            - Correct Relation: 'S/o Mr. Banwari Lal' (NOT 'पुत्र श्री बनवारी लाल')
        17. ENGLISH SOURCE PRIORITY: Always prefer extracting names and addresses natively from English text in the uploaded documents (e.g., the English side of an Aadhaar card). The English print is much more reliable. Only fallback to translating/transliterating Hindi text into English if English text is completely unavailable.
        """
        return prompt

    def _normalize_response(self, data, expected_borrowers, expected_loans, expected_witnesses, borrower_hints, witness_hints):
        if not isinstance(data, dict):
            return {"error": "AI returned JSON, but it was not an object"}

        data["ad"] = format_date_with_dots(data.get("ad", ""))
        self._normalize_list(data, "bs", ["s", "n", "a", "relation_text", "adr", "id", "pan"])
        self._normalize_list(data, "ls", ["n", "a", "w", "t"])
        self._normalize_list(data, "ps", ["adr", "lease_deed_no", "n", "s", "e", "w"])
        self._normalize_list(data, "ws", ["n", "relation_text", "adr"])
        self._normalize_list(data, "unassigned_aadhars", ["s", "n", "a", "relation_text", "adr", "id"])

        if "bsign" in data and isinstance(data["bsign"], dict):
            bsign = data["bsign"]
            for f in ["n", "a", "relation_text", "pan", "id"]:
                bsign[f] = str(bsign.get(f, "")).strip()
        else:
            data["bsign"] = {"n":"", "a":"", "relation_text":"", "pan":"", "id":""}

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
                data["ds_text"] = m.group(1).strip()
            elif raw_ds:
                data["ds_text"] = raw_ds.strip()
            else:
                data["ds_text"] = ""

        data["second_schedule"] = "" if data.get("second_schedule") is None else str(data.get("second_schedule", "")).strip()

        if data["second_schedule"]:
            val = str(data["second_schedule"])
            val = re.sub(r'(?<=\S)\s+(Original\b|Certified Copy\b)', r'\n\1', val, flags=re.IGNORECASE)
            data["second_schedule"] = val

        for key in ["ds_text", "second_schedule"]:
            if data.get(key):
                val = str(data[key])
                val = re.sub(r'\bProposed\s+(Sale\s+Deed|SD|Title\s+Deed|Deed)\b', r'\1', val, flags=re.IGNORECASE)
                data[key] = val

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
            if ua.get("relation_text"): ua["relation_text"] = normalize_relation_prefix(ua["relation_text"], "RM")
            if ua.get("n"): ua["n"] = normalize_name_salutation(ua["n"], ua.get("relation_text"))

        def split_sal(name_with_sal):
            m = re.match(r'^((?:Mr|Mrs|Ms|Shri|Smt|Sh)\.)\s*(.*)', name_with_sal, re.IGNORECASE)
            if m:
                return m.group(1), m.group(2).strip()
            return "", name_with_sal

        for b in data.get("bs", []):
            if b.get("n"):
                sal, name = split_sal(b["n"])
                b["s"] = sal
                b["n"] = name

        bsign = data.get("bsign", {})
        if not bsign.get("id") and not bsign.get("pan"):
            bsign = {"n":"", "a":"", "r":"", "rn":"", "relation_text":"", "pan":"", "id":""}
        else:
            if bsign.get("relation_text"):
                norm_rel = normalize_relation_prefix(bsign["relation_text"], "RM")
                bsign["relation_text"] = norm_rel
                r, rn = parse_relation_text(norm_rel)
                bsign["r"] = r
                bsign["rn"] = rn
            if bsign.get("n"):
                bsign["n"] = normalize_name_salutation(bsign["n"], bsign.get("r"))
        data["bsign"] = self._normalize_person(bsign, ["n", "a", "r", "rn", "relation_text", "pan", "id"])

        self._apply_person_hints(data, borrower_hints, witness_hints)

        for b in data.get("bs", []):
            if not b.get("id") and not b.get("pan"):
                for k in ["s", "n", "a", "r", "rn", "relation_text", "adr", "id", "pan"]:
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

        self._force_count(data, "bs", ["s", "n", "a", "r", "rn", "relation_text", "adr", "id", "pan"], expected_borrowers)
        self._force_count(data, "ls", ["n", "a", "w", "t"], expected_loans)
        self._force_count(data, "ws", ["n", "r", "rn", "relation_text", "adr"], expected_witnesses)

        for loan in data.get("ls", []):
            if loan.get("a"):
                loan["a"] = format_indian_currency(str(loan["a"]))
            if not loan.get("w") or loan["w"].casefold() in {"amount in words", "not found"}:
                loan["w"] = amount_to_words(str(loan.get("a", "0")))
            
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
            clean_item = {f: str(item.get(f, "")).strip() for f in fields}
            if "date" in clean_item:
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
                nvidia_key = "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"
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

        @retry(
            wait=wait_exponential(multiplier=1, min=4, max=10),
            stop=stop_after_attempt(3),
            retry=retry_if_exception_type(APIError)
        )
        def _call_api_with_retry(client, model, contents):
            return client.models.generate_content(model=model, contents=contents)

        for current_model in fallback_queue:
            attempts = 0
            max_attempts = len(self.api_keys)
            
            print(f"[DIAGNOSTIC] raw_generate: Attempting model {current_model}...")

            while attempts < max_attempts:
                if not self.client:
                    self._init_client()
                if not self.client:
                    print(f"[DIAGNOSTIC] raw_generate: Client init failed for key index {self.active_key_index}")
                    return None

                try:
                    contents = [types.Part.from_text(text=prompt)]
                    response = _call_api_with_retry(self.client, current_model, contents)
                    if response and response.text:
                        return response.text
                except Exception as e:
                    print(f"[FAILOVER WARNING] Gemini raw_generate failed ({current_model}, Key {self.active_key_index}): {e}")
                    self._rotate_key()
                    attempts += 1
            
            print(f"[FAILOVER] Model {current_model} exhausted all keys. Trying next fallback...")
        # Fallback to NVIDIA NIM Llama 3.1 8B
        print("[FAILOVER] Gemini exhausted. Attempting fallback to NVIDIA NIM Llama 3.1 8B...")
        try:
            import requests
            nvidia_key = "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"
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
