import re

def Unicode_to_KrutiDev(unicode_str):
    if not unicode_str: return ""
    s = str(unicode_str)
    
    # 1. Protect Date Hyphens (DD-MM-YYYY)
    s = re.sub(r'(\d{1,2})-(\d{1,2})-(\d{4})', r'\1@@@DASH@@@\2@@@DASH@@@\3', s)
    
    # 2. Pre-mapping

    # Global Asterisk to curly quote translation (before DevLys mapping)
    s = s.replace("**", "@@TEMP_DBL_AST@@")
    s = s.replace("*", "’")
    s = s.replace("@@TEMP_DBL_AST@@", "**")

    s = re.sub(r'([\u0900-\u097F])्िा', r'\1ि', s)
    s = s.replace("निमर्ित", "निर्मित")
    s = re.sub(r'(\d)\.(\d)', r'\1-\2', s)
    s = s.replace("/-", "@&")
    s = s.replace("एवज में", "एवज में")
    if "एवज" in s: s = s.replace("एवज", "एवज्")
    s = s.replace("स्वर्गीय", "स्व-")
    s = s.replace("स्व.", "स्व-")
    s = s.replace("पत्नि", "पत्नी")
    
    # Convert abbreviation dots to hyphens in Unicode (e.g. जे.बी. -> जे-बी-, नं. -> नं-)
    s = re.sub(r'([\u0900-\u097Fa-zA-Z])\.', r'\1-', s)
    
    # Quotes Identity
    s = s.replace("“", "Þ").replace("”", "ß")
    s = s.replace("‘", "^").replace("’", "*")
    s = s.replace("‘‘", "“").replace("’’", "”")
    
    # Identity Boilerplate & Specific Normalizations (Before full mapping)
    s = s.replace("(1).", "¼1½-")
    s = s.replace(", (2).", "] ¼2½-")
    s = s.replace("(2).", "¼2½-")
    s = s.replace(", (3).", "] ¼3½-")
    s = s.replace("(3).", "¼3½-")

    s = s.replace("प्रFke", "izFke").replace("प्रdkj", "izdkj")
    s = s.replace("प्रek.k", "izek.k")

    # Standard KrutiDev mapping pairs
    mapping = [
        ("‘", "^"), ("’", "*"), ("“", "Þ"), ("”", "ß"), ("(", "¼"), (")", "½"), ("{", "¿"), ("}", "À"), ("=", "¾"), ("।", "A"), ("?", "\\"), ("µ", "&"), ("॰", "Œ"), (",", "]"), 
        ("०", "å"), ("१", "ƒ"), ("२", "„"), ("३", "…"), ("४", "†"), ("५", "‡"), ("६", "ˆ"), ("७", "‰"), ("८", "Š"), ("९", "‹"), ("x", "Û"),
        ("फ़्", "¶"), ("क़", "d"), ("ख़", "[k"), ("ग़", "x"), ("ज़्", "T"), ("ज़", "t"), ("ड़", "M+"), ("ढ़", "<+"), ("फ़", "Q"), ("य़", ";"), ("ऱ", "j"), ("ऩ", "u"),
        ("त्त्", "Ù"), ("त्त", "Ùk"), ("क्त", "Dr"), ("दृ", "–"), ("कृ", "—"), ("ह्न", "à"), ("ह्य", "á"), ("हृ", "â"), ("ह्म", "ã"), ("ह्र", "ºz"), ("ह्", "º"), ("द्द", "í"), 
        ("क्ष्", "{"), ("क्ष", "{k"), ("त्र्", "«"), ("त्र", "="), ("ज्ञ", "K"), 
        ("छ्य", "Nî"), ("ट्य", "Vî"), ("ठ्य", "Bî"), ("ड्य", "Mî"), ("ढ्य", "<î"), ("द्य", "|"), ("द्व", "}"), ("श्र", "J"), 
        ("ट्र", "Vª"), ("ड्र", "Mª"), ("ढ्र", "<ªª"), ("छ्र", "Nª"), ("क्र", "Ø"), ("फ्र", "Ý"), ("द्र", "æ"), ("प्र", "ç"), ("ग्र", "xz"), 
        ("रु", "#"), ("रू", ":"), ("्र", "z"), 
        ("ओ", "vks"), ("औ", "vkS"), ("आ", "vk"), ("अ", "v"), ("ई", "bZ"), ("इ", "b"), ("उ", "m"), ("ऊ", "Å"), ("ऐ", ",s"), ("ए", ","), ("ऋ", "_"), 
        ("क्", "D"), ("क", "d"), ("क्क", "ô"), ("ख्", "["), ("ख", "[k"), ("ग्", "X"), ("ग", "x"), ("घ्", "?"), ("घ", "?k"), ("ङ", "³"), 
        ("चै", "pkS"), ("च्", "P"), ("च", "p"), ("छ", "N"), ("ज्", "T"), ("ज", "t"), ("झ्", "÷"), ("झ", ">"), ("ञ", "¥"), 
        ("ट्ट", "ê"), ("ट्ठ", "ë"), ("ट", "V"), ("ठ", "B"), ("ड्ड", "ì"), ("ड्ढ", "ï"), ("ड", "M"), ("ढ", "<"), ("ण्", "."), ("ण", ".k"), 
        ("त्", "R"), ("त", "r"), ("थ्", "F"), ("थ", "Fk"), ("द्ध", ")"), ("द", "n"), ("ध्", "/"), ("ध", "/k"), ("न्", "U"), ("न", "u"), 
        ("प्", "I"), ("प", "i"), ("फ्", "¶"), ("फ", "Q"), ("ब्", "C"), ("ब", "c"), ("भ्", "H"), ("भ", "Hk"), ("म्", "E"), ("म", "e"), 
        ("य्", "¸"), ("य", ";"), ("र", "j"), ("ल्", "Y"), ("ल", "y"), ("ळ", "G"), ("व्", "O"), ("व", "o"), ("श्", "'"), ("श", "'k"), ("ष्", "\""), ("ष", "\"k"), ("स्", "L"), ("स", "l"), ("ह", "g"), 
        ("ऑ", "v‚"), ("ॉ", "‚"), ("ो", "ks"), ("ौ", "kS"), ("ा", "k"), ("ी", "h"), ("ु", "q"), ("ू", "w"), ("ृ", "`"), ("े", "s"), ("ै", "S"), ("ं", "a"), ("ँ", "¡"), ("ः", "%"), ("ॅ", "W"), ("ऽ", "·"), ("ि", "f"), ("् ", "~ "), ("्", "~")
    ]
    
    # 3. Handle 'ि' Matra position in UNICODE before mapping
    # Consonant + ि -> ि + Consonant
    # regex matches any consonant (including half conjuncts) followed by ि
    s = re.sub(r'((?:[\u0900-\u0939]\u094d)?[\u0900-\u0939])ि', r'ि\1', s)

    # 4. Apply mapping
    res = s
    for uni, kru in mapping:
        res = res.replace(uni, kru)

    # 5. Reph (Z) logic - generic cluster-aware swapping
    res = res.replace("j~", "Z")
    chars = list(res)
    i = 0
    matras = set("khqwsSa¡%z‚")
    punctuation = set(" ,.?!()[]{}<>+-*/=;:\"'\n\r\tÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿœ")
    while i < len(chars):
        if chars[i] == 'Z':
            idx = i + 1
            if idx < len(chars) and chars[idx] == 'f':
                idx += 1
            
            consonant_consumed = False
            while (idx < len(chars) and 
                   chars[idx] not in matras and 
                   chars[idx] not in punctuation and 
                   not chars[idx].isdigit() and 
                   chars[idx] != 'f' and 
                   not consonant_consumed):
                idx += 1
                consonant_consumed = True
                if idx < len(chars) and chars[idx-1] == '~':
                    consonant_consumed = False
            
            while idx < len(chars) and chars[idx] in matras:
                idx += 1
            
            if idx > i + 1:
                z_char = chars[i]
                for k in range(i, idx - 1):
                    chars[k] = chars[k+1]
                chars[idx - 1] = z_char
                i = idx - 1
        i += 1
    res = "".join(chars)
    
    # 6. Firm-specific common word / ligature fixes
    res = res.replace("ojxxt", "oxZxt")
    res = res.replace("ojxQhV", "oxZQhV")
    res = res.replace("ojx", "oxZ")
    
    # 7. Restore and Clean
    res = res.replace("@@@DASH@@@", "-")
    
    # FINAL OVERRIDES
    res = res.replace("LoxhZ;", "Lo-").replace("LoxZh;", "Lo-")
    res = res.replace("Rr", "Ùk").replace("è", "/k")
    res = res.replace("d‚eu", "dkWeu").replace("ikfZdax", "ikfdZax").replace("ikfdaZx", "ikfdZax")
    res = res.replace("Iy‚V", "IykV")  # Normalize Plot
    res = res.replace("fç", "fiz")     # Normalize 'pri' like in Priyanka
    res = res.replace("ç", "iz")       # Normalize general 'pra'
    res = re.sub(r'[izç]+frfuf/k', 'izfrfuf/k', res)
    res = res.replace("çFke", "izFke").replace("çdkj", "izdkj").replace("çek.k", "izek.k")
    res = re.sub(r'(\d{2})&(\d{2})&(\d{4})', r'\1-\2-\3', res) # Protect global date hyphens mapped into & back to -
    
    return res

def normalize_relation_prefix(r_str, doc_type="RM"):
    if not r_str: return ""
    s = str(r_str).strip()
    s = " ".join(s.split())
    
    is_hindi = (doc_type == "SD") or any(ord(char) > 127 for char in s)
    if is_hindi:
        # Check if it's just the relation keyword itself
        keyword_map = {
            "son of": "पुत्र", "s/o": "पुत्र", "son": "पुत्र",
            "daughter of": "पुत्री", "d/o": "पुत्री", "daughter": "पुत्री",
            "wife of": "पत्नी", "w/o": "पत्नी", "wife": "पत्नी", "पत्नि": "पत्नी",
            "husband of": "पत्नी", "h/o": "पत्नी", "husband": "पत्नी",
            "care of": "केयर ऑफ", "c/o": "केयर ऑफ",
            "पुत्र": "पुत्र", "पुत्री": "पुत्री", "पत्नी": "पत्नी", "पति": "पत्नी", "केयर ऑफ": "केयर ऑफ"
        }
        val_clean = s.lower().replace('.', '').replace(':', '').strip()
        if val_clean in keyword_map:
            return keyword_map[val_clean]
            
        # Clean double/corrupt deceased prefixes
        s = re.sub(r'(स्वर्गीय|स्व\.|स्व\-)\s*(?:श्री\s*)?(?:र्गीय|स्वर्गीय|स्व\.|स्व\-)\s*(?:श्री\s*)?', r'\1 श्री ', s)
        
        # If it's already a normalized form like "पुत्र श्री राम" or "पुत्र स्वर्गीय श्री श्याम"
        if re.match(r'^(पुत्र|पुत्री|पत्नी|पति|केयर\s+ऑफ)\s+(?:श्री|श्रीमती|स्वर्गीय\s+श्री|स्व\.|स्व\-)\s+\S+', s):
            s = re.sub(r'\b(स्व\-|\bस्व\.)\s*(?:श्री)?\s*', 'स्वर्गीय श्री ', s)
            s = " ".join(s.split())
            return s
            
        # Otherwise, parse semantic relation text
        rel = "पुत्र"  # default
        if any(x in val_clean for x in ["daughter", "d/o", "पुत्री"]):
            rel = "पुत्री"
        elif any(x in val_clean for x in ["wife", "w/o", "husband", "h/o", "पत्नी", "पत्नि", "पति"]):
            rel = "पत्नी"
        elif any(x in val_clean for x in ["care", "c/o", "केयर"]):
            rel = "केयर ऑफ"
            
        # Extract relative's name
        prefix_pattern = r'^(?:father\'s\s+name|father\s+name|father|पिता\s+का\s+नाम|पिता|s/o|son\s+of|son|daughter\'s\s+name|daughter\s+name|daughter|पुत्री\s+का\s+नाम|पुत्री|d/o|wife\'s\s+name|wife\s+name|wife|पत्नी\s+का\s+नाम|पत्नी|पत्नि|w/o|husband\'s\s+name|husband\s+name|husband|पति\s+का\s+नाम|पति|h/o|care\s+of|c/o|केयर\s+ऑफ)\s*[:\-–—\s]*'
        name_part = re.sub(prefix_pattern, '', s, flags=re.IGNORECASE).strip()
        
        if not name_part or name_part == s:
            return s
            
        # Handle deceased prefix on relative name
        is_deceased = False
        if re.match(r'^(Late|स्व\.|स्वर्गीय|स्व\-)\b', name_part, re.IGNORECASE):
            is_deceased = True
            name_part = re.sub(r'^(Late|स्व\.|स्वर्गीय|स्व\-)\s*', '', name_part, flags=re.IGNORECASE).strip()
            
        # Strip any sub-salutation like Mr. or Shri or श्रीमती
        name_part = re.sub(r'^(Mr\.|Mr|Shri|Shree|श्री|श्रीमती)\s*', '', name_part, flags=re.IGNORECASE).strip()
        
        sal = "स्वर्गीय श्री" if is_deceased else "श्री"
        return f"{rel} {sal} {name_part}"
    else:
        r_map = {"son of": "S/o", "daughter of": "D/o", "wife of": "W/o", "husband of": "H/o", "care of": "C/o", "s/o": "S/o", "d/o": "D/o", "w/o": "W/o", "h/o": "H/o", "c/o": "C/o"}
        val = s.lower().replace('.', '').replace(':', '').strip()
        return r_map.get(val, s)

def extract_salutation_and_name(full_name):
    if not full_name: return "", ""
    s = str(full_name).strip()
    salutations = ["श्री", "श्रीमती", "सुश्री", "डॉ.", "Mr.", "Mrs.", "Ms.", "Dr.", "Late", "LoxhZ;", "स्व."]
    for sal in salutations:
        if s.startswith(sal): return sal, s[len(sal):].strip()
    return "", s

def normalize_name_salutation(name, relation=None, default_to_male=True):
    if not name: return ""
    s = str(name).strip()
    s = " ".join(s.split())
    
    # Handle deceased prefix first
    if re.match(r'^(Late|स्व\.|स्वर्गीय|स्व\-)\s*', s, re.IGNORECASE):
        name_part = re.sub(r'^(Late|स्व\.|स्वर्गीय|स्व\-)\s*', '', s, flags=re.IGNORECASE).strip()
        name_part = re.sub(r'^(Mr\.|Mr|Shri|Shree|श्री|श्रीमती)\s*', '', name_part, flags=re.IGNORECASE).strip()
        return "स्वर्गीय श्री " + name_part
        
    is_hindi = any(ord(char) > 127 for char in s)
    
    living_salutations = ["श्री", "श्रीमती", "सुश्री", "Mr.", "Mrs.", "Ms.", "Mr", "Mrs", "Ms"]
    for sal in living_salutations:
        if s.startswith(sal):
            if len(s) == len(sal) or s[len(sal)].isspace() or s[len(sal)] == '.':
                rest = s[len(sal):].strip()
                if rest.startswith('.'): rest = rest[1:].strip()
                if relation:
                    rel = relation.lower()
                    if any(x in rel for x in ["पत्नी", "पुत्री", "wife", "daughter", "smt", "mrs", "w/o", "d/o"]):
                        return ("श्रीमती " if is_hindi else "Mrs. ") + rest
                return s
                
    if relation:
        rel = relation.lower()
        if any(x in rel for x in ["पत्नी", "पुत्री", "wife", "daughter", "smt", "mrs", "w/o", "d/o"]):
            return ("श्रीमती " if is_hindi else "Mrs. ") + s
            
    if default_to_male:
        return ("श्री " if is_hindi else "Mr. ") + s
    else:
        return ("श्रीमती " if is_hindi else "Mrs. ") + s

def normalize_relative_salutation(name, relation_prefix=None):
    if not name: return ""
    s = str(name).strip()
    s = " ".join(s.split())
    
    if re.match(r'^(Late|स्व\.|स्वर्गीय|स्व\-)\s*', s, re.IGNORECASE):
        name_part = re.sub(r'^(Late|स्व\.|स्वर्गीय|स्व\-)\s*', '', s, flags=re.IGNORECASE).strip()
        name_part = re.sub(r'^(Mr\.|Mr|Shri|Shree|श्री|श्रीमती)\s*', '', name_part, flags=re.IGNORECASE).strip()
        return "स्वर्गीय श्री " + name_part
        
    salutations = ["श्री", "श्रीमती", "सुश्री", "डॉ.", "Mr.", "Mrs.", "Ms.", "Dr.", "Late", "LoxhZ;", "स्व."]
    for sal in salutations:
        if s.startswith(sal):
            if len(s) == len(sal) or s[len(sal)].isspace() or s[len(sal)] == '.':
                return s
                
    is_hindi = any(ord(char) > 127 for char in s)
    if relation_prefix:
        pref = relation_prefix.lower()
        if "स्व" in pref or "late" in pref: return s
    return ("श्री " if is_hindi else "Mr. ") + s

def parse_relation_text(relation_text):
    if not relation_text: return "", ""
    s = str(relation_text).strip()
    m = re.match(r'^(पुत्र|पुत्री|पत्नी|पति|केयर\s+ऑफ)\s+(.*)$', s)
    if m: return m.group(1), m.group(2)
    m = re.match(r'^(S/o|D/o|W/o|H/o|C/o|Son of|Daughter of|Wife of|Husband of|Care of)\s+(.*)$', s, re.IGNORECASE)
    if m: return m.group(1), m.group(2)
    return "", s

def format_date_with_dots(date_str):
    if not date_str: return ""
    return str(date_str).strip().replace("-", ".").replace("/", ".")

def format_date_to_ordinal_english(date_str):
    if not date_str: return ""
    # Parse DD.MM.YYYY, DD-MM-YYYY, YYYY-MM-DD
    cleaned = str(date_str).strip().replace(".", "-").replace("/", "-")
    
    import datetime
    dt = None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d-%m-%y", "%Y/%m/%d"):
        try:
            dt = datetime.datetime.strptime(cleaned, fmt)
            break
        except ValueError:
            continue
            
    if not dt:
        return date_str
        
    day = dt.day
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        
    month_name = dt.strftime("%B")
    return f"{day}{suffix} {month_name}, {year}" if 'year' in locals() else f"{day}{suffix} {month_name}, {dt.year}"

def amount_to_words(amount_str):
    try:
        from num2words import num2words
        s = str(amount_str).replace(',', '').replace('/-', '').strip()
        if not s.isdigit(): return amount_str
        return num2words(int(s), lang='en_IN').replace('-', ' ').title() + " Only"
    except: return amount_str

def format_indian_currency(amount_str):
    if not amount_str: return ""
    amount_str = str(amount_str).replace(',', '').strip()
    try:
        # Check if float or int
        if '.' in amount_str:
            num = float(amount_str)
            s = f"{num:.2f}"
            int_part, dec_part = s.split('.')
            if len(int_part) > 3:
                last_three = int_part[-3:]
                other = int_part[:-3][::-1]
                parts = [other[i:i+2] for i in range(0, len(other), 2)]
                formatted_int = ",".join(parts)[::-1] + "," + last_three
            else:
                formatted_int = int_part
            return f"{formatted_int}.{dec_part}/-"
        else:
            s = str(int(amount_str))
            if len(s) > 3:
                last_three = s[-3:]
                other = s[:-3][::-1]
                parts = [other[i:i+2] for i in range(0, len(other), 2)]
                formatted_amount = ",".join(parts)[::-1] + "," + last_three + "/-"
            else:
                formatted_amount = s + "/-"
            return formatted_amount
    except ValueError:
        return amount_str

def clean_aadhar_address(address_str):
    if not address_str: return ""
    s = str(address_str).strip()
    s = re.sub(r'^(?:S/o|D/o|W/o|H/o|C/o|Son of|Daughter of|Wife of|Husband of|Care of)[^,]*,?\s*', '', s, flags=re.IGNORECASE).strip()
    return s

def convert_hindi_digits_to_english(data):
    if data is None:
        return data
    hindi_to_eng = {
        '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
        '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
    }
    
    def convert_str(s):
        if not isinstance(s, str):
            return s
        for h, e in hindi_to_eng.items():
            s = s.replace(h, e)
        return s
        
    if isinstance(data, dict):
        return {k: convert_hindi_digits_to_english(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_hindi_digits_to_english(item) for item in data]
    elif isinstance(data, str):
        return convert_str(data)
    return data

def parse_and_format_chain(raw_text):
    if not raw_text:
        return "", []
    
    lines = re.split(r'\n+|\r+', str(raw_text))
    
    clean_docs = []
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        line_lower = line_str.lower()
        if any(w in line_lower for w in ["proposed", "purposed", "undertaking"]):
            # Check if this is a proposed Sale Deed
            if "sale deed" in line_lower or "sale-deed" in line_lower:
                match_exec = re.search(r'executed\s+by\s+(.*?)(?:\s+for\s+the\s+sale\s+of|\s+for\s+sale\s+of|$)', line_str, re.IGNORECASE)
                executant = match_exec.group(1).strip().rstrip('.') if match_exec else "_________________"
                
                # Format to the template requested by user
                formatted_doc = f"Original Registered Sale deed dated _________________ executed by {executant}, for the sale of Said Property alongwith site plan and the same has been registered in the office of Sub Registrar Jaipur __________ on _____________, as R.S. No. _______________________________________, Book No. ________, Vol. No. _________, at Page No. ___________ and affixed on Additional Book No. _________ Volume No. ____________ at Page No. ___________ to____________."
                clean_docs.append(formatted_doc)
            continue
            
        cleaned = re.sub(r'^(?:[a-zA-Z0-9]+[\.\)]|[\-\*•\s]+)\s*', '', line_str).strip()
        
        if cleaned:
            clean_docs.append(cleaned)
            
    formatted_lines = []
    for idx, doc in enumerate(clean_docs):
        bullet = chr(ord('a') + idx)
        formatted_lines.append(f"{bullet}.\t{doc}")
        
    formatted_text = "\n".join(formatted_lines)
    return formatted_text, clean_docs

def select_relevant_pdf_pages(pdf_path, keywords=None):
    import pypdf
    if keywords is None:
        keywords = []
    
    try:
        reader = pypdf.PdfReader(pdf_path)
        total_pages = len(reader.pages)
        if total_pages == 0:
            return []
            
        # Check if PDF contains any extractable text (to detect scanned vs searchable)
        has_any_text = False
        page_texts = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            page_texts.append(text)
            if text.strip():
                has_any_text = True
                
        if not has_any_text:
            return [] # Scanned PDF fallback
            
        # Hybrid page selection: always select page 1, 2 and the last page
        selected_indices = {0, 1, total_pages - 1}
        selected_indices = {idx for idx in selected_indices if 0 <= idx < total_pages}
        
        # Match keywords on middle pages
        lower_keywords = [kw.lower() for kw in keywords]
        for idx in range(2, total_pages - 1):
            page_text_lower = page_texts[idx].lower()
            if any(kw in page_text_lower for kw in lower_keywords):
                selected_indices.add(idx)
                
        sorted_indices = sorted(list(selected_indices))
        
        # Cap at 12 pages max (prioritizing first 2, last 1, and then middle matching pages)
        if len(sorted_indices) > 12:
            # Always keep first two and last page if they were selected
            essential = {0, 1, total_pages - 1}
            essential = {idx for idx in essential if idx in sorted_indices}
            extras = [idx for idx in sorted_indices if idx not in essential]
            
            # Take extra pages up to the cap of 12
            allowed_extras_count = 12 - len(essential)
            sorted_indices = sorted(list(essential) + extras[:allowed_extras_count])
            
        return sorted_indices
    except Exception as e:
        print(f"[PDF Helper Warning] Failed to inspect PDF {pdf_path}: {e}")
        return []

def extract_pdf_pages_text(pdf_path, page_indices):
    import pypdf
    try:
        reader = pypdf.PdfReader(pdf_path)
        output_text = []
        for idx in page_indices:
            if 0 <= idx < len(reader.pages):
                page_txt = reader.pages[idx].extract_text() or ""
                output_text.append(f"--- [Page {idx + 1}] ---\n{page_txt}")
        return "\n\n".join(output_text)
    except Exception as e:
        print(f"[PDF Helper Warning] Failed to extract text for PDF {pdf_path}: {e}")
        return ""

def validate_case_id(case_id):
    import re
    if not case_id or not isinstance(case_id, str):
        return False
    return bool(re.match(r"^case_\d+$", case_id))

def validate_bucket_name(bucket_name):
    whitelist = {'kyc', 'legal', 'ats', 'title_chain', 'ocr'}
    return bucket_name in whitelist

def is_safe_path(base_dir, path):
    import os
    base = os.path.realpath(base_dir)
    matchpath = os.path.realpath(path)
    return matchpath == base or matchpath.startswith(base + os.sep)


def prepare_image_for_nim(image_bytes: bytes, max_b64_len: int = 175000) -> str:
    import base64
    import io
    from PIL import Image
    
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')
        
    quality = 90
    scale = 1.0
    
    while True:
        w, h = int(img.width * scale), int(img.height * scale)
        if scale < 1.0:
            temp_img = img.resize((w, h), Image.Resampling.LANCZOS)
        else:
            temp_img = img
            
        out_arr = io.BytesIO()
        temp_img.save(out_arr, format='JPEG', quality=quality)
        b64_data = base64.b64encode(out_arr.getvalue()).decode('utf-8')
        b64_str = f"data:image/jpeg;base64,{b64_data}"
        
        if len(b64_str) < max_b64_len:
            return b64_str
            
        if quality > 30:
            quality -= 10
        else:
            scale -= 0.1
            quality = 80
            
        if scale <= 0.1:
            return b64_str


