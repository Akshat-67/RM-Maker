import re

def Unicode_to_KrutiDev(unicode_str):
    if not unicode_str: return ""
    s = str(unicode_str)
    
    # 1. Protect Date Hyphens (DD-MM-YYYY)
    s = re.sub(r'(\d{1,2})-(\d{1,2})-(\d{4})', r'\1@@@DASH@@@\2@@@DASH@@@\3', s)
    
    # 2. Pre-mapping
    s = re.sub(r'([\u0900-\u097F])्िा', r'\1ि', s)
    s = s.replace("निमर्ित", "निर्मित")
    s = s.replace("गणतिपुरा", "गणपतपुरा")
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
    
    return res

def normalize_relation_prefix(r_str, doc_type="RM"):
    if not r_str: return ""
    s = str(r_str).strip()
    is_hindi = (doc_type == "SD") or any(ord(char) > 127 for char in s)
    if is_hindi:
        r_map = {"son of": "पुत्र स्व-", "daughter of": "पुत्री श्री", "wife of": "पत्नी श्री", "husband of": "पति श्री", "care of": "केयर ऑफ", "s/o": "पुत्र स्व-", "d/o": "पुत्री श्री", "w/o": "पत्नी श्री", "h/o": "पति श्री", "c/o": "केयर ऑफ"}
        if doc_type == "SD":
            s = s.replace("स्वर्गीय", "स्व-").replace("स्व.", "स्व-").replace("पत्नि", "पत्नी")
        val = s.lower().replace('.', '').replace(':', '').strip()
        return r_map.get(val, s)
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
    salutations = ["श्री", "श्रीमती", "सुश्री", "डॉ.", "Mr.", "Mrs.", "Ms.", "Dr."]
    for sal in salutations:
        if s.startswith(sal): return s
    is_hindi = any(ord(char) > 127 for char in s)
    if relation:
        rel = relation.lower()
        if any(x in rel for x in ["पत्नी", "पुत्री", "wife", "daughter", "smt", "mrs"]):
            return ("श्रीमती " if is_hindi else "Mrs. ") + s
    return ("श्री " if is_hindi else "Mr. ") + s

def normalize_relative_salutation(name, relation_prefix=None):
    if not name: return ""
    s = str(name).strip()
    salutations = ["श्री", "श्रीमती", "सुश्री", "डॉ.", "Mr.", "Mrs.", "Ms.", "Dr.", "Late", "LoxhZ;", "स्व."]
    for sal in salutations:
        if s.startswith(sal): return sal, s[len(sal):].strip()
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
