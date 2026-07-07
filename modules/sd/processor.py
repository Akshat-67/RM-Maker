import os
import re
import zipfile
from html import unescape
from docxtpl import DocxTemplate, RichText
from docx.enum.text import WD_COLOR_INDEX
from docx.shared import RGBColor

from utils.helpers import (
    Unicode_to_KrutiDev,
    extract_salutation_and_name,
    normalize_relative_salutation,
    normalize_name_salutation,
    parse_relation_text,
    normalize_relation_prefix
)

HL_MARKER = "~~HL~~"
# Safe ASCII sentinel that won't appear naturally in any string and survives DevLys conversion
_HL_SENTINEL = "\x01HLMARK\x01"

def is_text_devlys(text):
    if not text:
        return False
    text_stripped = text.strip()
    # Explicitly ignore single letters or small Roman numerals to prevent DevLys font application
    if text_stripped.upper() in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "A", "B", "C", "D"]:
        return False
    # If it contains Hindi Unicode characters (Devanagari block), it is NOT DevLys
    if any(0x0900 <= ord(c) <= 0x097F for c in text):
        return False
        
    # Check for presence of common DevLys indicators
    devlys_indicators = [
        "fuoklh", "iq=", "gS", "foØsrk", "Øsrk", "lk{kh", "fy[kar", "iêk", "iV~Vk", 
        "eSus", "le>dj", "izFke", "fLFkr", "uxj", "rglhy", "ftyk", "jktLFkku",
        "Jhefrh", "fnukad", "foØsrkx.k", "Øsrkx.k", "iRuh", "Jh", "LoxhZ;", "Hkwfe",
        "dksbZ", "n{k.k", "mRrj", "iwoZ", "if'pe", "jkf'k", "vk/kkj", "uEcj", 
        "iSu", "vk;q", "tkfr", "¶ySV", "IykV", "eSllZ", "o\"kZ",
        "okgu", "ikfdZax", "fgLls", "eqcfyx", "t;iqj", "vtesj", "c['kh", "eq'rd"
    ]
    text_lower = text.lower()
    for ind in devlys_indicators:
        if ind.lower() in text_lower:
            return True
            
    # DevLys specific character presence (typical non-ascii character set used in mapping)
    devlys_chars = "Øæçè½¾ßáâãäåæçèéêëìíîïñòóôõö÷ùúûüýþÿ"
    if any(c in text for c in devlys_chars):
        return True
        
    # DevLys common special character/punctuation mappings
    devlys_special = "{}~`*\\|@"
    if any(c in text for c in devlys_special):
        return True
        
    # Check for the common DevLys vowel sign pattern: 'f' followed by a consonant or sign mapping (e.g. fd, fo, fy, ft, etc.)
    # Exclude standard English 'fe', 'fa' from matching as DevLys
    if re.search(r'f[b-df-hj-np-tv-zBCDFGHJKLMNPQRSTVWXYZ\[\]\{\}\;\:\'\"\,\<\.\>\/\?\`\~\!\@\#\$\%\^\&\*\(\)\_\+\-\=\|]', text):
        return True
        
    # Check if text is pure digits and common separators (matches Hindi font size properly)
    if re.match(r'^[\d\s\-\.,]+$', text.strip()):
        return True
        
    return False

def coerce_roman_in_text(text):
    if not isinstance(text, str):
        return text
    roman_map = {
        "I": "01", "II": "02", "III": "03", "IV": "04", "V": "05",
        "VI": "06", "VII": "07", "VIII": "08", "IX": "09", "X": "10"
    }
    # Keyword + separator + roman numeral. Avoid lookbehind: Python requires
    # fixed-width lookbehinds, while these keywords have different lengths.
    pattern = r'\b(पुस्तक|जिल्द|बुक|book|vol|volume|no|number|संख्या|दस्तावेज|दस्तावेज़|रजिस्ट्री)([:\-\s#\.]*)(I|II|III|IV|V|VI|VII|VIII|IX|X)\b'
    def repl(match):
        val = match.group(3).upper()
        return f"{match.group(1)}{match.group(2)}{roman_map.get(val, match.group(3))}"
    res = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    if res.strip().upper() in roman_map:
        res = roman_map[res.strip().upper()]
    return res

class SDTemplateProcessor:
    def __init__(self, template_path):
        self.template_path = template_path
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found at {template_path}")
        self.doc = DocxTemplate(template_path)

    def _convert_context_to_legacy(self, data):
        """Recursively scans context and encodes Hindi Unicode fields to DevLys ASCII."""
        if isinstance(data, dict):
            cleaned = {}
            for k, v in data.items():
                if k in ["reg_book", "reg_add_book", "book_no", "additional_book_no", "b_no"] and isinstance(v, str):
                    v_upper = v.strip().upper()
                    roman_map = {
                        "I": "01", "II": "02", "III": "03", "IV": "04", "V": "05",
                        "VI": "06", "VII": "07", "VIII": "08", "IX": "09", "X": "10"
                    }
                    if v_upper in roman_map:
                        v = roman_map[v_upper]
                cleaned[k] = self._convert_context_to_legacy(v)
            return cleaned
        elif isinstance(data, list):
            return [self._convert_context_to_legacy(x) for x in data]
        elif isinstance(data, str):
            # Coerce Roman numerals in general text fields to digits prior to conversion
            data = coerce_roman_in_text(data)
            # Sanitize control characters that break docx (but preserve our sentinel)
            data = re.sub(r'[^\x01\x09\x0A\x0D\x20-\x7E\x85\xA0-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]', '', data)
            # If standard English (no Hindi Unicode), return directly without DevLys encoding
            if not any(ord(char) > 127 for char in data):
                return data
            # Protect HL markers before DevLys conversion
            has_markers = _HL_SENTINEL in data or HL_MARKER in data
            if has_markers:
                data = data.replace(HL_MARKER, _HL_SENTINEL)
            val = Unicode_to_KrutiDev(data)
            val = val.replace("&", "&amp;")
            # Restore markers after DevLys conversion
            if has_markers:
                val = val.replace(_HL_SENTINEL, HL_MARKER)
            
            # 1. Newlines handling
            if '\n' in val:
                # We return it as is, and handle it during placeholder replacement in generate()
                return val
            return val
        else:
            return data

    def _template_xml(self):
        parts = []
        with zipfile.ZipFile(self.template_path) as zf:
            for name in zf.namelist():
                if name.startswith("word/") and name.endswith(".xml"):
                    xml = zf.read(name).decode("utf-8", errors="ignore")
                    parts.append(re.sub(r"<[^>]+>", "", xml))
        return unescape("\n".join(parts))

    def _required_list_lengths(self):
        required = {}
        for list_name, index in re.findall(r"\b(ss|bs|ls|ps|ws|ds)\s*\[\s*(\d+)\s*\]", self._template_xml()):
            required[list_name] = max(required.get(list_name, 0), int(index) + 1)
        return required

    def _pad_indexed_lists(self, context):
        defaults = {
            "ss": {"s": "", "n": "", "a": "", "c": "", "r": "", "rn": "", "relation_text": "", "adr": "", "id": "", "pan": ""},
            "bs": {"s": "", "n": "", "a": "", "c": "", "r": "", "rn": "", "relation_text": "", "adr": "", "id": "", "pan": ""},
            "ls": {"n": "", "a": "", "w": "", "t": ""},
            "ps": {"adr": "", "n": "", "s": "", "e": "", "w": "", "lease_deed_no": "", "plot_no": "", "scheme": "", "village": "", "tehsil": "", "dist": "", "land_area": "", "const_area": "", "unit": ""},
            "ws": {"n": "", "r": "", "rn": "", "relation_text": "", "adr": ""},
            "ds": {"t": ""}
        }
        for list_name, size in self._required_list_lengths().items():
            values = context.get(list_name)
            if not isinstance(values, list):
                values = []
            while len(values) < size:
                values.append(defaults[list_name].copy())
            context[list_name] = values
        return context

    def _normalize_context_salutations(self, context):
        contexts_to_clean = [context]
        if 'd' in context and isinstance(context['d'], dict):
            contexts_to_clean.append(context['d'])

        doc_type = "SD"
        for ctx in contexts_to_clean:
            if "ws" in ctx and isinstance(ctx["ws"], list):
                for w in ctx["ws"]:
                    if isinstance(w, dict):
                        if w.get("r"): w["r"] = normalize_relation_prefix(w["r"], doc_type)
                        if w.get("r") and w.get("rn") and not w.get("relation_text"):
                            w["relation_text"] = f"{w['r']} {w['rn']}"
                        elif w.get("relation_text"):
                            r, rn = parse_relation_text(w["relation_text"])
                            w["r"] = r
                            w["rn"] = rn
                        if w.get("n"):
                            is_male = True
                            if w.get("s") and any(x in w.get("s").lower() for x in ["श्रीमती", "mrs", "ms", "सुश्री", "female"]):
                                is_male = False
                            w["n"] = normalize_name_salutation(w["n"], w.get("r"), default_to_male=is_male)

            sellers_list = ctx.get("ss") or ctx.get("sellers")
            if sellers_list and isinstance(sellers_list, list):
                for s in sellers_list:
                    if isinstance(s, dict):
                        if s.get("r"): s["r"] = normalize_relation_prefix(s["r"], doc_type)
                        if s.get("r") and s.get("rn") and not s.get("relation_text"):
                            s["relation_text"] = f"{s['r']} {s['rn']}"
                        elif s.get("relation_text"):
                            r, rn = parse_relation_text(s["relation_text"])
                            s["r"] = r
                            s["rn"] = rn
                        if s.get("n"):
                            is_male = True
                            if s.get("s") and any(x in s.get("s").lower() for x in ["श्रीमती", "mrs", "ms", "सुश्री", "female"]):
                                is_male = False
                            s["n"] = normalize_name_salutation(s["n"], s.get("r"), default_to_male=is_male)

            buyers_list = ctx.get("bs") or ctx.get("buyers")
            if buyers_list and isinstance(buyers_list, list):
                for b in buyers_list:
                    if isinstance(b, dict):
                        if b.get("r"): b["r"] = normalize_relation_prefix(b["r"], doc_type)
                        if b.get("r") and b.get("rn") and not b.get("relation_text"):
                            b["relation_text"] = f"{b['r']} {b['rn']}"
                        elif b.get("relation_text"):
                            r, rn = parse_relation_text(b["relation_text"])
                            b["r"] = r
                            b["rn"] = rn
                        if b.get("n"):
                            is_male = True
                            if b.get("s") and any(x in b.get("s").lower() for x in ["श्रीमती", "mrs", "ms", "सुश्री", "female"]):
                                is_male = False
                            b["n"] = normalize_name_salutation(b["n"], b.get("r"), default_to_male=is_male)

    def generate(self, context, output_path, highlight_ai=False, highlight_missing=False, verified_fields=None):
        if verified_fields is None: verified_fields = set()
        d_ctx = context.get('d')
        if d_ctx is None:
            d_ctx = context.copy()
            context['d'] = d_ctx
        
        # SD compatibility keys
        if 'sale' not in context:
            context['sale'] = {}
        if 'amount' not in context['sale']:
            context['sale']['amount'] = context.get('amount', d_ctx.get('amount', ''))
        if 'amount_words' not in context['sale']:
            context['sale']['amount_words'] = context.get('amount_words', d_ctx.get('amount_words', ''))

        payments_list = context.get('payments') or d_ctx.get('payments') or []
        
        # Build text description of payments for text placeholders (e.g. Vivek Saxena)
        payment_lines = []
        for idx, p in enumerate(payments_list):
            line = f"{idx+1}. {p.get('a', '')} "
            details = []
            if p.get('n'):
                details.append(p.get('n'))
            if p.get('d'):
                details.append(f"दिनांक {p.get('d')}")
            if p.get('b'):
                details.append(p.get('b'))
            if details:
                line += "(" + " ".join(details) + ")"
            payment_lines.append(line)
        
        if payment_lines:
            context['sale']['payment_details'] = "\n".join(payment_lines)
        else:
            context['sale']['payment_details'] = "1. \n2. \n3. \n4. "

        if 'deed' not in context:
            context['deed'] = {'execution_date': context.get('rd', d_ctx.get('rd', ''))}
        
        if 'd' in context and isinstance(context['d'], dict):
            if 'sale' not in context['d']: context['d']['sale'] = context['sale']
            if 'deed' not in context['d']: context['d']['deed'] = context['deed']

        # Ensure base keys exist for empty contexts
        if 'ss' not in context: context['ss'] = context.get('sellers', [])
        if 'bs' not in context: context['bs'] = context.get('buyers', [])

        # --- Compute derived text fields if not already set ---
        # chain_text: narrative of the title chain (supports both 'title_chain' and 'chain' keys)
        # Also coerce a list chain_text (from external callers) into a joined string
        if isinstance(context.get('chain_text'), list):
            context['chain_text'] = '\n'.join(context['chain_text'])
            if 'd' in context and isinstance(context['d'], dict):
                context['d']['chain_text'] = context['chain_text']

        if not context.get('chain_text'):
            try:
                from modules.sd.narrative import generate_chain_narrative
                chain_data = context.get('title_chain') or context.get('chain') or []
                # Normalize shorthand keys used in test/simple contexts:
                # d->date, s->executant_name, b->claimant_name, r_no->reg_no, v_no->reg_vol, p_no->reg_page, b_no->reg_book
                _normalized_chain = []
                for evt in chain_data:
                    if not isinstance(evt, dict):
                        continue
                    evt_copy = evt.copy()
                    mapped_evt = {
                        'event_type': evt_copy.get('event_type') or evt_copy.get('type') or 'SALE_DEED',
                        'date': evt_copy.get('date') or evt_copy.get('d') or '',
                        'executant_name': evt_copy.get('executant_name') or evt_copy.get('s') or '',
                        'claimant_name': evt_copy.get('claimant_name') or evt_copy.get('b') or '',
                        'consideration_amount': evt_copy.get('consideration_amount') or evt_copy.get('a') or '',
                        'is_registered': evt_copy.get('is_registered') or 'true',
                        'reg_office': evt_copy.get('reg_office') or evt_copy.get('ro') or '',
                        'reg_date': evt_copy.get('reg_date') or evt_copy.get('rd') or evt_copy.get('d') or '',
                        'reg_book': evt_copy.get('reg_book') or evt_copy.get('b_no') or '',
                        'reg_vol': evt_copy.get('reg_vol') or evt_copy.get('v_no') or '',
                        'reg_page': evt_copy.get('reg_page') or evt_copy.get('p_no') or '',
                        'reg_no': evt_copy.get('reg_no') or evt_copy.get('r_no') or '',
                        'document_name': evt_copy.get('document_name') or evt_copy.get('type') or ''
                    }
                    _normalized_chain.append(mapped_evt)
                result = generate_chain_narrative(_normalized_chain, context=context)
                # generate_chain_narrative returns a list of paragraph strings — join for template
                if isinstance(result, list):
                    context['chain_text'] = '\n'.join(result)
                else:
                    context['chain_text'] = result or ''
                if 'd' in context and isinstance(context['d'], dict):
                    context['d']['chain_text'] = context['chain_text']
            except Exception:
                context['chain_text'] = ''

        # full_address, dimension_text, boundary_text for each property in ps
        if context.get('ps') and isinstance(context['ps'], list):
            try:
                from modules.sd.extractor import SDDataExtractor
                _extractor = SDDataExtractor()
                prop_type = 'Flat' if any(
                    str(p.get('flat_no', '') or p.get('adr', '')).lower().count('flat') > 0
                    for p in context['ps'] if isinstance(p, dict)
                ) else 'Plot'
                for p in context['ps']:
                    if not isinstance(p, dict):
                        continue
                    if not p.get('full_address'):
                        p['full_address'] = _extractor.generate_full_property_address(p, 'SD', prop_type)
                    if not p.get('dimension_text'):
                        p['dimension_text'] = _extractor.generate_dimension_text(p)
                    if not p.get('boundary_text'):
                        p['boundary_text'] = _extractor.generate_boundary_text(p)
                # Mirror into d.ps too
                if 'd' in context and isinstance(context['d'], dict):
                    context['d']['ps'] = context['ps']
            except Exception:
                pass

        # Compute dynamic party labels (विक्रेता / विक्रेतागण / विक्रेताती / क्रेता / क्रेतागण / क्रेती)
        def compute_party_label(party_list, party_type="seller"):
            valid_party = [p for p in party_list if isinstance(p, dict) and any(str(v).strip() for v in p.values())]
            count = len(valid_party)
            if count == 0:
                count = len(party_list)
            
            if count > 1:
                return "विक्रेतागण" if party_type == "seller" else "क्रेतागण"
            elif count == 1:
                p = valid_party[0] if valid_party else (party_list[0] if party_list else {})
                salutation = str(p.get("s") or "").strip().lower()
                rel_text = str(p.get("relation_text") or "").strip().lower()
                
                is_female = False
                if any(x in salutation for x in ["smt", "mrs", "ms", "श्रीमती", "कुमारी"]):
                    is_female = True
                elif any(x in rel_text for x in ["w/o", "d/o", "wife of", "daughter of", "पत्नी", "पुत्री"]):
                    is_female = True
                
                if is_female:
                    return "विक्रेती" if party_type == "seller" else "क्रेती"
                else:
                    return "विक्रेता" if party_type == "seller" else "क्रेता"
            return "विक्रेता" if party_type == "seller" else "क्रेता"

        computed_seller_label = compute_party_label(context.get("ss", []), "seller")
        computed_buyer_label = compute_party_label(context.get("bs", []), "buyer")

        extracted_seller_label = context.get("seller_label") or (context.get("d") or {}).get("seller_label")
        extracted_buyer_label = context.get("buyer_label") or (context.get("d") or {}).get("buyer_label")

        if not extracted_seller_label or str(extracted_seller_label).strip() in ["विक्रेता", "Seller"]:
            extracted_seller_label = computed_seller_label
        if not extracted_buyer_label or str(extracted_buyer_label).strip() in ["क्रेता", "Buyer"]:
            extracted_buyer_label = computed_buyer_label

        context["seller_label"] = str(extracted_seller_label).strip()
        context["buyer_label"] = str(extracted_buyer_label).strip()
        if 'd' in context and isinstance(context['d'], dict):
            context['d']["seller_label"] = context["seller_label"]
            context['d']["buyer_label"] = context["buyer_label"]

        # Witness compatibility mappings (w1, w2)
        if 'ws' in context and isinstance(context['ws'], list):
            ws_list = context['ws']
            if len(ws_list) > 0:
                context['w1'] = ws_list[0]
            else:
                context['w1'] = {"n": "", "relation_text": "", "address": "", "aadhaar": ""}
            if len(ws_list) > 1:
                context['w2'] = ws_list[1]
            else:
                context['w2'] = {"n": "", "relation_text": "", "address": "", "aadhaar": ""}

        self._normalize_context_salutations(context)
        self._pad_indexed_lists(d_ctx)

        if highlight_ai or highlight_missing:
            context = self._apply_highlight_markers(context, verified_fields, highlight_ai, highlight_missing)

        context = self._convert_context_to_legacy(context)
        if isinstance(context, dict):
            if "chain_text" in context and isinstance(context["chain_text"], str):
                context["chain_text"] = context["chain_text"].replace("Lo- Jh", "LoxhZ; Jh")
            if "chain_paragraphs" in context and isinstance(context["chain_paragraphs"], list):
                context["chain_paragraphs"] = [
                    p.replace("Lo- Jh", "LoxhZ; Jh") if isinstance(p, str) else p
                    for p in context["chain_paragraphs"]
                ]
                
        # 1. Render the template
        self.doc.render(context)
        
        # 2. Save rendered doc to output path
        self.doc.save(output_path)
        
        # 3. Reload the document using standard docx to refresh XML parse trees
        import docx
        doc = docx.Document(output_path)
        
        # 4. Split multi-line paragraphs
        self._split_multi_line_paragraphs(doc)

        # 5. Run character cleanups
        self._clean_all_text(doc)

        # 6. Apply dynamic payments table updates
        self._process_payment_tables_on_doc(doc, context)

        # 7. Perform robust highlight rendering and restore fonts run-by-run
        self._apply_body_highlights_and_fonts(doc, highlight_ai, highlight_missing)

        # 8. Final save
        doc.save(output_path)

    def _split_multi_line_paragraphs(self, doc):
        """Splits paragraphs containing '\n' into actual separate Word paragraphs."""
        from docx.shared import Pt
        paras = list(doc.paragraphs)
        for p in paras:
            if '\n' in p.text:
                lines = p.text.split('\n')
                p.text = lines[0]
                current_p = p
                for line in lines[1:]:
                    new_para = doc.add_paragraph("")
                    current_p._p.addnext(new_para._p)
                    new_para.text = line
                    new_para.style = p.style
                    new_para.alignment = p.alignment
                    if new_para.runs:
                        new_para.runs[0].font.name = "DevLys 040"
                        new_para.runs[0].font.size = Pt(16)
                    current_p = new_para

    def _apply_highlight_markers(self, data, verified_fields, highlight_ai, highlight_missing, path=""):
        if isinstance(data, dict):
            return {k: self._apply_highlight_markers(v, verified_fields, highlight_ai, highlight_missing, f"{path}.{k}" if path else k) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._apply_highlight_markers(x, verified_fields, highlight_ai, highlight_missing, f"{path}.{i}") for i, x in enumerate(data)]
        elif isinstance(data, str):
            if not data.strip():
                if highlight_missing and path not in verified_fields: return f"{HL_MARKER}MISSING:{path.upper()}{HL_MARKER}"
                return data
            if highlight_ai and path not in verified_fields: return f"{HL_MARKER}{data}{HL_MARKER}"
            return data
        else:
            return data

    def _clean_all_text(self, doc):
        """Applies text spelling, ligature, and format cleanups globally across all body and table cell paragraphs."""
        for paragraph in doc.paragraphs:
            self._clean_paragraph_text(paragraph)
            
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        self._clean_paragraph_text(paragraph)

    def _clean_paragraph_text(self, paragraph):
        text = paragraph.text
        original = text
        
        # 1. Identity Boilerplate Fixes
        if text.strip() == "dh vksj ls": text = "& dh vksj ls &"
        
        # 2. Ligature and Standard Substitution Fixes (Regex Robust)
        text = re.sub(r'm[RrÙ]+jkf[/èk]+dkjh', 'mÙkjkf/kdkjh', text)
        
        text = text.replace("Lo ", "Lo- ").replace("Lo- Jh", "Lo- Jh").replace("mä ", "mDr ")
        text = text.replace("iêk", "iV~Vk").replace("i+ ", "i<+ ").replace("ledj", "le>dj").replace("izek.k", "izek.k")
        text = text.replace("dksbZ", "dksÃ").replace("n{fk.k", "nf{k.k").replace("LfFkr", "fLFkr")
        
        # 3. Generic Punctuation / Spacing
        text = text.replace("gSA, ]", "gS]").replace("gSA ]", "gS]").replace("gS, ", "gS] ").replace("xokgku,", "xokgku~").replace("i'pkr,", "i'pkr~")
        
        text = text.replace('] o"kZ', ' o"kZ').replace('] tkfr', ' tkfr').replace("^^foØsrkx.k**", " ^^foØsrkx.k**")
        text = text.replace("mä foØ;", "mDr foØ;").replace("mä ;wfuV", "mDr ;wfuV")
        text = text.replace("^^Accident/¶ysV**", "^^Accident@¶ysV**").replace("^^;wfuV/¶ysV**", "^^;wfuV@¶ysV**")
        
        if "gS%" in text and "gS%&" not in text: text = text.replace("gS%", "gS%&")

        # 4. Global Character / Hyphen Cleanups
        text = re.sub(r'([^\d])(?<!\bu)(?<!\bua)\-(\s*\d)', r'\g<1>&\g<2>', text)
        text = re.sub(r'(\d)\-([^\d])', r'\g<1>&\g<2>', text)
        text = text.replace(" - ", " & ")
        
        text = text.replace("okfjlkU", "okfjlku~")
        text = text.replace("vf/k—r", "vf/kd`r")
        
        text = text.replace("Qlz~V", "QLVZ").replace("vikj~VesUV", "vikVZesUV").replace("vikVesUV", "vikVZesUV")
        text = text.replace("les tkosaxs", "le>s tkosaxs")
        if "fuoklh%&" not in text: text = text.replace("fuoklh%", "fuoklh%&")
        text = text.replace("iq¾", "iq=")
        
        text = text.replace("mRrjkf/kdkjh", "mRrjkf/kdkjh")
        text = text.replace("ckcR", "ckcr~")
        text = text.replace("mRrj", "mÙkj")
        text = text.replace("mi-iath;d", "mi&iath;d").replace("mi.iath;d", "mi&iath;d")
        text = text.replace("fcYfMax", "fcfYMax")
        text = text.replace("fpUfgr", "fpfUgr")
        text = text.replace("dksÃ jde", "dksbZ jde")
        text = text.replace("Cy\u201ad", "CykWd")
        text = text.replace("vikVZesaV", "vikVZesUV")
        text = text.replace("yksoj", "yksvj")
        text = text.replace("ikfdaZx", "ikfdZax")
        text = text.replace("vkikVZesaV", "vkiVZesaV").replace("vkikVZesUV", "vkiVZesUV")
        
        text = text.replace("LoRo vf/kdkjksa", "LoRo vf\u00e8kdkjksa")
        text = text.replace("ekfydkuk vf/kdkjksa", "ekfydkuk vf\u00e8kdkjksa")
        text = text.replace("laca/k", "laca\u00e8k")
        text = text.replace("LoRokf/kdkj", "LoRokf\u00e8kdkj")
        text = text.replace("mÙkjkf/kdkfj;ksa", "mÙkjkf\u00e8kdkfj;ksa")
        text = text.replace("izfrfuf/k;ksa", "izfrfuf\u00e8k;ksa")
        text = text.replace("tulk/ku", "tulk\u00e8ku")
        text = text.replace("lq[kkf/kdkj", "lq[kkf\u00e8kdkj")
        text = text.replace("vf/kdkjksa o nkf;Ro", "vf\u00e8kdkjksa o nkf;Ro")
        text = text.replace("vf/kdkjksa eq", "vf\u00e8kdkjksa eq")
        text = text.replace("vf/kdkj ug", "vf\u00e8kdkj ug")

        # tatpashchat ending with full 'taa' (r) instead of half 'ta' (r~)
        text = text.replace("rRi'pqR", "rRi\u2019pkr").replace("rRi'pkr~", "rRi\u2019pkr").replace("rRi\u2019pkr~", "rRi\u2019pkr")
        
        # Double quotes of vikretagan / kretagan
        text = text.replace('"foØsrkx.k"', '^^foØsrkx.k**').replace('"foØsrk"', '^^foØsrk**')
        text = text.replace('"Øsrk"', '^^Øsrk**').replace('"Øsrkx.k"', '^^Øsrkx.k**')

        text = text.replace("vikVZesUV/;wfuV~l/\u00b6ysV~l", "vikVZesUV@;wfuV~l@\u00b6ysV~l")
        text = text.replace(";wfuV~/\u00b6ysV", ";wfuV~@\u00b6ysV")
        text = text.replace(";wfuV/\u00b6ysV", ";wfuV@\u00b6ysV")
        text = text.replace("vyx-vyx", "vyx&vyx")
        
        text = text.replace("ftu vf/kdkjksa eq\"rdkZ vf/kdkjksa] lq[kkf\u00e8kdkjksa lfgr Ø; fd;k Fkk", "ftu vf\u00e8kdkjksa eq*rdkZ vf\u00e8kdkjksa] lq[kkf/kdkjksa lfgr Ø; fd;k Fkk")
        text = re.sub(r'(vkoklh;\s+)\1', r'\1', text)
        text = text.replace("lEiRfr", "lEifRr")

        text = text.replace("dksÃ _.k", "dksbZ _.k")
        text = text.replace("dkZ;ky;", "dk;kZy;")
        
        if text != original:
            paragraph.text = text

    def _apply_body_highlights_and_fonts(self, doc, highlight_ai, highlight_missing):
        """Applies highlight rendering and forces correct fonts run-by-run."""
        for paragraph in doc.paragraphs:
            self._highlight_paragraph_robust(paragraph, highlight_ai, highlight_missing)
            self._apply_mixed_fonts_to_paragraph(paragraph)
            
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        self._highlight_paragraph_robust(paragraph, highlight_ai, highlight_missing)
                        self._apply_mixed_fonts_to_paragraph(paragraph)

    def _highlight_paragraph_robust(self, paragraph, highlight_ai, highlight_missing):
        from docx.shared import Pt
        text = paragraph.text
        if not text:
            return

        if HL_MARKER not in text:
            # Fix any Arial/default font issues on replaced legacy text runs
            for run in paragraph.runs:
                if is_text_devlys(run.text):
                    run.font.name = "DevLys 040"
                    run.font.size = Pt(16)
            return

        alignment = paragraph.alignment
        style = paragraph.style

        parts = text.split(HL_MARKER)
        paragraph.text = "" # Clears old runs

        for idx, part in enumerate(parts):
            if not part:
                continue
            run = paragraph.add_run(part)
            
            # Odd indexes represent highlighted variables
            if idx % 2 == 1:
                if part.startswith("MISSING:"):
                    if highlight_missing:
                        run.font.highlight_color = WD_COLOR_INDEX.RED
                        run.font.color.rgb = RGBColor(255, 255, 255)
                else:
                    if highlight_ai:
                        run.font.highlight_color = WD_COLOR_INDEX.YELLOW
            
            # Apply the correct font run-by-run
            if is_text_devlys(part):
                run.font.name = "DevLys 040"
                run.font.size = Pt(16)
            else:
                run.font.name = "Arial"

        paragraph.alignment = alignment
        paragraph.style = style

    def _apply_mixed_fonts_to_paragraph(self, paragraph):
        from docx.shared import Pt
        # Rebuild runs in the paragraph to separate DevLys and English parts
        runs_data = []
        for run in paragraph.runs:
            text = run.text
            if not text:
                continue
            
            # Save formatting attributes
            bold = run.bold
            italic = run.italic
            underline = run.underline
            color = run.font.color.rgb if run.font.color else None
            highlight = run.font.highlight_color
            
            # Split by English words/numbers/dates/PANs, including S/o, C/o, W/o, D/o (case-insensitive)
            # Refined to exclude single-character uppercase letters (like O, V, B, _) which are legacy DevLys characters.
            parts = re.split(r'(\b[SsDdWwCc]/[Oo]\b|\b\d+(?:[\s,\-\/\.\(\)]+\d+)*\b|\b[A-Z_]{2,}(?:[\s,\-\/\.\(\)]+[A-Z0-9_]{2,})*\b|\b[A-Z_]+:[A-Z_]+\b)', text)
            for idx, part in enumerate(parts):
                if not part:
                    continue
                is_english = (idx % 2 == 1)
                runs_data.append({
                    "text": part,
                    "is_english": is_english,
                    "bold": bold,
                    "italic": italic,
                    "underline": underline,
                    "color": color,
                    "highlight": highlight
                })
        
        # Rebuild paragraph runs
        paragraph.text = ""
        for rd in runs_data:
            run = paragraph.add_run(rd["text"])
            run.bold = rd["bold"]
            run.italic = rd["italic"]
            run.underline = rd["underline"]
            if rd["color"]:
                run.font.color.rgb = rd["color"]
            if rd["highlight"]:
                run.font.highlight_color = rd["highlight"]
            
            if rd["is_english"]:
                run.font.name = "Arial"
                run.font.size = Pt(11)
            else:
                # Force DevLys 040 only if the text is actually legacy DevLys encoding.
                # If it's Unicode Devanagari (chain narrative, etc.), we don't override the font
                # so that it inherits the template's style (Mangal/Segoe UI).
                if is_text_devlys(rd["text"]):
                    run.font.name = "DevLys 040"
                    run.font.size = Pt(16)

    def _process_payment_tables_on_doc(self, doc, context):
        import docx
        from docx.shared import Pt
        from utils.helpers import Unicode_to_KrutiDev

        payments = context.get('payments', [])
        amount = context.get('amount', '')
        amount_words = context.get('amount_words', '')

        def set_cell_text(cell, text, is_devlys=False):
            cell.text = text
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = "DevLys 040" if is_devlys else "Arial"
                    r.font.size = Pt(16) if is_devlys else Pt(11)

        def write_cell(cell, val, force_devlys=False):
            val_str = str(val or "")
            is_hindi = force_devlys or any(ord(c) > 127 for c in val_str)
            if is_hindi:
                converted = Unicode_to_KrutiDev(val_str)
                set_cell_text(cell, converted, is_devlys=True)
            else:
                set_cell_text(cell, val_str, is_devlys=False)

        for table in doc.tables:
            if len(table.rows) == 0:
                continue
            header_cells = [c.text.strip() for c in table.rows[0].cells]
            is_payment_table = False
            if len(header_cells) >= 4:
                h_text = " ".join(header_cells).lower()
                if "s.no" in h_text and "amount" in h_text and "bank" in h_text and ("cash" in h_text or "cheque" in h_text or "transfer" in h_text):
                    is_payment_table = True

            if not is_payment_table:
                continue

            # Clear existing data rows (keep header row at index 0)
            while len(table.rows) > 1:
                tbl = table._tbl
                tbl.remove(table.rows[1]._tr)

            # Populate rows
            if payments:
                for idx, p in enumerate(payments):
                    row = table.add_row()
                    write_cell(row.cells[0], f"{idx + 1}.", force_devlys=True)
                    write_cell(row.cells[1], p.get('a', ''))
                    write_cell(row.cells[2], p.get('n', ''))
                    write_cell(row.cells[3], p.get('d', ''))
                    write_cell(row.cells[4], p.get('b', ''))
            else:
                # Add 4 blank rows
                for idx in range(4):
                    row = table.add_row()
                    write_cell(row.cells[0], f"{idx + 1}.", force_devlys=True)
                    write_cell(row.cells[1], "")
                    write_cell(row.cells[2], "")
                    write_cell(row.cells[3], "")
                    write_cell(row.cells[4], "")

            # Add the total row (कुल राशि)
            total_row = table.add_row()
            total_label = Unicode_to_KrutiDev("कुल राशि")
            set_cell_text(total_row.cells[0], total_label, is_devlys=True)
            write_cell(total_row.cells[1], amount)
            
            # The remaining cells can show the amount in words
            words_val = amount_words
            if words_val:
                write_cell(total_row.cells[2], words_val)
                write_cell(total_row.cells[3], words_val)
                write_cell(total_row.cells[4], words_val)
            else:
                write_cell(total_row.cells[2], "")
                write_cell(total_row.cells[3], "")
                write_cell(total_row.cells[4], "")
