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
    normalize_relation_prefix,
    parse_and_format_chain
)

HL_MARKER = "~~HL~~"

def robust_extract_salutation_and_name(full_name):
    if not full_name: return "", ""
    s = str(full_name).strip()
    s = " ".join(s.split())
    
    # Case-insensitive English and exact Hindi/DevLys salutations
    # Match longest salutation first to avoid matching "Mr" before "Mrs"
    # Ensure they match as word prefixes or boundaries
    salutations_pattern = r'^(?:M/s\.?|Messrs|Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Shri\.?|Shree\.?|Late\.?|LoxhZ;\.?|श्री|श्रीमती|सुश्री|डॉ\.?|स्व\.?|स्वर्गीय)\s*'
    
    match = re.match(salutations_pattern, s, re.IGNORECASE)
    if match:
        sal = match.group(0).strip()
        name_part = s[match.end():].strip()
        return sal, name_part
    return "", s

def robust_normalize_name_salutation(name, relation=None, default_to_male=True):
    if not name: return ""
    s = str(name).strip()
    s = " ".join(s.split())
    
    sal, clean_name = robust_extract_salutation_and_name(s)
    if sal:
        return s
        
    return normalize_name_salutation(s, relation, default_to_male)

def title_case_address(text):
    if not text:
        return ""
    words = str(text).strip().split()
    if not words:
        return ""
        
    lowercase_words = {"and", "or", "of", "in", "at", "by", "for", "with", "from", "on", "the", "a", "an", "to", "its"}
    
    title_words = []
    for idx, w in enumerate(words):
        w_lower = w.lower()
        
        # Strip trailing punctuation for exact match checks on connecting words/relations
        w_clean = re.sub(r'[^a-zA-Z0-9/]', '', w_lower)
        
        if w_clean in ["s/o", "w/o", "d/o", "h/o", "c/o"]:
            suffix = w[len(w_clean):]
            title_words.append(w_clean[0].upper() + "/" + w_clean[2].lower() + suffix)
        elif w_clean in ["m/s"]:
            suffix = w[len(w_clean):]
            title_words.append("M/s" + suffix)
        elif w_clean in lowercase_words and idx > 0:
            suffix = w[len(w_clean):]
            title_words.append(w_clean + suffix)
        else:
            def replace_alpha(match):
                part = match.group(0)
                part_lower = part.lower()
                if part_lower in lowercase_words:
                    return part_lower
                if re.match(r'^[ivx]+$', part_lower):
                    return part.upper()
                if len(part) == 1:
                    return part.upper()
                return part.capitalize()
                
            title_words.append(re.sub(r'[a-zA-Z\u0900-\u097F]+', replace_alpha, w))
            
    return " ".join(title_words)

class RMTemplateProcessor:
    def __init__(self, template_path):
        self.template_path = template_path
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found at {template_path}")
        self.doc = DocxTemplate(template_path)

    def _convert_context_to_legacy(self, data):
        """Recursively scans context and prepares fields for Word Template rendering."""
        if isinstance(data, dict):
            return {k: self._convert_context_to_legacy(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_context_to_legacy(x) for x in data]
        elif isinstance(data, str):
            # Strip invalid XML control characters
            data = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\x85\xA0-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]', '', data)
            if '\n' in data:
                rt = RichText()
                parts = data.split('\n')
                for i, part in enumerate(parts):
                    rt.add(part, font='Cambria', size=24)
                    if i < len(parts) - 1:
                        rt.add('\a')
                return rt
            return data
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
        for list_name, index in re.findall(r"\b(bs|ls|ps|ws|ds)\s*\[\s*(\d+)\s*\]", self._template_xml()):
            required[list_name] = max(required.get(list_name, 0), int(index) + 1)
        return required

    def _pad_indexed_lists(self, context):
        defaults = {
            "bs": {"s": "", "n": "", "a": "", "r": "", "rn": "", "adr": "", "id": "", "pan": ""},
            "ls": {"n": "", "a": "", "w": "", "t": ""},
            "ps": {"adr": "", "n": "", "s": "", "e": "", "w": "", "lease_deed_no": ""},
            "ws": {"n": "", "r": "", "rn": "", "adr": ""},
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

        xml_content = self._template_xml()
        has_bsign_s = "bsign.s" in xml_content
        doc_type = "RM"
        seen_ids = set()

        for ctx in contexts_to_clean:
            # 1. Normalize Borrowers relative names
            if "bs" in ctx and isinstance(ctx["bs"], list):
                for i, b in enumerate(ctx["bs"]):
                    if isinstance(b, dict):
                        if id(b) in seen_ids:
                            continue
                        seen_ids.add(id(b))
                        if b.get("r"):
                            b["r"] = normalize_relation_prefix(b["r"], doc_type)
                        
                        if b.get("r") and b.get("rn"):
                            if not b.get("relation_text"):
                                b["relation_text"] = f"{b['r']} {b['rn']}"
                        elif b.get("relation_text"):
                            r, rn = parse_relation_text(b["relation_text"])
                            b["r"] = r
                            b["rn"] = rn
                        
                        if b.get("r"):
                            b["r"] = normalize_relation_prefix(b["r"], doc_type)
                            if b.get("rn"):
                                b["relation_text"] = f"{b['r']} {b['rn']}"
                                
                        if b.get("rn"):
                            b["rn"] = normalize_relative_salutation(b["rn"], b.get("r"))

                        if b.get("n"):
                            raw_name = b["n"]
                            existing_s = b.get("s", "").strip()
                            starts_with_sal, _ = robust_extract_salutation_and_name(raw_name)
                            if existing_s and not starts_with_sal:
                                raw_name = f"{existing_s} {raw_name}"
                            sal, clean_name = robust_extract_salutation_and_name(raw_name)
                            has_bs_s = bool(re.search(rf"bs\s*\[\s*{i}\s*\]\s*\.\s*s\b", xml_content))
                            if has_bs_s:
                                b["s"] = sal
                                b["n"] = clean_name
                            else:
                                b["s"] = ""
                                b["n"] = robust_normalize_name_salutation(raw_name, b.get("r"))
            
            # 2. Normalize Witnesses names and relative names
            if "ws" in ctx and isinstance(ctx["ws"], list):
                for w in ctx["ws"]:
                    if isinstance(w, dict):
                        if id(w) in seen_ids:
                            continue
                        seen_ids.add(id(w))
                        if w.get("r"):
                            w["r"] = normalize_relation_prefix(w["r"], doc_type)
                        
                        if w.get("r") and w.get("rn"):
                            if not w.get("relation_text"):
                                w["relation_text"] = f"{w['r']} {w['rn']}"
                        elif w.get("relation_text"):
                            r, rn = parse_relation_text(w["relation_text"])
                            w["r"] = r
                            w["rn"] = rn
                            
                        if w.get("r"):
                            w["r"] = normalize_relation_prefix(w["r"], doc_type)
                            if w.get("rn"):
                                w["relation_text"] = f"{w['r']} {w['rn']}"
                                
                        if w.get("n"):
                            w["n"] = normalize_name_salutation(w["n"], w.get("r"))
                        if w.get("rn"):
                            w["rn"] = normalize_relative_salutation(w["rn"], w.get("r"))

            # 3. Normalize Bank Signatory
            if "bsign" in ctx and isinstance(ctx["bsign"], dict):
                bsign = ctx["bsign"]
                if id(bsign) not in seen_ids:
                    seen_ids.add(id(bsign))
                    if bsign.get("r"):
                        bsign["r"] = normalize_relation_prefix(bsign["r"], doc_type)
                    
                    if bsign.get("r") and bsign.get("rn"):
                        if not bsign.get("relation_text"):
                            bsign["relation_text"] = f"{bsign['r']} {bsign['rn']}"
                    elif bsign.get("relation_text"):
                        r, rn = parse_relation_text(bsign["relation_text"])
                        bsign["r"] = r
                        bsign["rn"] = rn
                        
                    if bsign.get("r"):
                        bsign["r"] = normalize_relation_prefix(bsign["r"], doc_type)
                        if bsign.get("rn"):
                            bsign["relation_text"] = f"{bsign['r']} {bsign['rn']}"
                            
                    if bsign.get("rn"):
                        bsign["rn"] = normalize_relative_salutation(bsign["rn"], bsign.get("r"))
                    
                    # Normalize name and split or embed salutation depending on has_bsign_s
                    if bsign.get("n"):
                        raw_name = bsign["n"]
                        existing_s = bsign.get("s", "").strip()
                        starts_with_sal, _ = robust_extract_salutation_and_name(raw_name)
                        if existing_s and not starts_with_sal:
                            raw_name = f"{existing_s} {raw_name}"
                        sal, clean_name = robust_extract_salutation_and_name(raw_name)
                        
                        if has_bsign_s:
                            bsign["s"] = sal
                            bsign["n"] = clean_name
                        else:
                            bsign["s"] = ""
                            bsign["n"] = robust_normalize_name_salutation(raw_name, bsign.get("r"))

    def generate(self, context, output_path, highlight_ai=False, highlight_missing=False, verified_fields=None):
        if verified_fields is None: verified_fields = set()
        
        d_ctx = context.get('d', context)
        context['d'] = d_ctx
        
        self._normalize_context_salutations(context)

        # Format address fields to Title Case for RM draft
        def format_all_addresses(ctx):
            if not isinstance(ctx, dict): return
            for b in ctx.get("bs", []):
                if isinstance(b, dict) and b.get("adr"):
                    b["adr"] = title_case_address(b["adr"])
            for w in ctx.get("ws", []):
                if isinstance(w, dict) and w.get("adr"):
                    w["adr"] = title_case_address(w["adr"])
            bsign = ctx.get("bsign")
            if isinstance(bsign, dict) and bsign.get("adr"):
                bsign["adr"] = title_case_address(bsign["adr"])
            for p in ctx.get("ps", []):
                if isinstance(p, dict):
                    if p.get("adr"):
                        p["adr"] = title_case_address(p["adr"])
                    if p.get("full_address"):
                        p["full_address"] = title_case_address(p["full_address"])

        format_all_addresses(context)
        if d_ctx is not context:
            format_all_addresses(d_ctx)

        # Process and standardize title chain documents
        raw_chain = d_ctx.get("ds_text", "") or d_ctx.get("second_schedule", "")
        
        # If we have chain text, parse and format it
        if raw_chain:
            formatted_chain, clean_docs = parse_and_format_chain(raw_chain)
            
            d_ctx["ds_text"] = formatted_chain
            d_ctx["second_schedule"] = formatted_chain
            if d_ctx is not context:
                context["ds_text"] = formatted_chain
                context["second_schedule"] = formatted_chain
                
            d_ctx["ds"] = [{"t": doc} for doc in clean_docs]
            if d_ctx is not context:
                context["ds"] = [{"t": doc} for doc in clean_docs]
        else:
            # If no raw chain text is present, but ds list is already present, format from ds list
            existing_ds = d_ctx.get("ds", [])
            if existing_ds:
                clean_docs = [item["t"] for item in existing_ds if isinstance(item, dict) and item.get("t")]
                raw_chain_from_ds = "\n".join(clean_docs)
                formatted_chain, _ = parse_and_format_chain(raw_chain_from_ds)
                
                d_ctx["ds_text"] = formatted_chain
                d_ctx["second_schedule"] = formatted_chain
                if d_ctx is not context:
                    context["ds_text"] = formatted_chain
                    context["second_schedule"] = formatted_chain

        # Populate Chain_Text in all contexts
        formatted_chain = d_ctx.get("ds_text", "")
        d_ctx["Chain_Text"] = formatted_chain
        if d_ctx is not context:
            context["Chain_Text"] = formatted_chain
            
        # Ensure verification status carries over to Chain_Text and all ds list items
        if "ds_text" in verified_fields:
            verified_fields.add("Chain_Text")
            verified_fields.add("d.Chain_Text")
            for idx in range(len(d_ctx.get("ds", []))):
                verified_fields.add(f"ds.{idx}.t")
                verified_fields.add(f"d.ds.{idx}.t")

        self._pad_indexed_lists(d_ctx)

        if highlight_ai or highlight_missing:
            context = self._apply_highlight_markers(context, verified_fields, highlight_ai, highlight_missing)

        context = self._convert_context_to_legacy(context)
        self.doc.render(context)

        # ALWAYS apply body highlights to strip delimiters
        self._apply_body_highlights(highlight_ai, highlight_missing)

        self._postprocess_saved_doc(output_path)

    def _apply_highlight_markers(self, data, verified_fields, highlight_ai, highlight_missing, path=""):
        # Exclude title chain / list of documents from highlighting completely
        norm_path = path.lower()
        if (norm_path == "ds_text" or norm_path == "d.ds_text" or 
            norm_path == "second_schedule" or norm_path == "d.second_schedule" or 
            norm_path == "chain_text" or norm_path == "d.chain_text" or 
            norm_path.startswith("ds") or norm_path.startswith("d.ds")):
            return data

        if isinstance(data, dict):
            return {k: self._apply_highlight_markers(v, verified_fields, highlight_ai, highlight_missing, f"{path}.{k}" if path else k) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._apply_highlight_markers(x, verified_fields, highlight_ai, highlight_missing, f"{path}.{i}") for i, x in enumerate(data)]
        elif isinstance(data, str):
            if not data.strip():
                if highlight_missing and path not in verified_fields:
                    return f"{HL_MARKER}MISSING:{path.upper()}{HL_MARKER}"
                return data
            if highlight_ai and path not in verified_fields:
                if "\n" in data:
                    parts = []
                    for line in data.split("\n"):
                        if line.strip():
                            parts.append(f"{HL_MARKER}{line}{HL_MARKER}")
                        else:
                            parts.append(line)
                    return "\n".join(parts)
                return f"{HL_MARKER}{data}{HL_MARKER}"
            return data
        else:
            return data

    def _apply_body_highlights(self, highlight_ai, highlight_missing):
        yellow_highlight = WD_COLOR_INDEX.YELLOW
        red_highlight = WD_COLOR_INDEX.RED
        
        for paragraph in self.doc.paragraphs:
            self._highlight_paragraph_runs(paragraph, yellow_highlight, red_highlight, highlight_ai, highlight_missing)
            
        for table in self.doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        self._highlight_paragraph_runs(paragraph, yellow_highlight, red_highlight, highlight_ai, highlight_missing)

    def _highlight_paragraph_runs(self, paragraph, yellow_highlight, red_highlight, highlight_ai, highlight_missing):
        if HL_MARKER not in paragraph.text:
            return

        base_font_name = "Cambria"
        base_font_size = None
        base_bold = False
        base_italic = False
        base_color = None

        for r in paragraph.runs:
            if r.text:
                if r.font.name:
                    base_font_name = r.font.name
                if r.font.size:
                    base_font_size = r.font.size
                if r.bold is not None:
                    base_bold = r.bold
                if r.italic is not None:
                    base_italic = r.italic
                if r.font.color and r.font.color.rgb:
                    base_color = r.font.color.rgb
                break

        text = paragraph.text
        paragraph.text = "" # Clears old runs

        parts = text.split(HL_MARKER)
        for idx, part in enumerate(parts):
            if not part:
                continue
            run = paragraph.add_run(part)
            
            run.font.name = base_font_name
            if base_font_size:
                run.font.size = base_font_size
            run.bold = base_bold
            run.italic = base_italic
            if base_color:
                run.font.color.rgb = base_color

            if idx % 2 == 1:
                if part.startswith("MISSING:"):
                    if highlight_missing:
                        run.font.highlight_color = red_highlight
                        run.font.color.rgb = RGBColor(255, 255, 255)
                else:
                    if highlight_ai:
                        run.font.highlight_color = yellow_highlight

    def _postprocess_saved_doc(self, output_path):
        self.doc.save(output_path)
