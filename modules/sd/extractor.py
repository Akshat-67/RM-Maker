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
    format_date_with_dots,
    normalize_relation_prefix
)

class SDDataExtractor:
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
            return [m.name for m in models_list if "generateContent" in m.supported_developer_methods]
        except Exception as e:
            print(f"[Extractor Warning] Failed to query Gemini models list: {e}")
            return ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]

    @staticmethod
    def is_flat_property(ps_dict):
        if not ps_dict: return False
        return bool(
            ps_dict.get("flat_no") 
            or ps_dict.get("floor")
            or "Unit" in str(ps_dict.get("property_portion", ""))
            or "फ्लैट" in str(ps_dict.get("plot_no", ""))
            or "Flat" in str(ps_dict.get("plot_no", ""))
        )

    def generate_full_property_address(self, prop, doc_type="SD", property_type="Plot"):
        """Compiles a formal property address string for SD from extracted fields."""
        if not isinstance(prop, dict): return ""

        adr = str(prop.get("adr", "")).strip()
        if adr:
            if property_type == "Flat":
                res = adr
                if res.endswith("राजस्थान"):
                    res += " में स्थित है"
                const_area = str(prop.get("const_area", "")).strip()
                const_unit = str(prop.get("const_unit", "") or prop.get("unit", "") or "वर्गफीट").strip()
                if const_area and "सुपर बिल्टअप एरिया" not in res:
                    res += f", जिसका सुपर बिल्टअप एरिया {const_area} {const_unit} है"
                return res
            elif property_type == "Plot":
                match = re.search(r'((?:प्लाट|प्लॉट|Plot|Khasra|खसरा)\s*(?:नं|No)?\.?\s*[-&]?[^\s,]+.*)$', adr, re.IGNORECASE)
                if match:
                    res = match.group(1).strip()
                    if "आवासीय" in adr and not res.startswith("आवासीय"):
                        res = "आवासीय " + res
                    return res

        def s(key): return str(prop.get(key, "")).strip()

        plot_no       = s("plot_no")
        flat_no       = s("flat_no")
        floor         = s("floor")
        building_name = s("building_name")
        project_name  = s("project_name")
        scheme        = s("scheme")
        village       = s("village")
        tehsil        = s("tehsil")
        dist          = s("dist")
        landmark      = s("landmark")
        state         = s("state") or "राजस्थान"
        const_area    = s("const_area")
        const_unit    = s("const_unit") or s("unit") or "वर्गफीट"
        ward          = s("ward")
        parking_type  = s("parking_type")

        components = []

        is_flat = property_type == "Flat" or SDDataExtractor.is_flat_property(prop)

        if is_flat:
            # Use explicit flat_no, NO fallback to plot_no
            flat_raw = re.sub(
                r'^(Flat\s*No\.?\s*|फ्लैट\s*नं\.?\s*|आवासीय\s*फ्लैट\s*नं\.?\s*)',
                '', flat_no, flags=re.IGNORECASE
            ).strip()
            if flat_raw:
                components.append(f"आवासीय फ्लैट नम्बर {flat_raw}")
            
            if floor:
                components.append(floor)
            if building_name:
                components.append(building_name)
            if project_name and project_name != building_name:
                components.append(f"प्रोजेक्ट {project_name}")
            
            if plot_no:
                plot_raw = re.sub(
                    r'^(Plot\s*No\.?\s*|प्लॉट\s*नं\.?\s*|प्लाट\s*नं\.?\s*)',
                    '', plot_no, flags=re.IGNORECASE
                ).strip()
                if plot_raw:
                    components.append(f"प्लाट नं. {plot_raw}")
        else:
            plot_raw = re.sub(
                r'^(Plot\s*No\.?\s*|प्लॉट\s*नं\.?\s*|प्लाट\s*नं\.?\s*)',
                '', plot_no, flags=re.IGNORECASE
            ).strip()
            if plot_raw:
                components.append(f"आवासीय प्लाट नं. {plot_raw}")

        if scheme:
            scheme_raw = re.sub(r'^(योजना\s*)', '', scheme, flags=re.IGNORECASE).strip()
            components.append(scheme_raw if scheme_raw else scheme)
        if village:
            village_raw = re.sub(r'^(ग्राम\s*)', '', village, flags=re.IGNORECASE).strip()
            components.append(f"ग्राम {village_raw}" if village_raw else village)
        if tehsil:
            tehsil_raw = re.sub(r'^(तहसील\s*)', '', tehsil, flags=re.IGNORECASE).strip()
            components.append(f"तहसील {tehsil_raw}" if tehsil_raw else tehsil)
        if landmark:
            components.append(landmark)
        if dist:
            dist_raw = re.sub(r'^(जिला\s*)', '', dist, flags=re.IGNORECASE).strip()
            components.append(f"जिला {dist_raw}" if dist_raw else dist)
        if state:
            components.append(state)

        res = ", ".join([c for c in components if c])

        # Append super built-up area for flats
        if is_flat and const_area:
            if "सुपर बिल्टअप एरिया" not in res:
                res += f", जिसका सुपर बिल्टअप एरिया {const_area} {const_unit} है"

        return res

    def generate_plot_address(self, prop):
        """Compiles a plot-level only description (used for dimension paragraphs)."""
        if not isinstance(prop, dict): return ""
        def s(key): return str(prop.get(key, "")).strip()
        
        plot_no = s("plot_no")
        scheme = s("scheme")
        village = s("village")
        tehsil = s("tehsil")
        dist = s("dist")
        state = s("state") or "राजस्थान"
        
        plot_raw = re.sub(r'^(Plot\s*No\.?\s*|प्लॉट\s*नं\.?\s*|प्लाट\s*नं\.?\s*)', '', plot_no, flags=re.IGNORECASE).strip()
        
        components = []
        if plot_raw: components.append(f"आवासीय प्लाट नं. {plot_raw}")
        if scheme: components.append(scheme)
        if village: components.append(f"ग्राम {village}" if "ग्राम" not in village else village)
        if tehsil: components.append(f"तहसील {tehsil}" if "तहसील" not in tehsil else tehsil)
        if dist: components.append(f"जिला {dist}" if "जिला" not in dist else dist)
        if state: components.append(state)
        
        return ", ".join(components)

    def generate_dimension_text(self, prop):
        """Compiles E-W and N-S dimensions into a legal Hindi sentence."""
        ew = str(prop.get("length_ew", "")).strip()
        ns = str(prop.get("length_ns", "")).strip()
        area = str(prop.get("land_area", "")).strip()
        unit = str(prop.get("unit", "वर्ग गज")).strip()
        
        parts = []
        if ew and ns:
            parts.append(f"जिसकी नाप पूर्व से पश्चिम {ew} एवं उत्तर से दक्षिण {ns} है")
        
        if area:
            parts.append(f"जिसका कुल क्षेत्रफल {area} {unit} है")
        
        res = ", ".join(parts).strip()
        return res

    def generate_boundary_text(self, prop):
        """Compiles North, South, East, West boundaries into a structured Hindi block."""
        n = str(prop.get("n", "")).strip()
        s = str(prop.get("s", "")).strip()
        e = str(prop.get("e", "")).strip()
        w = str(prop.get("w", "")).strip()
        
        if not (n or s or e or w):
            return ""
            
        parts = []
        if e: parts.append(f"पूर्व की ओर {e}")
        if w: parts.append(f"पश्चिम की ओर {w}")
        if n: parts.append(f"उत्तर की ओर {n}")
        if s: parts.append(f"तथा दक्षिण की ओर {s}")
        
        return f"जिसकी चारों सीमाओें में {', '.join(parts)} स्िथत है"

    def extract_title_chain(self, file_paths, model_name="gemini-2.5-flash"):
        """Dedicated extraction path for parsing Title Chain history from Legal Reports."""
        if not self.api_keys:
            return {"error": "Gemini API Keys Missing"}

        contents = []
        txt_files = [p for p in file_paths if p.lower().endswith('.txt')]
        effective_paths = txt_files if txt_files else file_paths
        for path in effective_paths:
            ext = os.path.splitext(path)[1].lower()
            mime_type, _ = mimetypes.guess_type(path)
            if ext in ['.jpg', '.jpeg', '.png', '.pdf']:
                with open(path, 'rb') as f:
                    raw = f.read()
                contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type or 'application/octet-stream'))
            elif ext == '.txt':
                with open(path, 'r', encoding='utf-8') as f:
                    contents.append(types.Part.from_text(text=f.read()))

        if not contents:
            return {"error": "No valid files to process."}

        prompt = """
        CRITICAL MISSION: You are a senior legal analyst reviewing a Title Search Report (TSR) or chain of documents.
        Your task is to extract the CHRONOLOGICAL History of Title / Chain of Ownership.

        Map each transfer event strictly to ONE of the following event_types:
        - ALLOTMENT: Original grant, Patta, Lease Deed, Allotment Letter by an Authority/Society.
        - CONSTRUCTION: Builder/Owner constructs building, apartments, or flats.
        - SALE_DEED: Sale Deed, Conveyance Deed, Sub-lease Deed for consideration.
        - TRANSFER: Any other transfer (e.g. Gift Deed, Relinquishment Deed, Release Deed, Haktyag, Will, Mutation, Transfer Letter, Transfer Order).

        DO NOT extract or use GIFT_DEED, RELINQUISHMENT, DEATH, WILL, PARTITION, or COURT_ORDER as separate event types. Map them to TRANSFER instead.

        For each event, extract:
        - event_type (from list above)
        - document_name: The Hindi translation of the document type (e.g., 'विक्रय पत्र', 'पट्टा विलेख', 'हस्तान्तरण पत्र', 'निर्माण पत्र')
        - document_number: The exact patta/document number (e.g. 'डी-2341')
        - date: DD.MM.YYYY (DO NOT HALLUCINATE. If no date is found, leave blank "")
        - executant_name: Seller/Principal/Authority/Builder in Unicode Hindi
        - claimant_name: Buyer/Attorney/Allottee in Unicode Hindi
        - is_registered: true or false (boolean)
        - reg_office: Registrar Office in Unicode Hindi
        - reg_date: DD.MM.YYYY
        - reg_book, reg_vol, reg_page: Registration details (numbers only)
        - reg_no: The 15-digit E-Panjiyan sequence/receipt number (e.g. '201803021103534', labeled 'क्रम संख्या' or 'Receipt No')
        - reg_add_book, reg_add_vol: Additional Book details
        - reg_add_page: Additional Book page number or page range (e.g., '1026-1039', '494-507'). DO NOT truncate page ranges to a single page number. Extract the full range if present in the text (e.g., '1026 to 1039' should be extracted as '1026-1039').
        - consideration_amount: Numeric digits only (DO NOT HALLUCINATE)
        - project_name: Project name for CONSTRUCTION events only (Unicode Hindi, e.g. 'परियोजना का नाम')
        - unit_number: Unit/Flat number for CONSTRUCTION events only (Unicode Hindi, e.g. 'एस-1')
        - confidence: Rate the extraction quality as "High", "Medium", or "Low" based on text clarity.
        - source_text: Provide the exact 1-2 sentences from the English report that proves this event.

        Return ONLY a JSON object with a single key "title_chain" containing the array of events sorted chronologically (oldest first).
        
        CONSTRUCTION EVENT RULES:
        - If the report/TSR mentions construction, flats constructed, units numbered, project named, or scheme named, you MUST create a CONSTRUCTION event. Do not discard these paragraphs.
        - For a CONSTRUCTION event, capture the 'project_name' (e.g. 'परियोजना का नाम') and 'unit_number' (e.g. 'एस-1') where available.
        - Specifically, if a construction paragraph in the documents contains language about naming/identifying the building or project (such as "तथा उसका नाम ... रख दिया", "परियोजना का नाम ... रखा गया", "अपार्टमेंट का नाम ... रखा", "नामकरण"), you MUST extract that exact project/building name as the project_name and store it on the CONSTRUCTION event.
        - The 'executant_name' for CONSTRUCTION should be the builder/owner who constructed the units (e.g., 'मैसर्स एक्सवाईजेड कंस्ट्रक्शन जरिये प्रोपराइटर श्री एबीसी पुत्र श्री एक्सवाईजेड'). DO NOT hallucinate the claimant.

        TRANSFER EVENT RULES:
        - If the report/TSR contains 'Transfer Deed', 'Transfer Letter', or 'Transfer Order', you MUST create a TRANSFER event.

        CRITICAL NAME EXTRACTION RULES:
        - Names in executant_name and claimant_name MUST be EXACT, COMPLETE, and in UNICODE HINDI (Hindi script).
        - Preserve all proprietor and relative/parent details in the name field (e.g. 'मैसर्स एक्सवाईजेड कंस्ट्रक्शन जरिये प्रोपराइटर श्री एबीसी पुत्र श्री एक्सवाईजेड'). Do not trim or truncate these.

        CRITICAL RULES FOR TITLE CHAIN:
        1. DO NOT SKIP ANY TRANSFERS. If A sold to B, and B sold to C, you MUST extract exactly all events!
        2. DO NOT HALLUCINATE DATES OR AMOUNTS. If the exact date or exact consideration amount is not explicitly written in the text for that specific transfer event, leave it blank "". Do not copy dates or amounts from other transfers.
        3. DO NOT INCLUDE CONVERSATIONAL TEXT. ONLY VALID JSON.
        """

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
                response = _call_api_with_retry(self.client, model_name.replace("models/", "", 1) if model_name else "gemini-2.5-flash", final_contents)
                
                raw = response.text
                m = re.search(r'```json\s*(.*?)\s*```', raw, re.DOTALL | re.IGNORECASE)
                if m: raw = m.group(1)
                else:
                    m = re.search(r'(\{.*\})', raw, re.DOTALL)
                    if m: raw = m.group(1)
                
                data = json.loads(raw)
                if "title_chain" not in data or not isinstance(data["title_chain"], list):
                    data["title_chain"] = []
                else:
                    self._normalize_list(data, "title_chain", [
                        "event_type", "document_name", "document_number", "date", "consideration_amount", 
                        "executant_name", "claimant_name", "reg_office", "reg_date", 
                        "reg_book", "reg_vol", "reg_page", "reg_no", "reg_add_book", "reg_add_vol", "reg_add_page", 
                        "book_no", "volume_no", "page_no", "additional_book_no", "additional_volume_no", "additional_page_range",
                        "confidence", "source_text", "is_registered", "project_name", "unit_number", "field_sources", "event_property_type"
                    ])
                    self.heal_title_chain_from_ocr(data["title_chain"], file_paths)
                    
                return data

            except Exception as e:
                print(f"[FAILOVER WARNING] Gemini extract_title_chain failed (Key {self.active_key_index}): {e}")
                last_error = str(e)
                self._rotate_key()
                attempts += 1

        return {"error": f"AI Extraction Failed after {max_attempts} attempts. Last error: {last_error}"}

    def extract_with_ai(self, file_paths, selected_model, expected_sellers=None, expected_buyers=None,
                        expected_witnesses=2, seller_hints="", buyer_hints="", witness_hints="",
                        current_data=None, **kwargs):
        """Extract data from files using Google Gemini API."""
        if not self.api_keys:
            return {"error": "Gemini API Keys Missing"}

        contents = []
        txt_files = [p for p in file_paths if p.lower().endswith('.txt')]
        effective_paths = txt_files if txt_files else file_paths
        for path in effective_paths:
            ext = os.path.splitext(path)[1].lower()
            mime_type, _ = mimetypes.guess_type(path)
            if ext in ['.jpg', '.jpeg', '.png', '.pdf']:
                with open(path, 'rb') as f:
                    raw = f.read()
                contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type or 'application/octet-stream'))
            elif ext == '.txt':
                with open(path, 'r', encoding='utf-8') as f:
                    contents.append(types.Part.from_text(text=f.read()))

        prompt = self._build_sd_prompt(expected_sellers, expected_buyers, expected_witnesses, current_data)
                                    
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
                    normalized_data = self._normalize_sd_response(data, expected_sellers, expected_buyers, expected_witnesses)
                    if "title_chain" in normalized_data and isinstance(normalized_data["title_chain"], list):
                        self.heal_title_chain_from_ocr(normalized_data["title_chain"], file_paths)
                    return normalized_data
                return {"error": "AI returned non-JSON response", "raw": response.text}
            except Exception as e:
                last_error = str(e)
                print(f"[FAILOVER WARNING] Gemini extraction failed: {last_error}")
                self._rotate_key()
                attempts += 1
                
        return {"error": f"Gemini AI Failover Error: All API keys failed. Last error: {last_error}"}

    def _build_sd_prompt(self, expected_sellers, expected_buyers, expected_witnesses, current_data):
        count_instruction = f"""
        CASE: Type: Sale Deed (SD), Sellers:{expected_sellers}, Buyers:{expected_buyers}, Witnesses:{expected_witnesses}.
        """

        previously_identified_instruction = ""
        if current_data:
            clean_current = {}
            for k in ['ss', 'bs', 'ws', 'ps', 'title_chain']:
                if k in current_data and current_data[k]:
                    clean_current[k] = [{kk: vv for kk, vv in p.items() if vv} for p in current_data[k]]
                    clean_current[k] = [p for p in clean_current[k] if p]
            
            if any(clean_current.values()):
                previously_identified_instruction = f"""
        EXISTING ROLES (Map new documents to these names):
        {json.dumps(clean_current)}
        """

        prompt = """
        Extract data for Sale Deed (SD) from Hindi documents. Return ONLY a JSON object.
        IMPORTANT: Extract all descriptive text (Names, Addresses, Relations, Caste, Property details) in UNICODE HINDI (Hindi script).
        
        JSON STRUCTURE:
        {
          "rd": "Date of Execution of the CURRENT document being drafted (e.g. today's date if drafting a new deed, or the exact execution date specified in the Sale Deed. DO NOT use the Agreement to Sell date).",
          "amount": "Consideration Amount (digits only, e.g. '1500000')",
          "amount_words": "Amount in Words (Unicode Hindi, e.g. 'पंद्रह लाख')",
          "consideration": "Consideration details/value (Unicode Hindi)",
          "tds": "TDS details (Unicode Hindi, e.g., if consideration is >= 50 Lakhs)",
          "hypothecation": "Existing Mortgage Bank Name (Unicode Hindi)",
          "ss": [{"n":"Name", "a":"Age", "c":"Caste", "relation_text":"Complete Relation Phrase (e.g. 'पुत्र श्री भीवा राम')", "adr":"Address", "id":"Aadhar", "pan":"PAN"}],
          "bs": [{"n":"Name", "a":"Age", "c":"Caste", "relation_text":"Complete Relation Phrase (e.g. 'पुत्री श्री रामअवतार मीणा')", "adr":"Address", "id":"Aadhar", "pan":"PAN"}],
          "ps": [{
            "adr": "Full address if stated as a single string (Unicode Hindi)",
            "plot_no": "Plot/Flat/Unit number being sold (e.g. 'S-1' or 'A-24')",
            "floor": "Floor description for flat (Unicode Hindi, e.g. 'सेकंड फ्लोर')",
            "building_name": "Name of the building/society/complex (Unicode Hindi, e.g. 'श्री साईं रेजीडेंसी')",
            "project_name": "Name of the project if stated (Unicode Hindi, e.g. 'रॉयल एन्क्लेव')",
            "lease_deed_no": "JDA/Authority Patta or Lease Deed number (e.g. 'D-2341')",
            "document_number": "Document or registration number of the current deed if applicable",
            "landmark": "Landmark or location cue (Unicode Hindi, e.g. 'अजमेर रोड')",
            "scheme": "Colony/Scheme name (Unicode Hindi)",
            "village": "Village/Gram (Unicode Hindi)",
            "tehsil": "Tehsil name (Unicode Hindi)",
            "dist": "District (Unicode Hindi)",
            "state": "State (Unicode Hindi)",
            "land_area": "Area of the ORIGINAL PLOT including its unit (e.g. '183.33 वर्गगज' or '100 sq yards'). Do not drop the unit. This is the plot on which the building is constructed.",
            "const_area": "Super Built-up or construction area of the FLAT/UNIT being sold (e.g. '1087.19')",
            "unit": "Unit for land_area (e.g. 'वर्ग गज')",
            "const_unit": "Unit for const_area (e.g. 'वर्गफ़ीट')",
            "length_ew": "East-West dimension of the ORIGINAL PLOT (e.g. '30 फ़ीट')",
            "length_ns": "North-South dimension of the ORIGINAL PLOT (e.g. '55 फ़ीट')",
            "n": "North boundary of the ORIGINAL PLOT (Unicode Hindi)",
            "s": "South boundary of the ORIGINAL PLOT (Unicode Hindi)",
            "e": "East boundary of the ORIGINAL PLOT (Unicode Hindi)",
            "w": "West boundary of the ORIGINAL PLOT (Unicode Hindi)",
            "parking_type": "Open/Covered/None",
            "parking_number": "Parking number or description",
            "area_type": "Super Built-up / Carpet / Plot Area",
            "covered_area": "Covered area if stated",
            "property_portion": "Portion of the property being sold"
          }],
          "ws": [{"n":"Name", "relation_text":"Complete Relation Phrase (e.g. 'पुत्र श्री रामेश्वर प्रसाद')", "adr":"Address"}],
          "title_chain": [{"event_type":"SALE_DEED|ALLOTMENT|CONSTRUCTION|POA|RELINQUISHMENT|CORRECTION_DEED|TRANSFER", "document_name":"हिंदी Doc Name (e.g. 'विक्रय पत्र')", "date":"DD.MM.YYYY", "consideration_amount":"digits", "executant_name":"Seller/Authority (Unicode Hindi)", "claimant_name":"Buyer/Allottee (Unicode Hindi)", "is_registered":"true/false", "reg_office":"Office (Hindi)", "reg_date":"DD.MM.YYYY", "reg_book":"#", "reg_vol":"#", "reg_page":"#", "reg_no":"#", "reg_add_book":"#", "reg_add_vol":"#", "reg_add_page":"1026-1039 (number or range)", "project_name":"Name if CONSTRUCTION (Unicode Hindi, e.g. 'रॉयल एन्क्लेव')", "unit_number":"Unit/Flat No if CONSTRUCTION (Unicode Hindi, e.g. 'एस-1')", "confidence":"High/Medium/Low", "source_text":"exact source text"}],
          "reg": {"office":"Name", "book":"#", "vol":"#", "page":"#", "reg_no":"#", "reg_date":"Date"},
          "unassigned_aadhars": [{"s":"Mr/Mrs/Ms", "n":"Name", "a":"Age", "relation_text":"Complete Relation Phrase (exact Unicode Hindi)", "adr":"Address (exact Unicode Hindi)", "id":"Aadhar"}]
        }

        RULES:
        1. NO HALLUCINATION. If missing, use "".
        2. MANDATORY HINDI SCRIPT: You MUST use Unicode Hindi (Devanagari script) for ALL names, addresses, relations, castes, boundaries, and amount_words. DO NOT USE ENGLISH for these fields under any circumstances.
           - Correct Name: 'रामकुमार शर्मा' (NOT 'Ramkumar Sharma')
           - Correct Address: '१२३, मालवीय नगर, जयपुर' (NOT '123, Malviya Nagar, Jaipur')
           - Correct Relation: 'पुत्र श्री बनवारी लाल' (NOT 'S/o Banwari Lal')
           - Use English ONLY for fields like `id`, `pan`, `date` (DD.MM.YYYY), and purely numeric fields.
        2b. HINDI SOURCE PRIORITY: Always prefer extracting names and addresses natively from HINDI text in the uploaded documents (e.g., the Hindi side of an Aadhaar card, or a Hindi Agreement to Sale / ATS). The native Hindi print is much more reliable. Only fallback to translating/transliterating English text into Hindi if native Hindi text is completely unavailable.
        3. COUNTS: "ss" exactly selected count. "bs" exactly selected count. "ws" exactly 2.
        4. AADHAAR CARDS: Extract details from Aadhaar cards into 'unassigned_aadhars' ONLY.
        4b. WITNESS OCR ISOLATION: STRICTLY DO NOT extract witness details (names, addresses, Aadhaar, relation data) into 'unassigned_aadhars' or any other OCR sections. If an Aadhaar card belongs to a witness, do not extract it or include it in 'unassigned_aadhars'.
        5. BOUNDARIES: Extract the four boundary directions of the ORIGINAL PLOT from chain-of-title descriptions. Map to e, w, n, s. These are found in sentences like 'जिसकी चारों सीमाएं...' or 'पूर्व की ओर... पश्चिम की ओर...' etc.
        5b. DIMENSIONS: Extract length_ew (East-West) and length_ns (North-South) of the ORIGINAL PLOT from chain docs. These appear as 'पूर्व से पश्चिम XX फीट एवं उत्तर से दक्षिण XX फीट है'. land_area is the total plot area in sq. yards.
        6. RELATIONS & ADDRESSES: The first line on the back of an Aadhaar card is often the relation (e.g. S/o, C/o, W/o, D/o). YOU MUST SEPARATE THIS. Put the relation entirely in `relation_text` and only put the actual address in `adr`.
        6b. STRICT RELATION FORMATTING: ALWAYS format relations using exact Unicode Hindi (e.g. 'पुत्र श्री मोहनलाल', 'पत्नी श्री रामलाल', 'पुत्र स्वर्गीय श्री गंगाराम', 'पुत्री श्री ...'). NEVER output "S/O", "W/O", or "C/O".
        7. INCREMENTAL: Do not re-extract existing fields. Focus on new documents.
        8. PRECISE: Extract ALL digits of the consideration amount.
        9. TITLE CHAIN: Extract ALL title history events chronologically.
           - Map each event strictly to one of: ALLOTMENT, CONSTRUCTION, SALE_DEED, TRANSFER. Map any Gift, Relinquishment, Will, Mutation, or Transfer Letter/Order to TRANSFER. Map construction of flats/apartments to CONSTRUCTION.
           - CONSTRUCTION EVENT RULES: Create a CONSTRUCTION event if TSR/documents mention construction, flats built, units numbered, project/scheme named. Capture 'project_name' and 'unit_number' where available. The executant_name must be the owner/builder who constructed it. Specifically, if a construction paragraph in the documents contains language about naming/identifying the building or project (such as "तथा उसका नाम ... रख दिया", "परियोजना का नाम ... रखा गया", "अपार्टमेंट का नाम ... रखा", "नामकरण"), you MUST extract that exact project/building name as the project_name and store it on the CONSTRUCTION event.
           - TRANSFER EVENT RULES: Create a TRANSFER event if TSR contains Transfer Deed, Transfer Letter, or Transfer Order.
           - Names in executant_name and claimant_name MUST be EXACT, COMPLETE, FULL, and in Unicode Hindi. Preserve proprietor and parentage details (e.g. 'मैसर्स एक्सवाईजेड कंस्ट्रक्शन जरिये प्रोपराइटर श्री एबीसी पुत्र श्री एक्सवाईजेड'). Do not truncate or shorten names after the person's name (e.g. do not shorten "मैसर्स एक्सवाईजेड कंस्ट्रक्शन जरिये प्रोपराइटर श्री एबीसी पुत्र श्री एक्सवाईजेड" to just "मैसर्स एक्सवाईजेड कंस्ट्रक्शन जरिये प्रोपराइटर श्री एबीसी").
           - For ALLOTMENT: extract the exact patta/document number into 'document_number' (e.g. 'डी-2341').
           - For ALL registered deeds: Extract the 15-digit E-Panjiyan sequence/receipt number into 'reg_no' (e.g. '201803021103534'). This is labeled 'क्रम संख्या' or 'Receipt No'.
           - ALWAYS extract reg_add_book, reg_add_vol, reg_add_page (Additional/Addl. Book details) separately. Support page ranges for reg_add_page (e.g. '1026-1039', '494-507'). Do not truncate ranges to a single number.
        10. PROPERTY: For FLAT/UNIT sales, extract:
            - flat_no = the flat/unit number (e.g. 'S-1')
            - plot_no = the original plot number (e.g. 'A-24')
            - floor = floor description in Hindi
            - building_name = building/society name in Hindi
            - project_name = name given to the building project (e.g. 'रॉयल एन्क्लेव')
            - const_area = super built-up area of the flat
            - const_unit = unit for const_area
            - land_area = total area of the ORIGINAL PLOT
            - length_ew, length_ns = dimensions of the ORIGINAL PLOT
            - n,s,e,w = four boundaries of the ORIGINAL PLOT
        """
        return prompt + count_instruction + previously_identified_instruction

    def _normalize_sd_response(self, data, expected_sellers, expected_buyers, expected_witnesses):
        if not isinstance(data, dict):
            return {"error": "AI returned JSON, but it was not an object"}

        data["rd"] = format_date_with_dots(data.get("rd", ""))
        data["amount"] = re.sub(r'[^\d]', '', str(data.get("amount", "")))
        data["consideration"] = str(data.get("consideration", "")).strip()
        data["tds"] = str(data.get("tds", "")).strip()
        
        self._normalize_list(data, "ss", ["n", "a", "c", "relation_text", "adr", "id", "pan"])
        self._normalize_list(data, "bs", ["n", "a", "c", "relation_text", "adr", "id", "pan"])
        self._normalize_list(data, "ps", ["adr", "flat_no", "plot_no", "floor", "building_name", "project_name", "lease_deed_no", "document_number", "scheme", "village", "tehsil", "dist", "state", "land_area", "const_area", "unit", "const_unit", "n", "s", "e", "w", "ward", "khasra", "length_ew", "length_ns", "parking_type", "parking_number", "area_type", "covered_area", "property_portion"])
        self._normalize_list(data, "ws", ["n", "relation_text", "adr"])

        # Move extraction-compensation upstream (cleaning OCR commas between names and relations)
        for key in ["ss", "bs", "ws", "unassigned_aadhars"]:
            for person in data.get(key, []):
                if person.get("n"):
                    # Remove trailing comma from name if AI hallucinates it before a relation
                    person["n"] = re.sub(r',\s*$', '', person["n"]).strip()
                if person.get("relation_text"):
                    person["relation_text"] = normalize_relation_prefix(person["relation_text"], "SD")

        self._normalize_list(data, "title_chain", [
            "event_type", "document_name", "document_number", "date", "consideration_amount", 
            "executant_name", "claimant_name", "reg_office", "reg_date", 
            "reg_book", "reg_vol", "reg_page", "reg_no", "reg_add_book", "reg_add_vol", "reg_add_page", 
            "book_no", "volume_no", "page_no", "additional_book_no", "additional_volume_no", "additional_page_range",
            "confidence", "source_text", "is_registered", "project_name", "unit_number", "field_sources", "event_property_type"
        ])
        
        self._normalize_list(data, "unassigned_aadhars", ["s", "n", "a", "relation_text", "adr", "id"])
        
        witness_names = set()
        for w in data.get("ws", []):
            name_val = w.get("n", "").strip().casefold()
            if name_val:
                witness_names.add(name_val)
                sans_sal = re.sub(r'^(श्री|श्रीमती|mr|mrs|ms|shri|smt|sh)\.?\s+', '', name_val).strip()
                if sans_sal:
                    witness_names.add(sans_sal)

        filtered_ua = []
        for ua in data.get("unassigned_aadhars", []):
            ua_name = ua.get("n", "").strip().casefold()
            ua_sans_sal = re.sub(r'^(श्री|श्रीमती|mr|mrs|ms|shri|smt|sh)\.?\s+', '', ua_name).strip()
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

        for p in data.get("ps", []):
            p["full_address"] = self.generate_full_property_address(p, "SD")
            p["dimension_text"] = self.generate_dimension_text(p)
            p["boundary_text"] = self.generate_boundary_text(p)

        self._force_count(data, "ss", ["n", "a", "c", "relation_text", "adr", "id", "pan"], expected_sellers)
        self._force_count(data, "bs", ["n", "a", "c", "relation_text", "adr", "id", "pan"], expected_buyers)
        self._force_count(data, "ws", ["n", "relation_text", "adr"], expected_witnesses)
        
        if not data.get("title_chain"):
            data["title_chain"] = [{"event_type": "SALE_DEED", "document_name": "", "date": "", "consideration_amount": "", "executant_name": "", "claimant_name": "", "is_registered": "true", "reg_office": "", "reg_date": "", "reg_book": "", "reg_vol": "", "reg_page": "", "reg_no": "", "reg_add_book": "", "reg_add_vol": "", "reg_add_page": "", "confidence": "", "source_text": ""}]

        return data

    def _normalize_list(self, data, key, fields):
        items = data.get(key)
        if not isinstance(items, list):
            data[key] = []
            return
        
        alias_map = {
            "reg_book": "book_no",
            "reg_vol": "volume_no",
            "reg_page": "page_no",
            "reg_add_book": "additional_book_no",
            "reg_add_vol": "additional_volume_no",
            "reg_add_page": "additional_page_range"
        }
        
        clean_items = []
        for item in items:
            if not isinstance(item, dict): continue
            
            # Synchronize aliases two-way
            for orig, alias in alias_map.items():
                orig_val = str(item.get(orig, "")).strip()
                alias_val = str(item.get(alias, "")).strip()
                if orig_val and not alias_val:
                    item[alias] = orig_val
                elif alias_val and not orig_val:
                    item[orig] = alias_val
                    
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

    def heal_title_chain_from_ocr(self, title_chain, file_paths):
        """Heals title chain events by parsing OCR texts for project names and parentage."""
        if not title_chain or not file_paths:
            return

        # 1. Read all OCR/text files
        txt_contents = []
        for path in file_paths:
            if path.endswith('.txt'):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        txt_contents.append(f.read())
                except Exception as e:
                    print(f"[Healer Warning] Failed to read {path}: {e}")

        # Combine text content for searching
        combined_text = "\n".join(txt_contents)
        if not combined_text.strip():
            return

        # 2. Extract project name using general rule
        project_name = None
        patterns = [
            r'उसका\s+नाम\s+(?:[श्\"\'“‘]([^श्\"\'”’।]+)[श्\"\'”’]|([^ \t\n\r।]+))\s+रख\s+दिया',
            r'परियोजना\s+का\s+नाम\s+(?:[श्\"\'“‘]([^श्\"\'”’।]+)[श्\"\'”’]|([^ \t\n\r।]+))\s+रखा\s+गया',
            r'अपार्टमेंट\s+का\s+नाम\s+(?:[श्\"\'“‘]([^श्\"\'”’।]+)[श्\"\'”’]|([^ \t\n\r।]+))\s+रखा',
            r'नामकरण\s+(?:[श्\"\'“‘]([^श्\"\'”’।]+)[श्\"\'”’]|([^ \t\n\r।]+))'
        ]
        for pattern in patterns:
            matches = re.findall(pattern, combined_text)
            for match in matches:
                val = match[0] or match[1]
                if val:
                    val = val.strip()
                    val = re.sub(r'^[श्\"\'“‘\s]+|[श्\"\'”’\s]+$', '', val).strip()
                    if val:
                        project_name = val
                        print(f"[Healer] Found project name: {project_name}")
                        break
            if project_name:
                break

        # 3. Heal parentage for executants and claimants in the title chain
        for evt in title_chain:
            for field in ["executant_name", "claimant_name"]:
                name = evt.get(field, "")
                if not name:
                    continue
                if any(rel in name for rel in ["पुत्र", "पत्नी", "पत्नि", "पुत्री"]):
                    continue
                
                clean_name = re.sub(r'^(मैसर्स|M/s|Messrs|श्री|श्रीमती)\.?\s+', '', name, flags=re.IGNORECASE).strip()
                person_name = clean_name
                for split_word in ["जरिये", "द्वारा", "partner", "proprietor", "prop", "प्रोपराइटर", "भागीदार"]:
                    if split_word in person_name:
                        parts = person_name.split(split_word)
                        if len(parts) > 1:
                            person_name = parts[-1].strip()
                            
                person_name = re.sub(r'[^\u0900-\u097F\s]', '', person_name).strip()
                person_name = re.sub(r'^(श्री|श्रीमती|स्व\.|स्वर्गीय)\.?\s+', '', person_name).strip()
                
                if not person_name or len(person_name) < 3:
                    continue
                    
                person_name_clean = " ".join(person_name.split())
                escaped_name = r'\s*'.join(re.escape(c) for c in person_name_clean)
                
                rel_pattern = escaped_name + r'\s*(?:पुत्र|पत्नि|पत्नी|पुत्री)\s+(?:श्री|स्व\.?\s*श्री|स्वर्गीय\s+श्री)?\s*([^\s,।\d()]+(?:\s+[^\s,।\d()]+){0,4})'
                match = re.search(rel_pattern, combined_text)
                if match:
                    full_match = match.group(0)
                    relation_phrase = full_match[len(person_name_clean):].strip()
                    relation_phrase = re.sub(r'^पत्नि', 'पत्नी', relation_phrase)
                    
                    # Truncate at stop words/postpositions
                    words = relation_phrase.split()
                    stop_words = {
                        "ने", "को", "का", "की", "के", "द्वारा", "से", "तथा", "एवं", "और", 
                        "विक्रय", "कर", "दिया", "अपने", "उक्त", "प्रथमपक्ष", "द्वितीयपक्ष", 
                        "क्रेता", "विक्रेता", "निवासी", "निवासी:", "निवासीः-", "आयु", "जाति"
                    }
                    cleaned_words = []
                    for w in words:
                        w_clean = re.sub(r'[।\s,.:\-–—]', '', w)
                        if w_clean in stop_words:
                            break
                        cleaned_words.append(w)
                    relation_phrase = " ".join(cleaned_words).strip()
                    
                    if relation_phrase:
                        evt[field] = f"{name} {relation_phrase}"
                        print(f"[Healer] Healed parentage for {name} -> {evt[field]}")

        # 4. Correct executant of CONSTRUCTION based on chronological owner context
        non_const_evts = [e for e in title_chain if e.get("event_type") != "CONSTRUCTION"]
        
        def get_sort_key(evt):
            date_str = evt.get("date", "")
            if not date_str:
                return "00000000"
            m = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', date_str)
            if m:
                return f"{m.group(3)}{m.group(2)}{m.group(1)}"
            m = re.search(r'(\d{4})', date_str)
            if m:
                return f"{m.group(1)}0000"
            return "00000000"
        sorted_evts = sorted(non_const_evts, key=get_sort_key)

        for idx, evt in enumerate(title_chain):
            if evt.get("event_type") == "CONSTRUCTION":
                builder_name = None
                
                # A. Try succeeding event's executant (the seller of the flat)
                if idx + 1 < len(title_chain):
                    n = title_chain[idx + 1].get("executant_name")
                    if n and "प्राधिकरण" not in n:
                        builder_name = n
                
                # B. Try preceding event's claimant (the buyer of the plot)
                if not builder_name and idx - 1 >= 0:
                    n = title_chain[idx - 1].get("claimant_name")
                    if n and "प्राधिकरण" not in n:
                        builder_name = n
                        
                # C. Date-sorting fallback
                if not builder_name:
                    const_date_key = get_sort_key(evt)
                    last_before = None
                    for e in sorted_evts:
                        if get_sort_key(e) <= const_date_key and const_date_key != "00000000":
                            last_before = e
                    if last_before:
                        n = last_before.get("claimant_name")
                        if n and "प्राधिकरण" not in n:
                            builder_name = n
                    if not builder_name:
                        for e in sorted_evts:
                            if get_sort_key(e) > const_date_key:
                                n = e.get("executant_name")
                                if n and "प्राधिकरण" not in n:
                                    builder_name = n
                                    break
                
                # D. Final fallback to any name
                if not builder_name and sorted_evts:
                    builder_name = sorted_evts[-1].get("executant_name") or sorted_evts[-1].get("claimant_name")
                    
                if builder_name:
                    evt["executant_name"] = builder_name
                    print(f"[Healer] Set CONSTRUCTION builder to: {builder_name}")
                if project_name:
                    evt["project_name"] = project_name

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
