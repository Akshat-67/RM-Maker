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

class SDTemplateProcessor:
    def __init__(self, template_path):
        self.template_path = template_path
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found at {template_path}")
        self.doc = DocxTemplate(template_path)

    def _convert_context_to_legacy(self, data):
        """Recursively scans context and encodes Hindi Unicode fields to DevLys ASCII."""
        if isinstance(data, dict):
            return {k: self._convert_context_to_legacy(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_context_to_legacy(x) for x in data]
        elif isinstance(data, str):
            # Sanitize control characters that break docx
            data = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\x85\xA0-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]', '', data)
            val = Unicode_to_KrutiDev(data)
            val = val.replace("&", "&amp;")
            
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
                        if w.get("n"): w["n"] = normalize_name_salutation(w["n"], w.get("r"))

            sellers_list = ctx.get("ss") or ctx.get("sellers")
            if sellers_list and isinstance(sellers_list, list):
                for s in sellers_list:
                    if isinstance(s, dict):
                        if s.get("r"): s["r"] = normalize_relation_prefix(s["r"], doc_type)
                        if s.get("relation_text"):
                            r, rn = parse_relation_text(s["relation_text"])
                            s["r"] = r
                            s["rn"] = rn
                        if s.get("n"): s["n"] = normalize_name_salutation(s["n"], s.get("r"))

            buyers_list = ctx.get("bs") or ctx.get("buyers")
            if buyers_list and isinstance(buyers_list, list):
                for b in buyers_list:
                    if isinstance(b, dict):
                        if b.get("r"): b["r"] = normalize_relation_prefix(b["r"], doc_type)
                        if b.get("relation_text"):
                            r, rn = parse_relation_text(b["relation_text"])
                            b["r"] = r
                            b["rn"] = rn
                        if b.get("n"): b["n"] = normalize_name_salutation(b["n"], b.get("r"))

    def generate(self, context, output_path, highlight_ai=False, highlight_missing=False, verified_fields=None):
        if verified_fields is None: verified_fields = set()
        d_ctx = context.get('d')
        if d_ctx is None:
            d_ctx = context.copy()
            context['d'] = d_ctx
        
        # SD compatibility keys
        if 'sale' not in context:
            context['sale'] = {
                'amount': context.get('amount', d_ctx.get('amount', '')),
                'amount_words': context.get('amount_words', d_ctx.get('amount_words', '')),
                'payment_details': context.get('payments', d_ctx.get('payments', []))
            }
        if 'deed' not in context:
            context['deed'] = {'execution_date': context.get('rd', d_ctx.get('rd', ''))}
        
        if 'd' in context and isinstance(context['d'], dict):
            if 'sale' not in context['d']: context['d']['sale'] = context['sale']
            if 'deed' not in context['d']: context['d']['deed'] = context['deed']

        # Ensure base keys exist for empty contexts
        if 'ss' not in context: context['ss'] = context.get('sellers', [])
        if 'bs' not in context: context['bs'] = context.get('buyers', [])

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
        self.doc.render(context)
        
        # Post-render paragraph splitting
        # We look for paragraphs that contain newlines (from our legacy conversion)
        # and split them into actual separate Word paragraphs.
        self._split_multi_line_paragraphs()

        if highlight_ai or highlight_missing:
            self._apply_body_highlights()

        self._postprocess_saved_doc(output_path)

    def _split_multi_line_paragraphs(self):
        """Splits paragraphs containing '\n' into actual separate Word paragraphs."""
        # We iterate in reverse to avoid index shifts affecting our loop
        # and to properly handle multiple multi-line paragraphs.
        # But for simpler logic, let's just collect and process.
        paras = list(self.doc.paragraphs)
        for p in paras:
            if '\n' in p.text:
                lines = p.text.split('\n')
                # Update current paragraph with first line
                p.text = lines[0]
                current_p = p
                # Insert subsequent lines as new paragraphs
                for line in lines[1:]:
                    new_para = self.doc.add_paragraph("") # Add to end to get an object
                    # Move the new paragraph XML element to after current_p
                    current_p._p.addnext(new_para._p)
                    new_para.text = line
                    # Match style and alignment
                    new_para.style = p.style
                    new_para.alignment = p.alignment
                    if new_para.runs:
                        new_para.runs[0].font.name = "DevLys 010"
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

    def _apply_body_highlights(self):
        for paragraph in self.doc.paragraphs:
            self._highlight_paragraph_runs(paragraph, WD_COLOR_INDEX.YELLOW, WD_COLOR_INDEX.RED)
        for table in self.doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        self._highlight_paragraph_runs(paragraph, WD_COLOR_INDEX.YELLOW, WD_COLOR_INDEX.RED)

    def _highlight_paragraph_runs(self, paragraph, yellow_highlight, red_highlight):
        from docx.text.run import Run
        runs = list(paragraph.runs)
        for run in runs:
            text = run.text
            if HL_MARKER in text:
                parts = text.split(HL_MARKER)
                run.text = parts[0]
                current_r = run._r
                for idx in range(1, len(parts)):
                    part = parts[idx]
                    new_r = paragraph.add_run(part)._r
                    current_r.addnext(new_r)
                    if idx % 2 == 1:
                        temp_run = Run(new_r, paragraph)
                        if part.startswith("MISSING:"):
                            temp_run.font.highlight_color = red_highlight
                            temp_run.font.color.rgb = RGBColor(255, 255, 255)
                        else:
                            temp_run.font.highlight_color = yellow_highlight
                    current_r = new_r

    def _postprocess_saved_doc(self, output_path):
        for paragraph in self.doc.paragraphs:
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
            text = text.replace("^^;wfuV/¶ysV**", "^^;wfuV@¶ysV**")
            
            if "gS%" in text and "gS%&" not in text: text = text.replace("gS%", "gS%&")

            # 4. Global Character / Hyphen Cleanups
            
            # Generic non-digit to digit hyphen-to-ampersand cleanup (e.g. महाराष्ट्र-411044 -> महाराष्ट्र&411044)
            # Exclude standalone 'u-' and 'ua-' abbreviations using negative lookbehind
            text = re.sub(r'([^\d])(?<!\bu)(?<!\bua)\-(\s*\d)', r'\g<1>&\g<2>', text)
            text = re.sub(r'(\d)\-([^\d])', r'\g<1>&\g<2>', text)
            text = text.replace(" - ", " & ")
            
            # Generic character/ligature normalizations
            text = text.replace("okfjlkU", "okfjlku~")
            text = text.replace("vf/k—r", "vf/kd`r")
            
            # Word-perfect mismatches
            text = text.replace("Qlz~V", "QLVZ").replace("vikj~VesUV", "vikVZesUV").replace("vikVesUV", "vikVZesUV")
            text = text.replace("les tkosaxs", "le>s tkosaxs")
            if "fuoklh%&" not in text: text = text.replace("fuoklh%", "fuoklh%&")
            text = text.replace("iq¾", "iq=")
            
            # Template alignment fixes
            text = text.replace("mRrjkf/kdkjh", "mÙkjkf/kdkjh")
            text = text.replace("ckcR", "ckcr~")
            text = text.replace("mRrj", "mÙkj")
            text = text.replace("mi-iath;d", "mi&iath;d").replace("mi.iath;d", "mi&iath;d")
            text = text.replace("fcYfMax", "fcfYMax")
            text = text.replace("fpUfgr", "fpfUgr")
            text = text.replace("dksÃ jde", "dksbZ jde")
            text = text.replace("Cy‚d", "CykWd")
            text = text.replace("vikVZesaV", "vikVZesUV")
            text = text.replace("yksoj", "yksvj")
            text = text.replace("ikfdaZx", "ikfdZax")
            text = text.replace("vkikVZesaV", "vkiVZesaV").replace("vkikVZesUV", "vkiVZesUV")
            
            # Surgical è (dh) ligatures in static template
            text = text.replace("LoRo vf/kdkjksa", "LoRo vfèkdkjksa")
            text = text.replace("ekfydkuk vf/kdkjksa", "ekfydkuk vfèkdkjksa")
            text = text.replace("laca/k", "lacaèk")
            text = text.replace("LoRokf/kdkj", "LoRokfèkdkj")
            text = text.replace("mÙkjkf/kdkfj;ksa", "mÙkjkfèkdkfj;ksa")
            text = text.replace("izfrfuf/k;ksa", "izfrfufèk;ksa")
            text = text.replace("tulk/ku", "tulkèku")
            text = text.replace("lq[kkf/kdkj", "lq[kkfèkdkj")
            text = text.replace("vf/kdkjksa o nkf;Ro", "vfèkdkjksa o nkf;Ro")
            text = text.replace("vf/kdkjksa eq", "vfèkdkjksa eq")
            text = text.replace("vf/kdkj ug", "vfèkdkj ug")

            # Word-specific cleanup
            text = text.replace("rRi'pkR", "rRi’pkr~").replace("rRi'pkr~", "rRi’pkr~")
            text = text.replace("vikVZesUV/;wfuV~l/¶ysV~l", "vikVZesUV@;wfuV~l@¶ysV~l")
            text = text.replace(";wfuV~/¶ysV", ";wfuV~@¶ysV")
            text = text.replace(";wfuV/¶ysV", ";wfuV@¶ysV")
            text = text.replace("vyx-vyx", "vyx&vyx")
            
            # Precise alignment for PARA 18
            text = text.replace("ftu vf/kdkjksa eq\"rdkZ vf/kdkjksa] lq[kkfèkdkjksa lfgr Ø; fd;k Fkk", "ftu vfèkdkjksa eq*rdkZ vfèkdkjksa] lq[kkf/kdkjksa lfgr Ø; fd;k Fkk")
            text = re.sub(r'(vkoklh;\s+)\1', r'\1', text)
            text = text.replace("lEiRfr", "lEifRr")

            # Restore global dksbZ exceptions:
            text = text.replace("dksÃ jde", "dksbZ jde")
            text = text.replace("dksÃ _.k", "dksbZ _.k")
            
            # Global cleanup of कार्यालय duplicates:
            text = text.replace("dkZ;ky;", "dk;kZy;")
            
            if text != original:
                if paragraph.runs:
                    paragraph.text = text
                    paragraph.runs[0].font.name = "DevLys 010"

        self.doc.save(output_path)
