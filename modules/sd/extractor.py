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

    def _filter_relevant_pages(self, pages_text, min_pages_threshold=8, score_threshold=2):
        """Pre-filters pages of text-searchable PDFs based on high-relevance title flow keywords."""
        total_pages = len(pages_text)
        if total_pages <= min_pages_threshold:
            print(f"[Pre-filter] Total pages ({total_pages}) <= threshold ({min_pages_threshold}). Keeping all pages.")
            return [text for _, text in pages_text], list(range(1, total_pages + 1))

        # Keywords with weights
        primary_keywords = [
            "chain of title", "history of title", "flow of title", "tracing of title", 
            "chain of documents", "detail of documents", "deeds", "विक्रय पत्र", 
            "पट्टा विलेख", "मुख्तियारनामा", "हकत्याग पत्र", "वसीयतनामा", "दाखिल खारिज", 
            "नामांतरण", "chain of deeds", "antecedent deeds", "flow of ownership"
        ]
        
        secondary_keywords = [
            "sale deed", "allotment", "lease deed", "power of attorney", "will", 
            "death certificate", "succession", "gift deed", "relinquishment", "mutation", 
            "patta", "registered", "registry", "khasra", "khata", "rakba", "ownership",
            "विक्रय", "आवंटन", "रजिस्ट्री", "पंजीकृत", "उत्तराधिकार", "मृत्यु", "खसरा", 
            "खाता", "क्रेता", "विक्रेता", "स्वामित्व", "शीर्षक", "दस्तावेज"
        ]

        page_scores = []
        total_extracted_len = 0
        for page_num, text in pages_text:
            total_extracted_len += len(text)
            score = 0
            text_lower = text.lower()
            
            # Score primary keywords (3 points each)
            for kw in primary_keywords:
                if kw in text_lower:
                    score += 3
                    
            # Score secondary keywords (1 point each)
            for kw in secondary_keywords:
                if kw in text_lower:
                    score += 1
                    
            page_scores.append((page_num, score, text))

        # If the PDF has no searchable text (scanned PDF), return None to disable filtering and send raw bytes
        if total_extracted_len < 200:
            print(f"[Pre-filter] Scanned PDF detected (total text len: {total_extracted_len}). Disabling pre-filtering.")
            return None, None

        # Select pages matching threshold
        selected_indices = set()
        for idx, (page_num, score, _) in enumerate(page_scores):
            if score >= score_threshold:
                selected_indices.add(idx)
                # Also keep the immediately following page to prevent cutting off a paragraph in the middle
                if idx + 1 < total_pages:
                    selected_indices.add(idx + 1)
                # Also keep the immediately preceding page to ensure context
                if idx - 1 >= 0:
                    selected_indices.add(idx - 1)

        # Sort selected indices
        selected_indices = sorted(list(selected_indices))
        
        # If no pages matched, fall back to keeping all pages
        if not selected_indices:
            print("[Pre-filter] No pages matched the score threshold. Keeping all pages.")
            return [text for _, text in pages_text], list(range(1, total_pages + 1))

        selected_texts = [page_scores[i][2] for i in selected_indices]
        selected_page_nums = [page_scores[i][0] for i in selected_indices]
        
        print(f"[Pre-filter] Filtered {total_pages} pages down to {len(selected_texts)} pages: {selected_page_nums}")
        return selected_texts, selected_page_nums

    def extract_title_chain(self, file_paths, model_name="gemini-2.5-flash"):
        """Dedicated extraction path for parsing Title Chain history from Legal Reports with Chronological CoT and PDF pre-filtering."""
        if not self.api_keys:
            return {"error": "Gemini API Keys Missing"}

        contents = []
        txt_files = [p for p in file_paths if p.lower().endswith('.txt')]
        effective_paths = txt_files if txt_files else file_paths
        
        filtered_files_desc = []

        for path in effective_paths:
            ext = os.path.splitext(path)[1].lower()
            mime_type, _ = mimetypes.guess_type(path)
            
            if ext == '.pdf':
                # Try pre-filtering the PDF using pypdf text extraction
                try:
                    import pypdf
                    pages_text = []
                    reader = pypdf.PdfReader(path)
                    for idx, page in enumerate(reader.pages):
                        text = page.extract_text() or ""
                        pages_text.append((idx + 1, text))
                    
                    selected_texts, selected_pages = self._filter_relevant_pages(pages_text)
                    if selected_texts is not None:
                        # Success! We filtered the PDF text pages
                        combined_filtered_text = f"--- Legal Report Page-Filtered Content ({os.path.basename(path)}) ---\n"
                        for p_num, p_text in zip(selected_pages, selected_texts):
                            combined_filtered_text += f"\n--- PAGE {p_num} ---\n{p_text}\n"
                        contents.append(types.Part.from_text(text=combined_filtered_text))
                        filtered_files_desc.append(f"{os.path.basename(path)} (Pages {selected_pages} kept)")
                        print(f"[Pre-filter] Successfully filtered {os.path.basename(path)} to pages {selected_pages}")
                        continue
                except Exception as pdf_err:
                    print(f"[Pre-filter Warning] Failed to pre-filter PDF {path}: {pdf_err}")
                
                # If pre-filtering failed or was bypassed (scanned PDF), send the raw PDF bytes
                with open(path, 'rb') as f:
                    raw = f.read()
                contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type or 'application/octet-stream'))
                filtered_files_desc.append(f"{os.path.basename(path)} (Sent entire PDF as binary)")
                
            elif ext in ['.jpg', '.jpeg', '.png']:
                with open(path, 'rb') as f:
                    raw = f.read()
                contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type or 'application/octet-stream'))
                filtered_files_desc.append(f"{os.path.basename(path)} (Sent image)")
                
            elif ext == '.txt':
                with open(path, 'r', encoding='utf-8') as f:
                    contents.append(types.Part.from_text(text=f.read()))
                filtered_files_desc.append(f"{os.path.basename(path)} (Sent text)")

        if not contents:
            return {"error": "No valid files to process."}

        prompt = """
        CRITICAL MISSION: You are a senior legal analyst reviewing a Title Search Report (TSR) or chain of documents.
        Your task is to extract the complete, highly accurate CHRONOLOGICAL History of Title / Chain of Ownership of the property.

        LINKAGE & CHAIN OF CUSTODY RULE:
        Every title flow is a continuous chain of custody. Ensure that the Claimant (Buyer/Allottee/Heir) of Event N matches the Executant (Seller/Giver/Deceased) of Event N+1. If there is a gap (e.g. Person A acquires the property, but later Person B sells it), carefully search the text to find the bridging event (such as a Will, Death/Succession, Gift, or Power of Attorney) and extract it!

        MAP TO SPECIFIC TEMPLATE KEYS:
        Classify each event and populate its matching template fields:
        1. ALLOTMENT_SOCIETY: Society allotment. Requires: "receipt_no" (receipt number), "receipt_date" (DD.MM.YYYY).
        2. DEATH_HEIRS_WITH_SPOUSE: Demise of owner and spouse. Requires: "wife_name", "wife_death_date" (DD.MM.YYYY), "share_fraction" (fraction/percentage, e.g., '1/2' or 'अविभाजित').
        3. DEATH_HEIRS_SINGLE: Demise of single owner. Requires: "share_fraction".
        4. DEATH_DIVIDED: Demise of owner with physical divided portions given to heirs. Requires: "husband_name", "husband_death_date" (DD.MM.YYYY), "east_owner", "west_owner".
        5. HAK_TYAG: Relinquishment deed. Requires: "share_fraction".
        6. AGRICULTURAL_ALLOTMENT: Revenue record allotment. Requires: "khata_no", "khasra_no", "rakba", "share_fraction".
        7. POA_AGRICULTURAL: Power of attorney for agricultural land. Requires: "khasra_no", "rakba", "share_fraction", "co_owner".
        8. POA_NON_AGRICULTURAL: Standard registered POA. Requires: "share_fraction".
        9. COLONY_DEVELOPMENT: Plot sub-division event. Requires: "owner_name", "share_fraction".
        10. DEVELOPER_AGREEMENT: Development agreement. Requires: "share_fraction".
        11. PART_SALE: Sale deed transferring partial share. Requires: "share_fraction".
        12. TRANSFER_CERTIFICATE: Transfer certificate with receipt. Requires: "receipt_no", "receipt_date" (DD.MM.YYYY).
        13. GIFT_DEED: Registered Gift deed. Requires: "parent_property_info" (parent plot/land info).
        14. WILL: Registered/unregistered Will. Requires: "will_type" (Registered/Unregistered), "death_date" (DD.MM.YYYY of testator).
        15. PARTITION: Partition deed. Requires: "share_fraction".
        16. ALLOTMENT_PLOT / ALLOTMENT_FLAT: Plot or Flat allotment by local authority.
        17. CONSTRUCTION_FLAT: Multi-story building construction. Requires: "project_name", "unit_number".
        18. SALE_DEED_PLOT / SALE_DEED_FLAT: Standard registered sale deed of plot or flat.

        MAP EVENT TYPES:
        Each event MUST have an "event_type" mapping to one of: ALLOTMENT, CONSTRUCTION, SALE_DEED, WILL, DEATH, HAK_TYAG, POA, or TRANSFER.

        ENGLISH-FIRST EXTRACTION RULE:
        To maximize parsing accuracy and avoid cognitive overload, extract all names ("executant_name", "claimant_name", "wife_name", "husband_name", "east_owner", "west_owner", "owner_name", "co_owner"), document types ("document_name"), and registrar offices ("reg_office") in ENGLISH, EXACTLY as written in the report. They will be translated/transliterated to Hindi in a subsequent dedicated step.

        JSON FORMAT SPECIFICATION:
        Return a JSON object with EXACTLY two keys:
        1. "chronological_analysis": A detailed, step-by-step text description showing your legal reasoning, how you traced the property chain of custody, how you resolved any name/title gaps, and how you mapped each event to a template.
        2. "title_chain": An array of objects sorted chronologically (oldest first) containing the following fields:
           - template_key: (String, one of the 18 keys listed above, e.g. "ALLOTMENT_SOCIETY")
           - event_type: (String, ALLOTMENT, CONSTRUCTION, SALE_DEED, WILL, DEATH, HAK_TYAG, POA, TRANSFER)
           - document_name: (String, e.g., 'Sale Deed', 'Allotment Letter', 'Death/Succession', 'Power of Attorney')
           - document_number: (String, e.g., 'D-2341')
           - date: (String, DD.MM.YYYY format. Convert e.g., '11th July, 2019' to '11.07.2019'. Leave blank "" if not found)
           - executant_name: (String, Seller/Principal/Authority in English)
           - claimant_name: (String, Buyer/Attorney/Allottee/Heir in English)
           - is_registered: (String, "true" or "false")
           - reg_office: (String, Registrar office in English, e.g., 'Sub-Registrar Jaipur-VII')
           - reg_date: (String, DD.MM.YYYY format)
           - reg_book, reg_vol, reg_page: (String, numbers only)
           - reg_no: (String, 15-digit E-Panjiyan sequence/receipt number, e.g., '201803021103534')
           - reg_add_book, reg_add_vol: (String, numbers only)
           - reg_add_page: (String, page range, e.g., '1026-1039')
           - consideration_amount: (String, numbers only)
           - project_name: (String, e.g., 'Royal Enclave' - for CONSTRUCTION only)
           - unit_number: (String, e.g., 'S-1' - for CONSTRUCTION only)
           - share_fraction: (String, e.g. '1/2', 'undivided' - where applicable)
           - wife_name: (String, where applicable)
           - wife_death_date: (String, DD.MM.YYYY)
           - husband_name: (String, where applicable)
           - husband_death_date: (String, DD.MM.YYYY)
           - east_owner: (String, where applicable)
           - west_owner: (String, where applicable)
           - khata_no: (String, where applicable)
           - khasra_no: (String, where applicable)
           - rakba: (String, where applicable)
           - co_owner: (String, where applicable)
           - owner_name: (String, where applicable)
           - parent_property_info: (String, where applicable)
           - will_type: (String, 'Registered' or 'Unregistered')
           - death_date: (String, DD.MM.YYYY)
           - receipt_no: (String, where applicable)
           - receipt_date: (String, DD.MM.YYYY)
           - confidence: (String, 'High', 'Medium', 'Low')
           - source_text: (String, exact 1-2 sentences from English report proving this event)

        CRITICAL RULES:
        1. DO NOT SKIP ANY TRANSFERS. Every link must be represented.
        2. DO NOT HALLUCINATE DATES OR KEYS. If a specific field is not found in the text, leave it blank "".
        3. Return ONLY valid, parseable JSON. No conversational text outside JSON.
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
                        "template_key", "event_type", "document_name", "document_number", "date", "consideration_amount", 
                        "executant_name", "claimant_name", "reg_office", "reg_date", 
                        "reg_book", "reg_vol", "reg_page", "reg_no", "reg_add_book", "reg_add_vol", "reg_add_page", 
                        "book_no", "volume_no", "page_no", "additional_book_no", "additional_volume_no", "additional_page_range",
                        "confidence", "source_text", "is_registered", "project_name", "unit_number", "field_sources", "event_property_type",
                        "share_fraction", "wife_name", "wife_death_date", "husband_name", "husband_death_date", 
                        "east_owner", "west_owner", "khata_no", "khasra_no", "rakba", "co_owner", "owner_name", 
                        "parent_property_info", "will_type", "death_date", "receipt_no", "receipt_date"
                    ])
                    # We run OCR healing later on the Hindi translated name lists, but run a basic pass here as well
                    self.heal_title_chain_from_ocr(data["title_chain"], file_paths)
                    
                return data

            except Exception as e:
                print(f"[FAILOVER WARNING] Gemini extract_title_chain failed (Key {self.active_key_index}): {e}")
                last_error = str(e)
                self._rotate_key()
                attempts += 1

        return {"error": f"AI Extraction Failed after {max_attempts} attempts. Last error: {last_error}"}

    def translate_title_chain_to_hindi(self, chain_events, file_paths=None, model="gemini-2.5-flash"):
        """Translates English fields in title chain to Unicode Hindi using Gemini and runs OCR healing."""
        if not chain_events:
            return chain_events
            
        prompt = f"""
        You are a Hindi legal translation expert.
        Translate the following list of title chain events into Unicode Hindi.
        
        Specifically:
        - Translate/transliterate "executant_name", "claimant_name", "reg_office", "document_name", "wife_name", "husband_name", "east_owner", "west_owner", "owner_name", and "co_owner" into proper Unicode Hindi (Devanagari script).
        - Keep dates, numbers, event_type, is_registered, and numeric/alphanumeric fields (like reg_book, reg_vol, reg_page, reg_no, document_number) exactly as they are.
        - Ensure names preserve relation details and title/proprietorship structures (e.g. "wife of", "son of", "Proprietor", "M/s" translated/transliterated properly in Hindi).
        
        Input list:
        {json.dumps(chain_events, ensure_ascii=False, indent=2)}
        
        Return ONLY a JSON array of these events with the translated fields. Do not include any explanation.
        """
        try:
            raw_res = self.raw_generate(prompt, model_name=model)
            if raw_res:
                m = re.search(r'```json\s*(.*?)\s*```', raw_res, re.DOTALL | re.IGNORECASE)
                if m:
                    raw_res = m.group(1)
                else:
                    m = re.search(r'(\[.*\])', raw_res, re.DOTALL)
                    if m:
                        raw_res = m.group(1)
                translated = json.loads(raw_res)
                if isinstance(translated, list) and len(translated) == len(chain_events):
                    # Call heal_title_chain_from_ocr on the translated Hindi events to restore full parentage details
                    if file_paths:
                        self.heal_title_chain_from_ocr(translated, file_paths)
                    return translated
        except Exception as e:
            print(f"[WARNING] translate_title_chain_to_hindi failed: {e}")
            
        # Fallback: run healing on the untranslated chain if translation fails
        if file_paths:
            self.heal_title_chain_from_ocr(chain_events, file_paths)
        return chain_events


    def extract_buckets_with_ai(self, buckets, selected_model, expected_sellers=None, expected_buyers=None,
                                expected_witnesses=2, seller_hints="", buyer_hints="", witness_hints="",
                                current_data=None, **kwargs):
        """
        Process each SD document bucket independently according to its primary objective,
        and then merge the extracted results using the Source Priority Matrix.
        """
        if not self.api_keys:
            return {"error": "Gemini API Keys Missing"}

        merged_data = current_data or {}

        # 1. KYC - Extract Identity only
        if buckets.get("kyc"):
            kyc_prompt = self._build_kyc_prompt(expected_sellers, expected_buyers, expected_witnesses)
            kyc_res = self._run_gemini_extraction(buckets["kyc"], selected_model, kyc_prompt)
            if kyc_res and not kyc_res.get("error"):
                merged_data = self._merge_kyc_results(merged_data, kyc_res)

        # 2. Legal - Extract Property and Chain only (Primary Source)
        if buckets.get("legal"):
            legal_prompt = self._build_legal_prompt()
            legal_res = self._run_gemini_extraction(buckets["legal"], selected_model, legal_prompt)
            if legal_res and not legal_res.get("error"):
                merged_data = self._merge_legal_results(merged_data, legal_res, file_paths=buckets["legal"])

        # 3. ATS - Extract Consideration and Transaction only
        if buckets.get("ats"):
            ats_prompt = self._build_ats_prompt()
            ats_res = self._run_gemini_extraction(buckets["ats"], selected_model, ats_prompt)
            if ats_res and not ats_res.get("error"):
                merged_data = self._merge_ats_results(merged_data, ats_res)

        # 4. Title Chain - Extract Site Plan Dimensions and verify
        if buckets.get("title_chain"):
            title_prompt = self._build_title_prompt()
            title_res = self._run_gemini_extraction(buckets["title_chain"], selected_model, title_prompt)
            if title_res and not title_res.get("error"):
                merged_data = self._merge_title_results(merged_data, title_res)

        return self._normalize_final_data(merged_data, expected_sellers, expected_buyers, expected_witnesses)

    def _run_gemini_extraction(self, file_paths, selected_model, prompt):
        contents = []
        txt_files = [p for p in file_paths if p.lower().endswith('.txt')]
        effective_paths = txt_files if txt_files else file_paths
        import mimetypes
        import os
        from google.genai import types
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
            elif ext == '.docx':
                try:
                    import docx
                    doc = docx.Document(path)
                    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                    contents.append(types.Part.from_text(text=text))
                except Exception as e:
                    print(f"Error reading docx {path}: {e}")
                    pass

        return self._call_gemini(selected_model, contents, prompt)

    def _call_gemini(self, selected_model, contents, prompt):
        from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
        from google.genai.errors import APIError
        import json
        import re

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
            def _api_call(client, model, contents):
                return client.models.generate_content(model=model, contents=contents)

            try:
                full_contents = contents + [prompt]
                response = _api_call(self.client, selected_model, full_contents)
                raw_text = response.text

                # Cleanup markdown and parse JSON
                json_str = raw_text.replace('```json', '').replace('```', '').strip()
                if not json_str: return {"error": "Empty JSON"}

                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    # Attempt dirty fix
                    try:
                        dirty_str = re.sub(r',\s*}', '}', json_str)
                        dirty_str = re.sub(r',\s*\]', ']', dirty_str)
                        return json.loads(dirty_str)
                    except:
                        return {"error": f"JSON Parse Failed: {str(e)}"}
            except Exception as e:
                from tenacity import RetryError
                underlying = e.last_attempt.exception() if isinstance(e, RetryError) else e
                last_error = str(underlying)
                print(f"[FAILOVER WARNING] Gemini extraction failed: {last_error}")
                self._rotate_key()
                attempts += 1

        return {"error": f"Extraction Failed: {last_error}"}

    def _is_meaningful(self, val):
        if not val: return False
        val_str = str(val).strip().lower()
        if val_str in ["", "null", "none", "n/a", "unknown", "not available", "-"]: return False
        return True

    def _merge_kyc_results(self, current, kyc):
        # KYC is #1 for Seller/Buyer Name and Address
        for key in ["ss", "bs"]:
            current_list = current.get(key, [])
            kyc_list = kyc.get(key, [])
            max_len = max(len(current_list), len(kyc_list))
            for i in range(max_len):
                if i >= len(current_list): current_list.append({})
                if i < len(kyc_list):
                    k_item = kyc_list[i]
                    c_item = current_list[i]
                    if self._is_meaningful(k_item.get("n")): c_item["n"] = k_item["n"]
                    if self._is_meaningful(k_item.get("n_en")): c_item["n_en"] = k_item["n_en"]
                    if self._is_meaningful(k_item.get("adr")): c_item["adr"] = k_item["adr"]
                    if self._is_meaningful(k_item.get("adr_en")): c_item["adr_en"] = k_item["adr_en"]
                    if self._is_meaningful(k_item.get("a")): c_item["a"] = k_item["a"]
                    if self._is_meaningful(k_item.get("id")): c_item["id"] = k_item["id"]
                    if self._is_meaningful(k_item.get("pan")): c_item["pan"] = k_item["pan"]
                    if self._is_meaningful(k_item.get("relation_text")): c_item["relation_text"] = k_item["relation_text"]
                    if self._is_meaningful(k_item.get("rn_en")): c_item["rn_en"] = k_item["rn_en"]
                    if self._is_meaningful(k_item.get("dob")): c_item["dob"] = k_item["dob"]
            current[key] = current_list

        # Preserve unassigned Aadhaar cards for Role Assignment UI in SD mode
        if "unassigned_aadhars" in kyc:
            current["unassigned_aadhars"] = kyc["unassigned_aadhars"]

        return current

    def _merge_legal_results(self, current, legal, file_paths=None):
        # Legal is #1 for Property Address, Area, Boundaries, Title Chain
        # It is #2 for Seller/Buyer Address
        current_ps = current.get("ps", [{}])
        legal_ps = legal.get("ps", [{}])
        if legal_ps:
            c_p = current_ps[0]
            l_p = legal_ps[0]
            for f in ["adr", "land_area", "const_area", "unit", "const_unit", "plot_no", "floor", "building_name", "n", "s", "e", "w"]:
                if self._is_meaningful(l_p.get(f)): c_p[f] = l_p[f]
        current["ps"] = current_ps

        if legal.get("title_chain") and len(legal["title_chain"]) > 0:
            raw_chain = legal["title_chain"]
            # Translate English fields to Unicode Hindi and heal with OCR if file_paths are present
            translated_chain = self.translate_title_chain_to_hindi(raw_chain, file_paths=file_paths)
            current["title_chain"] = translated_chain

        for key in ["ss", "bs"]:
            current_list = current.get(key, [])
            legal_list = legal.get(key, [])
            for i in range(min(len(current_list), len(legal_list))):
                if not self._is_meaningful(current_list[i].get("adr")) and self._is_meaningful(legal_list[i].get("adr")):
                    current_list[i]["adr"] = legal_list[i]["adr"]
                if not self._is_meaningful(current_list[i].get("adr_en")) and self._is_meaningful(legal_list[i].get("adr_en")):
                    current_list[i]["adr_en"] = legal_list[i]["adr_en"]
        return current

    def _merge_ats_results(self, current, ats):
        # ATS is #1 for Sale Amount, #2 for Seller Name, #3 for Property Address / Seller Address
        if self._is_meaningful(ats.get("amount")): current["amount"] = ats["amount"]
        if self._is_meaningful(ats.get("amount_words")): current["amount_words"] = ats["amount_words"]
        if self._is_meaningful(ats.get("consideration")): current["consideration"] = ats["consideration"]

        for key in ["ss", "bs"]:
            current_list = current.get(key, [])
            ats_list = ats.get(key, [])
            for i in range(min(len(current_list), len(ats_list))):
                if not self._is_meaningful(current_list[i].get("n")) and self._is_meaningful(ats_list[i].get("n")):
                    current_list[i]["n"] = ats_list[i]["n"]
                if not self._is_meaningful(current_list[i].get("n_en")) and self._is_meaningful(ats_list[i].get("n_en")):
                    current_list[i]["n_en"] = ats_list[i]["n_en"]
                if not self._is_meaningful(current_list[i].get("adr")) and self._is_meaningful(ats_list[i].get("adr")):
                    current_list[i]["adr"] = ats_list[i]["adr"]
                if not self._is_meaningful(current_list[i].get("adr_en")) and self._is_meaningful(ats_list[i].get("adr_en")):
                    current_list[i]["adr_en"] = ats_list[i]["adr_en"]

        current_ps = current.get("ps", [{}])
        ats_ps = ats.get("ps", [{}])
        if ats_ps:
            c_p = current_ps[0]
            a_p = ats_ps[0]
            if not self._is_meaningful(c_p.get("adr")) and self._is_meaningful(a_p.get("adr")): c_p["adr"] = a_p["adr"]
        current["ps"] = current_ps
        return current

    def _merge_title_results(self, current, title):
        # Title is #1 for Site Plan Dimensions, #2 for Property Address/Area/Boundaries
        current_ps = current.get("ps", [{}])
        title_ps = title.get("ps", [{}])
        if title_ps:
            c_p = current_ps[0]
            t_p = title_ps[0]

            if self._is_meaningful(t_p.get("east_west_dim")): c_p["east_west_dim"] = t_p["east_west_dim"]
            if self._is_meaningful(t_p.get("north_south_dim")): c_p["north_south_dim"] = t_p["north_south_dim"]

            for f in ["adr", "land_area", "n", "s", "e", "w", "length_ew", "length_ns"]:
                if not self._is_meaningful(c_p.get(f)) and self._is_meaningful(t_p.get(f)):
                    c_p[f] = t_p[f]
        current["ps"] = current_ps
        return current

    def _build_kyc_prompt(self, expected_sellers, expected_buyers, expected_witnesses):
        return f"""
        Extract identity data from these KYC/ID documents (Aadhaar, PAN, Driving License). Return ONLY a JSON object.
        IMPORTANT: Extract descriptive text in UNICODE HINDI. English names/addresses/relations must be transliterated.

        JSON STRUCTURE:
        {{
          "unassigned_aadhars": [{{
            "s": "Mr/Mrs/Ms (based on gender)",
            "n": "Name (Unicode Hindi)",
            "a": "Age (numeric)",
            "relation_text": "Complete Relation Phrase (e.g. 'पुत्र श्री ...' or 'पत्नी श्री ...' in Unicode Hindi)",
            "adr": "Address (exact Aadhaar/DL print in Unicode Hindi)",
            "id": "Aadhar Number (digits only)",
            "pan": "PAN Card Number (10-char alphanumeric, if PAN card is provided)"
          }}]
        }}
        
        CRITICAL EXTRACTION RULES:
        1. AADHAAR CARDS & ID DOCUMENTS: Extract details from Aadhaar/PAN/DL into 'unassigned_aadhars' ONLY. DO NOT map them directly to sellers or buyers.
        2. RELATIONS & ADDRESSES SEPARATION:
           - Look at the relationship line in the ID documents.
           - Format it strictly in Unicode Hindi as:
             * "पुत्र श्री <Father's Name>" (for Son of)
             * "पुत्री श्री <Father's Name>" (for Daughter of)
             * "पत्नी श्री <Husband's Name>" (for Wife of)
             * "पति श्री <Wife's Name>" (for Husband of)
             * "पुत्र स्वर्गीय श्री <Name>" (if deceased/Late is mentioned)
             * "केयर ऑफ श्री <Name>" (for Care of)
           - Store this entire formatted phrase in the `relation_text` field.
           - STRICTLY REMOVE this relationship prefix and the relative's name from the beginning of the `adr` field. The `adr` field must start with the house/flat number or street name, NOT the relative's name.
        3. FIELD EXTRACTION PRIORITY & MERGING (Aadhaar > PAN > Driving License):
           If multiple documents (e.g. Aadhaar, PAN, Driving License) belong to the same person, you MUST merge their details into a single object in the `unassigned_aadhars` list. For each field, follow this strict priority order:
           - NAME (`n`):
             1. Aadhaar Card name (Unicode Hindi).
             2. PAN Card name (Unicode Hindi).
             3. Driving License name (Unicode Hindi).
           - AGE / DOB (`a`):
             1. Aadhaar Card age/DOB.
             2. PAN Card DOB (calculate age based on DOB relative to the current year 2026).
             3. Driving License DOB (calculate age).
           - RELATION (`relation_text`):
             1. Aadhaar Card: Look at the back of the Aadhaar card. If a relationship line (e.g. "C/o", "S/o", "W/o", "D/o" or Hindi equivalent) is printed, use it.
             2. PAN Card: If Aadhaar lacks it, extract the Father's Name from the PAN card and format it as "पुत्र श्री <Father's Name from PAN>" (if male) or "पुत्री श्री <Father's Name from PAN>" (if female).
             3. Driving License: If both Aadhaar and PAN lack it, extract the "S/o", "W/o", or "D/o" line from the Driving License.
           - ADDRESS (`adr`):
             1. Aadhaar Card address (Unicode Hindi).
             2. Driving License address (Unicode Hindi).
             (Note: PAN card does not contain an address).
           - ID NUMBERS:
             - `id` = Aadhaar Number (from Aadhaar card).
             - `pan` = PAN Card Number (from PAN card).
        4. STRICT RELATION FORMATTING: ALWAYS format relations using exact Unicode Hindi. NEVER output English abbreviations like "S/O", "W/O", or "C/O" in `relation_text`.
        """

    def _build_legal_prompt(self):
        return """
        CRITICAL MISSION: You are a senior legal analyst reviewing a Title Search Report (TSR) or chain of documents.
        Your task is to extract BOTH:
        1. Property Details: Extract the property address, plot/flat details, area, and boundaries. Extract these in UNICODE HINDI.
        2. Title Chain: Extract the complete, highly accurate CHRONOLOGICAL History of Title / Chain of Ownership of the property. Extract the title chain names and text in ENGLISH-FIRST (they will be translated to Hindi later).

        LINKAGE & CHAIN OF CUSTODY RULE:
        Every title flow is a continuous chain of custody. Ensure that the Claimant (Buyer/Allottee/Heir) of Event N matches the Executant (Seller/Giver/Deceased) of Event N+1. If there is a gap (e.g. Person A acquires the property, but later Person B sells it), carefully search the text to find the bridging event (such as a Will, Death/Succession, Gift, or Power of Attorney) and extract it!

        MAP TO SPECIFIC TEMPLATE KEYS:
        MAP TO SPECIFIC TEMPLATE KEYS:
        Classify each event and populate its matching template fields:
        1. ALLOTMENT_SOCIETY: Society allotment. Requires: "receipt_no" (receipt number), "receipt_date" (DD.MM.YYYY).
        2. DEATH_HEIRS_WITH_SPOUSE: Demise of owner and spouse. Requires: "wife_name", "wife_death_date" (DD.MM.YYYY), "share_fraction" (fraction/percentage, e.g., '1/2' or 'अविभाजित').
        3. DEATH_HEIRS_SINGLE: Demise of single owner. Requires: "share_fraction".
        4. DEATH_DIVIDED: Demise of owner with physical divided portions given to heirs. Requires: "husband_name", "husband_death_date" (DD.MM.YYYY), "east_owner", "west_owner".
        5. HAK_TYAG: Relinquishment deed. Requires: "share_fraction".
        6. AGRICULTURAL_ALLOTMENT: Revenue record allotment. Requires: "khata_no", "khasra_no", "rakba", "share_fraction".
        7. POA_AGRICULTURAL: Power of attorney for agricultural land. Requires: "khasra_no", "rakba", "share_fraction", "co_owner".
        8. POA_NON_AGRICULTURAL: Standard registered POA. Requires: "share_fraction".
        9. COLONY_DEVELOPMENT: Plot sub-division event. Requires: "owner_name", "share_fraction".
        10. DEVELOPER_AGREEMENT: Development agreement. Requires: "share_fraction".
        11. PART_SALE: Sale deed transferring partial share. Requires: "share_fraction".
        12. TRANSFER_CERTIFICATE: Transfer certificate with receipt. Requires: "receipt_no", "receipt_date" (DD.MM.YYYY).
        13. GIFT_DEED: Registered Gift deed. Requires: "parent_property_info" (parent plot/land info).
        14. WILL: Registered/unregistered Will. Requires: "will_type" (Registered/Unregistered), "death_date" (DD.MM.YYYY of testator).
        15. PARTITION: Partition deed. Requires: "share_fraction".
        16. ALLOTMENT_PLOT / ALLOTMENT_FLAT: Plot or Flat allotment by local authority (e.g. JDA/NNJ/UIT). IMPORTANT: In Rajasthan, these allotments/lease deeds/pattas are almost always registered documents. You MUST extract their registration details (reg_office, reg_date, reg_book, reg_vol, reg_page, reg_no, reg_add_book, reg_add_vol, reg_add_page) if present in the text!
        17. LEASE_DEED: Allotment / Lease deed by Rajasthan Housing Board (RHB). These are also registered and require extracting all registration details!
        18. CONSTRUCTION_FLAT: Multi-story building construction. Requires: "project_name", "unit_number".
        19. SALE_DEED_PLOT / SALE_DEED_FLAT: Standard registered sale deed of plot or flat.

        MAP EVENT TYPES:
        Each event MUST have an "event_type" mapping to one of: ALLOTMENT, CONSTRUCTION, SALE_DEED, WILL, DEATH, HAK_TYAG, POA, or TRANSFER.

        ENGLISH-FIRST EXTRACTION RULE FOR TITLE CHAIN:
        To maximize parsing accuracy and avoid cognitive overload, extract all names ("executant_name", "claimant_name", "wife_name", "husband_name", "east_owner", "west_owner", "owner_name", "co_owner"), document types ("document_name"), and registrar offices ("reg_office") in ENGLISH, EXACTLY as written in the report. They will be translated/transliterated to Hindi in a subsequent dedicated step.

        JSON FORMAT SPECIFICATION:
        Return ONLY a JSON object with EXACTLY three keys:
        1. "ps": An array containing exactly one object with property details:
           - adr: Full address (Unicode Hindi)
           - plot_no: Plot/Flat/Unit number (e.g., "A-24" or "S-1")
           - floor: Floor description (Unicode Hindi, e.g., "सेकंड फ्लोर")
           - building_name: Building/Society/Complex name (Unicode Hindi)
           - land_area: Area of the ORIGINAL PLOT with unit (e.g., "183.33 वर्गगज")
           - const_area: Super Built-up/Construction area of the flat (e.g., "1087.19 वर्ग फीट")
           - unit: Unit for land_area (e.g., "वर्ग गज")
           - const_unit: Unit for const_area (e.g., "वर्ग फीट")
           - n: North boundary of the ORIGINAL PLOT (Unicode Hindi)
           - s: South boundary of the ORIGINAL PLOT (Unicode Hindi)
           - e: East boundary of the ORIGINAL PLOT (Unicode Hindi)
           - w: West boundary of the ORIGINAL PLOT (Unicode Hindi)
        2. "chronological_analysis": A detailed, step-by-step text description showing your legal reasoning, how you traced the property chain of custody, how you resolved any name/title gaps, and how you mapped each event to a template.
        3. "title_chain": An array of objects sorted chronologically (oldest first) containing the following fields:
           - template_key: (String, one of the 19 keys listed above, e.g. "ALLOTMENT_SOCIETY")
           - event_type: (String, ALLOTMENT, CONSTRUCTION, SALE_DEED, WILL, DEATH, HAK_TYAG, POA, TRANSFER)
           - document_name: (String, e.g., 'Sale Deed', 'Allotment Letter', 'Death/Succession', 'Power of Attorney')
           - document_number: (String, e.g., 'D-2341')
           - date: (String, DD.MM.YYYY format. Convert e.g., '11th July, 2019' to '11.07.2019'. Leave blank "" if not found)
           - executant_name: (String, Seller/Principal/Authority in English)
           - claimant_name: (String, Buyer/Attorney/Allottee/Heir in English)
           - is_registered: (String, "true" or "false")
           - reg_office: (String, Registrar office in English, e.g., 'Sub-Registrar Jaipur-VII')
           - reg_date: (String, DD.MM.YYYY format)
           - reg_book, reg_vol, reg_page: (String, numbers or Roman numerals, e.g. '1', '464', 'I')
           - reg_no: (String, registration number or 15-digit E-Panjiyan sequence, e.g., '4321' or '201803021103534')
           - reg_add_book, reg_add_vol: (String, numbers or Roman numerals, e.g. '1', '1855', 'I')
           - reg_add_page: (String, page range or single page, e.g., '1026-1039' or '98')
           - consideration_amount: (String, numbers only)
           - project_name: (String, e.g., 'Royal Enclave' - for CONSTRUCTION only)
           - unit_number: (String, e.g., 'S-1' - for CONSTRUCTION only)
           - share_fraction: (String, e.g. '1/2', 'undivided' - where applicable)
           - wife_name: (String, where applicable)
           - wife_death_date: (String, DD.MM.YYYY)
           - husband_name: (String, where applicable)
           - husband_death_date: (String, DD.MM.YYYY)
           - east_owner: (String, where applicable)
           - west_owner: (String, where applicable)
           - khata_no: (String, where applicable)
           - khasra_no: (String, where applicable)
           - rakba: (String, where applicable)
           - co_owner: (String, where applicable)
           - possession_no: (String, possession letter number, e.g., '1234' - where applicable)
           - possession_date: (String, possession date in DD.MM.YYYY, e.g., '17.04.2018' - where applicable)
           - nodues_date: (String, no dues certificate date in DD.MM.YYYY, e.g., '17.04.2018' - where applicable)
           - lease_date: (String, perpetual lease deed date in DD.MM.YYYY, e.g., '17.04.2018' - where applicable)
           - conveyance_date: (String, conveyance deed/allottee date in DD.MM.YYYY, e.g., '17.04.2018' - where applicable)
           - reg_add_serial: (String, registration additional serial/file number, e.g., '1234' - where applicable)
           - conv_reg_book: (String, Conveyance Deed registration book, e.g., 'I' or '1' - where applicable)
           - conv_reg_vol: (String, Conveyance Deed registration volume, e.g., '1855' - where applicable)
           - conv_reg_page: (String, Conveyance Deed registration page, e.g., '1026' - where applicable)
           - conv_reg_no: (String, Conveyance Deed registration number, e.g., '201803021103534' - where applicable)
           - conv_reg_add_book: (String, Conveyance Deed registration additional book, e.g., 'I' - where applicable)
           - conv_reg_add_vol: (String, Conveyance Deed registration additional volume, e.g., '1858' - where applicable)
           - conv_reg_add_serial: (String, Conveyance Deed registration additional serial, e.g., '494' - where applicable)
           - conv_reg_add_page_start: (String, Conveyance Deed registration additional page start, e.g., '494' - where applicable)
           - conv_reg_add_page_end: (String, Conveyance Deed registration additional page end, e.g., '507' - where applicable)
           - owner_name: (String, where applicable)
           - parent_property_info: (String, where applicable)
           - will_type: (String, 'Registered' or 'Unregistered')
           - death_date: (String, DD.MM.YYYY)
           - receipt_no: (String, where applicable)
           - receipt_date: (String, DD.MM.YYYY)
           - confidence: (String, 'High', 'Medium', 'Low')
           - source_text: (String, exact 1-2 sentences from English report proving this event)

        CRITICAL RULES:
        1. REGISTRATION DETAILS RULE: For EVERY event in the title chain (including Sale Deeds, Lease Deeds, Gift Deeds, Hak Tyags, Power of Attorneys, or any other document), if the text indicates it was registered, you MUST extract all registration details (reg_office, reg_date, reg_book, reg_vol, reg_page, reg_no, reg_add_book, reg_add_vol, reg_add_page). Never leave these blank if they are present in the text!
        2. DO NOT SKIP ANY TRANSFERS. Every link must be represented.
        3. DO NOT HALLUCINATE DATES OR KEYS. If a specific field is not found in the text, leave it blank "".
        4. Return ONLY valid, parseable JSON. No conversational text outside JSON.
        """

    def _build_ats_prompt(self):
        return """
        Extract Consideration and Transaction details from this Agreement to Sell (ATS). Return ONLY a JSON object.
        IMPORTANT: Extract descriptive text in UNICODE HINDI.

        JSON STRUCTURE:
        {
          "amount": "Consideration Amount (digits only)",
          "amount_words": "Amount in Words (Unicode Hindi)",
          "consideration": "Consideration details/value (Unicode Hindi)"
        }
        """

    def _build_title_prompt(self):
        return """
        Extract Site Plan dimensions and property verification details from this Title Document/Site Plan. Return ONLY a JSON object.
        IMPORTANT: Extract descriptive text in UNICODE HINDI.

        JSON STRUCTURE:
        {
          "ps": [{
            "east_west_dim": "East-to-West dimensions specifically from Site Plan (e.g. 'पूर्व से पश्चिम : 30 ft')",
            "north_south_dim": "North-to-South dimensions specifically from Site Plan (e.g. 'उत्तर से दक्षिण : 50 ft')",
            "length_ew": "East-West dimension of the ORIGINAL PLOT (e.g. '30 फ़ीट')",
            "length_ns": "North-South dimension of the ORIGINAL PLOT (e.g. '55 फ़ीट')",
            "adr": "Full property address",
            "land_area": "Area of ORIGINAL PLOT",
            "n": "North boundary",
            "s": "South boundary",
            "e": "East boundary",
            "w": "West boundary"
          }]
        }
        """

    def _normalize_final_data(self, data, expected_sellers, expected_buyers, expected_witnesses):
        # Apply the same normalization as the legacy method
        self._normalize_list(data, "ss", ["n", "n_en", "a", "dob", "c", "relation_text", "rn_en", "adr", "adr_en", "id", "pan"])
        self._normalize_list(data, "bs", ["n", "n_en", "a", "dob", "c", "relation_text", "rn_en", "adr", "adr_en", "id", "pan"])
        self._normalize_list(data, "ps", ["adr", "adr_en", "flat_no", "plot_no", "floor", "building_name", "project_name", "lease_deed_no", "document_number", "scheme", "village", "tehsil", "dist", "state", "land_area", "const_area", "unit", "const_unit", "n", "s", "e", "w", "ward", "khasra", "length_ew", "length_ns", "east_west_dim", "north_south_dim", "parking_type", "parking_number", "area_type", "covered_area", "property_portion"])
        self._normalize_list(data, "ws", ["n", "n_en", "dob", "relation_text", "rn_en", "adr", "adr_en"])

        import re
        for key in ["ss", "bs", "ws", "unassigned_aadhars"]:
            for person in data.get(key, []):
                if person.get("n"):
                    person["n"] = re.sub(r',\s*$', '', person["n"]).strip()
                if person.get("n_en"):
                    person["n_en"] = re.sub(r',\s*$', '', person["n_en"]).strip().upper()
                if person.get("rn_en"):
                    person["rn_en"] = person["rn_en"].strip().upper()
                if person.get("adr_en"):
                    person["adr_en"] = person["adr_en"].strip().upper()
                if person.get("dob"):
                    person["dob"] = person["dob"].strip()
                if person.get("relation_text"):
                    from utils.helpers import normalize_relation_prefix, parse_relation_text
                    person["relation_text"] = normalize_relation_prefix(person["relation_text"], "SD")
                    person["r"], person["rn"] = parse_relation_text(person["relation_text"])

        self._normalize_list(data, "unassigned_aadhars", ["s", "n", "n_en", "a", "dob", "r", "rn", "rn_en", "relation_text", "adr", "adr_en", "id"])

        self._normalize_list(data, "title_chain", [
            "template_key", "event_type", "document_name", "document_number", "date", "consideration_amount", 
            "executant_name", "claimant_name", "reg_office", "reg_date", 
            "reg_book", "reg_vol", "reg_page", "reg_no", "reg_add_book", "reg_add_vol", "reg_add_page", 
            "book_no", "volume_no", "page_no", "additional_book_no", "additional_volume_no", "additional_page_range",
            "confidence", "source_text", "is_registered", "project_name", "unit_number", "field_sources", "event_property_type",
            "share_fraction", "wife_name", "wife_death_date", "husband_name", "husband_death_date", 
            "east_owner", "west_owner", "khata_no", "khasra_no", "rakba", "co_owner", "owner_name", 
            "parent_property_info", "will_type", "death_date", "receipt_no", "receipt_date",
            "possession_no", "possession_date", "nodues_date", "lease_date", "conveyance_date",
            "reg_add_serial", "conv_reg_book", "conv_reg_vol", "conv_reg_page", "conv_reg_no",
            "conv_reg_add_book", "conv_reg_add_vol", "conv_reg_add_serial",
            "conv_reg_add_page_start", "conv_reg_add_page_end"
        ])

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
        IMPORTANT: Extract all Hindi descriptive fields in UNICODE HINDI script, AND extract their transliterated/English counterparts in UPPERCASE ENGLISH script (standard Roman alphabet) inside the respective '_en' fields.
        
        JSON STRUCTURE:
        {
          "rd": "Date of Execution of the CURRENT document being drafted (e.g. today's date if drafting a new deed, or the exact execution date specified in the Sale Deed. DO NOT use the Agreement to Sell date).",
          "amount": "Consideration Amount (digits only, e.g. '1500000')",
          "amount_words": "Amount in Words (Unicode Hindi, e.g. 'पंद्रह लाख')",
          "consideration": "Consideration details/value (Unicode Hindi)",
          "tds": "TDS details (Unicode Hindi, e.g., if consideration is >= 50 Lakhs)",
          "hypothecation": "Existing Mortgage Bank Name (Unicode Hindi)",
          "ss": [{"n":"Name in Hindi", "n_en":"Name in English script", "a":"Age", "dob":"Date of Birth (DD/MM/YYYY or YYYY if only year is printed)", "c":"Caste", "relation_text":"Complete Relation Phrase in Hindi (e.g. 'पुत्र श्री भीवा राम')", "rn_en":"Relative Father/Husband Name in English script (e.g. 'BHEEVA RAM')", "adr":"Address in Hindi", "adr_en":"Address in English script", "id":"Aadhar", "pan":"PAN", "is_bpl":"true/false (if buyer belongs to BPL)"}],
          "bs": [{"n":"Name in Hindi", "n_en":"Name in English script", "a":"Age", "dob":"Date of Birth (DD/MM/YYYY or YYYY if only year is printed)", "c":"Caste", "relation_text":"Complete Relation Phrase in Hindi (e.g. 'पुत्री श्री रामअवतार मीणा')", "rn_en":"Relative Father/Husband Name in English script (e.g. 'RAMAVTAR MEENA')", "adr":"Address in Hindi", "adr_en":"Address in English script", "id":"Aadhar", "pan":"PAN", "is_bpl":"true/false (if buyer belongs to BPL)"}],
          "ps": [{
            "adr": "Full address in Hindi (Unicode Hindi)",
            "adr_en": "Full address in English script (e.g. 'PLOT NO. 12, PATRAKAR COLONY, MANSAROVAR, JAIPUR')",
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
            "property_portion": "Portion of the property being sold",
            "lat": "Latitude coordinate from maps or documents (e.g. '26.949441')",
            "lng": "Longitude coordinate from maps or documents (e.g. '75.678939')",
            "road_width": "Width of boundary road in feet next to property (e.g. '30')"
          }],
          "ws": [{"n":"Name in Hindi", "n_en":"Name in English script", "relation_text":"Complete Relation Phrase in Hindi (e.g. 'पुत्र श्री रामेश्वर प्रसाद')", "rn_en":"Relative Father Name in English script (e.g. 'RAMESHWAR PRASAD')", "adr":"Address in Hindi", "adr_en":"Address in English script", "dob":"Date of Birth (DD/MM/YYYY or YYYY if only year is printed)"}],
          "title_chain": [{"template_key":"Specific template key (e.g. 'SALE_DEED_PLOT', 'ALLOTMENT_SOCIETY')", "event_type":"SALE_DEED|ALLOTMENT|CONSTRUCTION|POA|RELINQUISHMENT|CORRECTION_DEED|TRANSFER", "document_name":"हिंदी Doc Name (e.g. 'विक्रय पत्र')", "date":"DD.MM.YYYY", "consideration_amount":"digits", "executant_name":"Seller/Authority (Unicode Hindi)", "claimant_name":"Buyer/Allottee (Unicode Hindi)", "is_registered":"true/false", "reg_office":"Office (Hindi)", "reg_date":"DD.MM.YYYY", "reg_book":"#", "reg_vol":"#", "reg_page":"#", "reg_no":"#", "reg_add_book":"#", "reg_add_vol":"#", "reg_add_page":"1026-1039 (number or range)", "project_name":"Name if CONSTRUCTION (Unicode Hindi, e.g. 'रॉयल एन्क्लेव')", "unit_number":"Unit/Flat No if CONSTRUCTION (Unicode Hindi, e.g. 'एस-1')", "confidence":"High/Medium/Low", "source_text":"exact source text", "share_fraction":"e.g. '1/2', 'undivided'", "wife_name":"where applicable", "wife_death_date":"DD.MM.YYYY", "husband_name":"where applicable", "husband_death_date":"DD.MM.YYYY", "east_owner":"where applicable", "west_owner":"where applicable", "khata_no":"where applicable", "khasra_no":"where applicable", "rakba":"where applicable", "co_owner":"where applicable", "owner_name":"where applicable", "parent_property_info":"where applicable", "will_type":"'Registered' or 'Unregistered'", "death_date":"DD.MM.YYYY", "receipt_no":"where applicable", "receipt_date":"DD.MM.YYYY"}],
          "reg": {"office":"Name", "book":"#", "vol":"#", "page":"#", "reg_no":"#", "reg_date":"Date"},
          "unassigned_aadhars": [{"s":"Mr/Mrs/Ms", "n":"Name in Hindi", "n_en":"Name in English script", "a":"Age", "dob":"Date of Birth (DD/MM/YYYY or YYYY if only year is printed)", "relation_text":"Complete Relation Phrase in Hindi", "rn_en":"Relative Father/Husband Name in English script", "adr":"Address in Hindi", "adr_en":"Address in English script", "id":"Aadhar"}]
        }

        RULES:
        1. NO HALLUCINATION. If missing, use "".
        2. MANDATORY HINDI SCRIPT: You MUST use Unicode Hindi (Devanagari script) for ALL Hindi descriptive fields.
        2b. ENGLISH SCRIPT COUNTERPARTS: For every person (buyers, sellers, witnesses, unassigned aadhars) and property address, you must extract/transliterate their corresponding English names, relative names, and addresses into UPPERCASE ENGLISH script (standard Roman alphabet) inside the respective '_en' fields.
           - Correct Name: 'रामकुमार शर्मा' vs 'RAMKUMAR SHARMA'
           - Correct Address: '१२३, मालवीय नगर, जयपुर' vs '123, MALVIYA NAGAR, JAIPUR'
           - Correct Relation Name: 'बनवारी लाल' vs 'BANWARI LAL'
        3. COUNTS: "ss" exactly selected count. "bs" exactly selected count. "ws" exactly 2.
        4. AADHAAR CARDS: Extract details from Aadhaar cards into 'unassigned_aadhars' ONLY.
        4b. WITNESS OCR ISOLATION: STRICTLY DO NOT extract witness details (names, addresses, Aadhaar, relation data) into 'unassigned_aadhars' or any other OCR sections. If an Aadhaar card belongs to a witness, do not extract it or include it in 'unassigned_aadhars'.
        5. BOUNDARIES: Extract the four boundary directions of the ORIGINAL PLOT from chain-of-title descriptions. Map to e, w, n, s. These are found in sentences like 'जिसकी चारों सीमाएं...' or 'पूर्व की ओर... पश्चिम की ओर...' etc.
        5b. DIMENSIONS: Extract length_ew (East-West) and length_ns (North-South) of the ORIGINAL PLOT from chain docs. These appear as 'पूर्व से पश्चिम XX फीट एवं उत्तर से दक्षिण XX फीट है'. land_area is the total plot area in sq. yards.
        6. RELATIONS & ADDRESSES: The first line on the back of an Aadhaar card is often the relation (e.g. S/o, C/o, W/o, D/o). YOU MUST SEPARATE THIS. Put the relation entirely in `relation_text` and only put the actual address in `adr`.
        6b. STRICT HINDI RELATION FORMATTING: ALWAYS format relations using exact Unicode Hindi (e.g. 'पुत्र श्री मोहनलाल', 'पत्नी श्री रामलाल', 'पुत्र स्वर्गीय श्री गंगाराम', 'पुत्री श्री ...'). NEVER output "S/O", "W/O", or "C/O".
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
        
        self._normalize_list(data, "ss", ["n", "n_en", "a", "c", "relation_text", "rn_en", "adr", "adr_en", "id", "pan", "is_bpl"])
        self._normalize_list(data, "bs", ["n", "n_en", "a", "c", "relation_text", "rn_en", "adr", "adr_en", "id", "pan", "is_bpl"])
        self._normalize_list(data, "ps", ["adr", "adr_en", "flat_no", "plot_no", "floor", "building_name", "project_name", "lease_deed_no", "document_number", "scheme", "village", "tehsil", "dist", "state", "land_area", "const_area", "unit", "const_unit", "n", "s", "e", "w", "ward", "khasra", "length_ew", "length_ns", "parking_type", "parking_number", "area_type", "covered_area", "property_portion", "lat", "lng", "road_width"])
        self._normalize_list(data, "ws", ["n", "n_en", "relation_text", "rn_en", "adr", "adr_en"])

        # Move extraction-compensation upstream (cleaning OCR commas between names and relations)
        for key in ["ss", "bs", "ws", "unassigned_aadhars"]:
            for person in data.get(key, []):
                if person.get("n"):
                    person["n"] = re.sub(r',\s*$', '', person["n"]).strip()
                if person.get("n_en"):
                    person["n_en"] = re.sub(r',\s*$', '', person["n_en"]).strip().upper()
                if person.get("rn_en"):
                    person["rn_en"] = person["rn_en"].strip().upper()
                if person.get("adr_en"):
                    person["adr_en"] = person["adr_en"].strip().upper()
                if person.get("relation_text"):
                    from utils.helpers import parse_relation_text
                    person["relation_text"] = normalize_relation_prefix(person["relation_text"], "SD")
                    person["r"], person["rn"] = parse_relation_text(person["relation_text"])

        self._normalize_list(data, "title_chain", [
            "template_key", "event_type", "document_name", "document_number", "date", "consideration_amount", 
            "executant_name", "claimant_name", "reg_office", "reg_date", 
            "reg_book", "reg_vol", "reg_page", "reg_no", "reg_add_book", "reg_add_vol", "reg_add_page", 
            "book_no", "volume_no", "page_no", "additional_book_no", "additional_volume_no", "additional_page_range",
            "confidence", "source_text", "is_registered", "project_name", "unit_number", "field_sources", "event_property_type",
            "share_fraction", "wife_name", "wife_death_date", "husband_name", "husband_death_date", 
            "east_owner", "west_owner", "khata_no", "khasra_no", "rakba", "co_owner", "owner_name", 
            "parent_property_info", "will_type", "death_date", "receipt_no", "receipt_date",
            "possession_no", "possession_date", "nodues_date", "lease_date", "conveyance_date",
            "reg_add_serial", "conv_reg_book", "conv_reg_vol", "conv_reg_page", "conv_reg_no",
            "conv_reg_add_book", "conv_reg_add_vol", "conv_reg_add_serial",
            "conv_reg_add_page_start", "conv_reg_add_page_end"
        ])
        
        self._normalize_list(data, "unassigned_aadhars", ["s", "n", "n_en", "a", "r", "rn", "rn_en", "relation_text", "adr", "adr_en", "id", "pan", "is_bpl"])
        
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

        self._force_count(data, "ss", ["n", "n_en", "a", "c", "relation_text", "rn_en", "adr", "adr_en", "id", "pan", "is_bpl"], expected_sellers)
        self._force_count(data, "bs", ["n", "n_en", "a", "c", "relation_text", "rn_en", "adr", "adr_en", "id", "pan", "is_bpl"], expected_buyers)
        self._force_count(data, "ws", ["n", "n_en", "relation_text", "rn_en", "adr", "adr_en"], expected_witnesses)
        
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
