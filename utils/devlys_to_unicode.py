import os
import re
from copy import deepcopy
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# MAPPINGS DEVISE: (DevLys -> Unicode)
# Compiled from Kruti Dev 010 / DevLys 040 mapping pairs, sorted by legacy string length descending.
MAPPING_PAIRS = [
    # 3-character keys
    ("Q+Z", "QZ+"),
    ("sas", "sa"),
    ("f=k", "f="),
    ("nzZ", "र्द्र"),
    ("vks", "ओ"),
    ("vkS", "औ"),
    ("pkS", "चै"),
    ("\"k", "ष"),
    ("~ ", ","),
    # 2-character keys
    ("aa", "a"),
    (")Z", "र्द्ध"),
    ("ZZ", "Z"),
    ("¶+", "फ्"),
    ("d+", "क़"),
    ("[+k", "ख़"),
    ("[+", "ख़्"),
    ("x+", "ग़"),
    ("T+", "ज़्"),
    ("t+", "ज़"),
    ("M+", "ड़"),
    ("<+", "ढ़"),
    ("Q+", "फ़"),
    (";+", "य़"),
    ("j+", "ऱ"),
    ("u+", "ऩ"),
    ("Ùk", "त्त"),
    ("Ù", "त्त्"),
    ("Dr", "क्त"),
    ("ä", "क्त"),
    ("é", "न्न"),
    ("™", "न्न्"),
    ("=kk", "=k"),
    ("ºz", "ह्र"),
    ("í", "द्द"),
    ("{k", "क्ष"),
    ("«", "त्र्"),
    ("Nî", "छ्य"),
    ("Vî", "ट्य"),
    ("Bî", "ठ्य"),
    ("Mî", "ड्य"),
    ("<î", "ढ्य"),
    ("Vª", "ट्र"),
    ("Mª", "ड्र"),
    ("Nª", "छ्र"),
    ("xz", "ग्र"),
    ("v‚", "ऑ"),
    ("vk", "आ"),
    ("b±", "ईं"),
    ("bZ", "ई"),
    (",s", "ऐ"),
    ("Dk", "क"),
    ("[k", "ख"),
    ("Xk", "ग"),
    ("?k", "घ"),
    ("Pk", "च"),
    ("Tk", "ज"),
    ("Rk", "त"),
    ("Fk", "थ"),
    ("èk", "ध"),
    ("Uk", "न"),
    ("Ik", "प"),
    ("Ck", "ब"),
    ("Hk", "भ"),
    ("Ek", "म"),
    ("Yk", "ल"),
    ("Ok", "व"),
    ("'k", "श"),
    ("Lk", "स"),
    ("Ük", "श"),
    ("~j", "्र"),
    ("ks", "ो"),
    ("kS", "ौ"),
    (" ः", ":"),
    # 1-character keys
    ("ñ", "्र"),
    ("‘", "'"),
    ("’", "'"),
    ("“", "\""),
    ("”", "\""),
    ("å", "०"),
    ("ƒ", "१"),
    ("„", "२"),
    ("…", "३"),
    ("†", "४"),
    ("‡", "५"),
    ("ˆ", "६"),
    ("‰", "७"),
    ("Š", "८"),
    ("‹", "९"),
    ("–", "दृ"),
    ("—", "कृ"),
    ("à", "ह्न"),
    ("á", "ह्य"),
    ("â", "हृ"),
    ("ã", "ह्म"),
    ("º", "ह्"),
    ("=", "त्र"),
    ("|", "द्य"),
    ("K", "ज्ञ"),
    ("}", "द्व"),
    ("J", "श्र"),
    ("Ø", "क्र"),
    ("Ý", "फ्र"),
    ("æ", "द्र"),
    ("ç", "प्र"),
    ("Á", "प्र"),
    ("#", "रु"),
    (":", "रू"),
    ("v", "अ"),
    ("Ã", "ई"),
    ("b", "इ"),
    ("m", "उ"),
    ("Å", "ऊ"),
    (",", "ए"),
    ("_", "ऋ"),
    ("ô", "क्क"),
    ("d", "क"),
    ("D", "क्"),
    ("[", "ख्"),
    ("x", "ग"),
    ("X", "ग्"),
    ("Ä", "घ"),
    ("?", "घ्"),
    ("³", "ङ"),
    ("p", "च"),
    ("P", "च्"),
    ("N", "छ"),
    ("t", "ज"),
    ("T", "ज्"),
    (">", "झ"),
    ("÷", "झ्"),
    ("¥", "ञ"),
    ("ê", "ट्ट"),
    ("ë", "ट्ठ"),
    ("V", "ट"),
    ("B", "ठ"),
    ("ì", "ड्ड"),
    ("ï", "ड्ढ"),
    ("M", "ड"),
    ("<", "ढ"),
    (".k", "ण"),
    (".", "ण्"),
    ("r", "त"),
    ("R", "त्"),
    ("F", "थ्"),
    (")", "द्ध"),
    ("n", "द"),
    ("/k", "ध"),
    ("/", "ध्"),
    ("Ë", "ध्"),
    ("è", "ध्"),
    ("u", "न"),
    ("U", "न्"),
    ("i", "प"),
    ("I", "प्"),
    ("Q", "फ"),
    ("¶", "फ्"),
    ("c", "ब"),
    ("C", "ब्"),
    ("H", "भ्"),
    ("e", "म"),
    ("E", "म्"),
    (";", "य"),
    ("¸", "य्"),
    ("j", "र"),
    ("y", "ल"),
    ("Y", "ल्"),
    ("G", "ळ"),
    ("o", "व"),
    ("O", "व्"),
    ("'", "श्"),
    ("\"", "ष्"),
    ("l", "स"),
    ("L", "स्"),
    ("g", "ह"),
    ("È", "ीं"),
    ("z", "्र"),
    ("Ì", "द्द"),
    ("Í", "ट्ट"),
    ("Î", "ट्ठ"),
    ("Ï", "ड्ड"),
    ("Ñ", "कृ"),
    ("Ò", "भ"),
    ("Ó", "्य"),
    ("Ô", "ड्ढ"),
    ("Ö", "झ"),
    ("Ù", "त्त्"),
    ("Ü", "श्"),
    ("‚", "ॉ"),
    ("k", "ा"),
    ("h", "ी"),
    ("q", "ु"),
    ("w", "ू"),
    ("`", "ृ"),
    ("s", "े"),
    ("S", "ै"),
    ("a", "ं"),
    ("¡", "ँ"),
    ("%", "ः"),
    ("W", "ॅ"),
    ("•", "ऽ"),
    ("·", "ऽ"),
    ("∙", "ऽ"),
    ("~", "्"),
    ("\\", "?"),
    ("+", "़"),
    ("^", "‘"),
    ("*", "’"),
    ("Þ", "“"),
    ("ß", "”"),
    ("(", ";"),
    ("¼", "("),
    ("½", ")"),
    ("¿", "{"),
    ("À", "}"),
    ("¾", "="),
    ("A", "।"),
    ("-", "."),
    ("&", "-"),
    ("Œ", "॰"),
    ("]", ","),
    ("@", "/"),
    ("<ªª", "ढ्र"),
    ("Û", "x"),
    ("{", "क्ष्"),
    ("f", "ि")
]

# Ensure pairs are sorted long-to-short to perform safe replacements
MAPPING_PAIRS.sort(key=lambda x: len(x[0]), reverse=True)


class DevLysToUnicodeConverter:
    _devanagari_regex = re.compile(r'[ऀ-ॿ]')

    @staticmethod
    def is_likely_english(text):
        if not text or not text.strip():
            return True
            
        stripped = text.strip()
        
        # If it contains any Devanagari character, it's definitely not English
        if DevLysToUnicodeConverter._devanagari_regex.search(stripped):
            return False

        # If it doesn't match standard English/numeric/punctuation characters, it's not English
        if not re.match(r'^[A-Za-z0-9\s\.,\-\(\)\/\#\&\:\@]+$', stripped):
            return False
            
        # Common English terms in legal docs (case-insensitive)
        common_english = re.compile(
            r'\b(home|first|finance|company|india|limited|bank|loan|agreement|office|court|deed|sale|register|mortgage|borrower|lender|seller|buyer|witness|property|registration|number|date|tehsil|district|village|scheme|plot|area|amount|words|hypothecation|signature|total|rs|rupees|s\.?no|pan|aadhaar|uid|ifsc|sro|registrar|page|vol|book|no|name)\b',
            re.IGNORECASE
        )
        if common_english.search(stripped):
            return True

        # Check word-by-word
        words = stripped.split()
        if not words:
            return True

        # If there are specific DevLys substrings, it's not English
        devlys_specifics = ["Jh", "fo;", "eukst", "o\"kZ", "fHkok", "iq=", "vk;q", "fuoklh", "izFkei{k", "f}rh;i{k"]
        if any(x in stripped for x in devlys_specifics):
            return False

        is_english_words = []
        for w in words:
            # Clean punctuation from ends
            w_clean = re.sub(r'^[^A-Za-z0-9]+|[^A-Za-z0-9]+$', '', w)
            if not w_clean:
                continue
            if w_clean.isdigit():
                is_english_words.append(True)
                continue
            # If all uppercase (e.g. "S.NO", "PAN", "LAN", "IFSC")
            if w_clean.isupper():
                is_english_words.append(True)
                continue
            # If Capitalized (e.g. "Name", "Date")
            if w_clean[0].isupper() and w_clean[1:].islower() and len(w_clean) >= 3:
                is_english_words.append(True)
                continue
            # Common short lowercase English words
            if w_clean.islower() and len(w_clean) >= 3:
                if w_clean in ["and", "the", "for", "o", "of", "to", "in", "on", "at", "by", "with", "from", "as", "is", "are", "was", "were", "be"]:
                    is_english_words.append(True)
                    continue
            
            is_english_words.append(False)

        # If all words look like English, it's English
        if is_english_words and all(is_english_words):
            return True

        return False

    @staticmethod
    def devlys_to_unicode_text(text):
        if not text:
            return ""
        
        # Skip if already Unicode Devanagari
        if DevLysToUnicodeConverter._devanagari_regex.search(text):
            return text

        if DevLysToUnicodeConverter.is_likely_english(text):
            return text

        modified = text
        # Pre-normalize smart quotes to straight quotes so multi-character keys match
        modified = modified.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')

        # 1. Matra Reordering Preparation
        # In DevLys, the chhoti-i matra 'f' is typed before the consonant cluster.
        # We temporarily place 'ि' at that position and we will shift it after replacements are done.
        
        # 2. Run replacements long-to-short
        for devlys_seq, uni_seq in MAPPING_PAIRS:
            modified = modified.replace(devlys_seq, uni_seq)

        # 2b. Translate Alt-code combination character 'Æ' (chhoti-i + reph)
        # Æ followed by a consonant cluster gets replaced with ि + cluster + Z
        modified = re.sub(r'Æ((?:[\u0900-\u097F]्)*[\u0900-\u097F])', r'ि\1Z', modified)

        # 3. Chhoti-i Matra (ि) Reordering
        # The 'ि' Matra needs to move past the complete consonant cluster.
        # Consonant cluster: (consonant + halant)* + consonant
        # Example: ि + स् + ् + त -> स् + त + ि
        modified = re.sub(r'ि((?:[\u0900-\u097F]्)*[\u0900-\u097F])', r'\1ि', modified)

        # 4. Reph (र्) Reordering
        # In DevLys, 'Z' is typed at the end of the cluster. In Unicode it becomes 'र्' before the cluster.
        # Example: क + ा + Z -> र् + क + ा
        modified = re.sub(r'((?:[\u0900-\u097F]्)*[\u0900-\u097F][\u093e-\u094d\u0902\u0903]*)Z', r'र्\1', modified)

        # 5. Clean up duplicate halants or mapping edge cases
        modified = modified.replace("िि", "ि")
        modified = modified.replace("ींं", "ीं")
        
        return modified

    @staticmethod
    def merge_runs_compatible(paragraph):
        """
        Contiguously merges runs in a paragraph that have identical formatting.
        """
        # Cache paragraph.runs locally to avoid O(N^2) reconstruction from XML
        # when accessing it inside the loop, especially for large paragraphs.
        runs = paragraph.runs
        if len(runs) <= 1:
            return

        i = 0
        while i < len(runs) - 1:
            run1 = runs[i]
            run2 = runs[i+1]
            
            # Match formatting attributes
            r1_font = run1.font
            r2_font = run2.font
            
            font_compatible = (
                (r1_font.name == r2_font.name) and
                (r1_font.size == r2_font.size) and
                (r1_font.bold == r2_font.bold) and
                (r1_font.italic == r2_font.italic) and
                (r1_font.underline == r2_font.underline) and
                (r1_font.color.rgb == r2_font.color.rgb)
            )
            
            if font_compatible:
                run1.text = run1.text + run2.text
                p_element = paragraph._p
                p_element.remove(run2._r)
                # Keep local runs cache synchronized with XML deletion
                del runs[i+1]
            else:
                i += 1

    @staticmethod
    def set_font_mangal(run, font_name="Mangal"):
        """
        Configures the run font name to Mangal / standard Devanagari 
        across all OXML styling nodes, sets the language to Hindi, forces
        complex script styling tag, and adds hint="cs" to ensure proper
        rendering in Word.
        """
        run.font.name = font_name
        try:
            rPr = run._r.get_or_add_rPr()
            
            # Set font name in all slots + hint
            rFonts = rPr.get_or_add_rFonts()
            rFonts.set(qn('w:ascii'), font_name)
            rFonts.set(qn('w:hAnsi'), font_name)
            rFonts.set(qn('w:cs'), font_name)
            rFonts.set(qn('w:eastAsia'), font_name)
            rFonts.set(qn('w:hint'), 'cs')  # Tell Word to prefer CS font engine
            
            # Remove any theme references that could override our explicit font
            for attr in ['w:asciiTheme', 'w:hAnsiTheme', 'w:cstheme', 'w:eastAsiaTheme']:
                try:
                    rFonts.attrib.pop(qn(attr), None)
                except Exception:
                    pass
            
            # Set language to Hindi to ensure correct font engine is invoked
            lang = rPr.find(qn('w:lang'))
            if lang is None:
                lang = OxmlElement('w:lang')
                rPr.append(lang)
            lang.set(qn('w:val'), 'hi-IN')
            lang.set(qn('w:bidi'), 'hi-IN')
            
            # Add <w:cs/> element to tell Word to treat it as complex script
            cs = rPr.find(qn('w:cs'))
            if cs is None:
                cs = OxmlElement('w:cs')
                rPr.append(cs)
        except Exception:
            pass

    @staticmethod
    def _patch_rfonts_element(rFonts_el, font_name="Mangal"):
        """Patch an rFonts element to replace DevLys/Kruti references with font_name."""
        if rFonts_el is None:
            return False
        changed = False
        for attr in ['w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia']:
            val = rFonts_el.get(qn(attr))
            if val and ("devlys" in val.lower() or "kruti" in val.lower() or "remington" in val.lower()):
                rFonts_el.set(qn(attr), font_name)
                changed = True
        if changed:
            rFonts_el.set(qn('w:hint'), 'cs')
            # Also ensure cs slot is set even if it wasn't DevLys before
            if not rFonts_el.get(qn('w:cs')):
                rFonts_el.set(qn('w:cs'), font_name)
        return changed

    @classmethod
    def _patch_paragraph_formatting(cls, p, font_name="Mangal"):
        """
        Fix paragraph-level rPr (paragraph mark formatting) which Word uses
        as default run formatting. If it references DevLys fonts, Word may
        ignore run-level overrides for character classification.
        """
        pPr = p._p.find(qn('w:pPr'))
        if pPr is None:
            return
        rPr = pPr.find(qn('w:rPr'))
        if rPr is None:
            return
        rFonts = rPr.find(qn('w:rFonts'))
        if cls._patch_rfonts_element(rFonts, font_name):
            # Also set language on the paragraph-level rPr
            lang = rPr.find(qn('w:lang'))
            if lang is None:
                lang = OxmlElement('w:lang')
                rPr.append(lang)
            lang.set(qn('w:val'), 'hi-IN')
            lang.set(qn('w:bidi'), 'hi-IN')
            # Add cs flag
            cs = rPr.find(qn('w:cs'))
            if cs is None:
                cs = OxmlElement('w:cs')
                rPr.append(cs)

    @classmethod
    def _patch_styles(cls, doc, font_name="Mangal"):
        """
        Scan all styles in styles.xml and replace any DevLys/Kruti font 
        references with the target Unicode font. This prevents the style
        cascade from overriding our run-level font settings.
        """
        try:
            for style_el in doc.styles.element.findall(qn('w:style')):
                rPr = style_el.find(qn('w:rPr'))
                if rPr is not None:
                    rFonts = rPr.find(qn('w:rFonts'))
                    cls._patch_rfonts_element(rFonts, font_name)
        except Exception:
            pass

    @classmethod
    def convert_docx(cls, input_docx_path, output_docx_path, font_name="Mangal"):
        """
        Reads a DevLys-encoded DOCX file, translates all Hindi text sections 
        into Unicode, sets target font, and preserves complete document structure.
        """
        if not os.path.exists(input_docx_path):
            raise FileNotFoundError(f"Input file not found: {input_docx_path}")

        doc = Document(input_docx_path)

        # PHASE 0: Patch document-level styles that reference DevLys
        cls._patch_styles(doc, font_name)

        def process_paragraph(p):
            # First merge compatible runs to prevent run fragmentation bugs
            cls.merge_runs_compatible(p)

            any_converted = False
            for run in p.runs:
                text = run.text
                if not text or not text.strip():
                    continue

                # Check if this run is explicitly DevLys or contains DevLys content
                is_devlys = False
                if run.font and run.font.name:
                    f_name = run.font.name.lower()
                    if "devlys" in f_name or "kruti" in f_name or "remington" in f_name:
                        is_devlys = True
                
                # Fallback to structural heuristic check
                if not is_devlys:
                    # Performance optimization: Replace `any(ord(c)...)` loop with
                    # compiled regex `search` for checking Devanagari characters.
                    # This avoids Python iteration overhead and leverages C-level regex engine.
                    if not cls._devanagari_regex.search(text):
                        if not cls.is_likely_english(text):
                            is_devlys = True

                if is_devlys:
                    converted = cls.devlys_to_unicode_text(text)
                    if converted != text:
                        run.text = converted
                        cls.set_font_mangal(run, font_name)
                        any_converted = True

            # After converting runs, also patch the paragraph-level rPr
            if any_converted:
                cls._patch_paragraph_formatting(p, font_name)

        # 1. Process Body Paragraphs
        for p in doc.paragraphs:
            process_paragraph(p)

        # 2. Process Table Paragraphs
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        process_paragraph(p)

        # 3. Process Section Headers & Footers
        for section in doc.sections:
            for h_f in [section.header, section.footer, section.first_page_header, section.first_page_footer, section.even_page_header, section.even_page_footer]:
                if not h_f:
                    continue
                for p in h_f.paragraphs:
                    process_paragraph(p)
                for table in h_f.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for p in cell.paragraphs:
                                process_paragraph(p)

        # 4. Save converted document
        os.makedirs(os.path.dirname(os.path.abspath(output_docx_path)), exist_ok=True)
        doc.save(output_docx_path)
        return output_docx_path

