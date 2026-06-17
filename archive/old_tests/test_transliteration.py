import sys
sys.stdout.reconfigure(encoding='utf-8')

# Unicode to KrutiDev function
def Unicode_to_KrutiDev(unicode_substring):
    modified_substring = unicode_substring
    
    array_one = ["‘",   "’",   "“",   "”",   "(",    ")",   "{",    "}",   "=", "।",  "?",  "-",  "µ", "॰", ",", ".", "् ", 
    "०",  "१",  "२",  "३",     "४",   "५",  "६",   "७",   "८",   "९", "x", 
    
    "फ़्",  "क़",  "ख़",  "ग़", "ज़्", "ज़",  "ड़",  "ढ़",   "फ़",  "य़",  "ऱ",  "<b>ऩ</b>",  
    "त्त्",   "त्त",     "क्त",  "दृ",  "कृ",
    
    "ह्न",  "ह्य",  "हृ",  "ह्म",  "ह्र",  "ह्",   "द्द",  "क्ष्", "क्ष", "त्र्", "त्र","ज्ञ",
    "छ्य",  "ट्य",  "ठ्य",  "ड्य",  "ढ्य", "द्य","द्व",
    "श्र",  "ट्र",    "ड्र",    "ढ्र",    "छ्र",   "क्र",  "फ्र",  "द्र",   "प्र",   "ग्र", "रु",  "रू",
    "्र",
    
    "ओ",  "औ",  "आ",   "अ",   "ई",   "इ",  "उ",   "ऊ",  "ऐ",  "ए", "ऋ",
    
    "क्",  "क",  "क्क",  "ख्",   "ख",    "ग्",   "ग",  "घ्",  "घ",    "ङ",
    "चै",   "च्",   "च",   "छ",  "ज्", "ज",   "झ्",  "झ",   "ञ",
    
    "ट्ट",   "ट्ठ",   "ट",   "ठ",   "ड्ड",   "ड्ढ",  "ड",   "ढ",  "ण्", "ण",  
    "त्",  "त",  "थ्", "थ",  "द्ध",  "द", "ध्", "ध",  "न्",  "न",  
    
    "प्",  "प",  "फ्", "फ",  "ब्",  "ब", "भ्",  "भ",  "म्",  "म",
    "य्",  "य",  "र",  "ल्", "ल",  "ळ",  "व्",  "व", 
    "श्", "श",  "ष्", "ष",  "स्",   "स",   "ह",     
    
    "ऑ",   "ॉ",  "ो",   "ौ",   "ा",   "ी",   "ु",   "ू",   "ृ",   "े",   "ै",
    "ं",   "ँ",   "ः",   "ॅ",    "ऽ",  "् ", "्" ]
    
    array_two = ["^", "*",  "Þ", "ß", "¼", "½", "¿", "À", "¾", "A", "\\", "&", "&", "Œ", "]","-","~ ", 
    "å",  "ƒ",  "„",   "…",   "†",   "‡",   "ˆ",   "‰",   "Š",   "‹","Û",
    
    "¶",   "d",    "[k",  "x",  "T",  "t",   "M+", "<+", "Q",  ";",    "j",   "u",
    "Ù",   "Ùk",   "Dr",    "–",   "—",       
    
    "à",   "á",    "â",   "ã",   "ºz",  "º",   "í", "{", "{k",  "«", "=","K", 
    "Nî",   "Vî",    "Bî",   "Mî",   "<î", "|","}",
    "J",   "Vª",   "Mª",  "<ªª",  "Nª",   "Ø",  "Ý",   "æ", "ç", "xz", "#", ":",
    "z",
    
    "vks",  "vkS",  "vk",    "v",   "bZ",  "b",  "m",  "Å",  ",s",  ",",   "_",
    
    "D",  "d",    "ô",     "[",     "[k",    "X",   "x",  "?",    "?k",   "³", 
    "pkS",  "P",    "p",  "N",   "T",    "t",   "÷",  ">",   "¥",
    
    "ê",      "ë",      "V",  "B",   "ì",       "ï",     "M",  "<",  ".", ".k",   
    "R",  "r",   "F", "Fk",  ")",    "n", "/",  "/k",  "U", "u",   
    
    "I",  "i",   "¶", "Q",   "C",  "c",  "H",  "Hk", "E",   "e",
    "¸",   ";",    "j",  "Y",   "y",  "G",  "O",  "o",
    "'", "'k",  "\"", "\"k", "L",   "l",   "g",      
    
    "v‚",    "‚",    "ks",   "kS",   "k",     "h",    "q",   "w",   "`",    "s",    "S",
    "a",    "¡",    "%",     "W",   "·",   "~ ", "~"]
    
    array_one_length = len(array_one)
    
    # Specialty characters
    modified_substring = modified_substring.replace ("क़", "क़")   
    modified_substring = modified_substring.replace ("ख़‌", "ख़")
    modified_substring = modified_substring.replace ("ग़", "ग़")
    modified_substring = modified_substring.replace ("ज़", "ज़")
    modified_substring = modified_substring.replace ("ड़", "ड़")
    modified_substring = modified_substring.replace ("ढ़", "ढ़")
    modified_substring = modified_substring.replace ("ऩ", "ऩ")
    modified_substring = modified_substring.replace ("फ़", "फ़")
    modified_substring = modified_substring.replace ("य़", "य़")
    modified_substring = modified_substring.replace ("ऱ", "ऱ")
    modified_substring = modified_substring.replace("ि","f")
    
    # Replace Unicode with ASCII
    for input_symbol_idx in range(0, array_one_length):
        modified_substring = modified_substring.replace(array_one[input_symbol_idx ] , array_two[input_symbol_idx] )
    
    # Move "f"  to correct position
    modified_substring = "  " + modified_substring + "  "
    position_of_f = modified_substring.find("f")
    while (position_of_f != -1):    
        modified_substring = modified_substring[:position_of_f-1] + modified_substring[position_of_f] + modified_substring[position_of_f-1] + modified_substring[position_of_f+1:]
        position_of_f = modified_substring.find("f", position_of_f +1 ) # search for f ahead of the current position.
    modified_substring = modified_substring.strip()
    
    # Move "half R"  to correct position and replace
    modified_substring = "  " + modified_substring + "  "
    position_of_r = modified_substring.find("j~")
    set_of_matras =  ["‚",    "ks",   "kS",   "k",     "h",    "q",   "w",   "`",    "s",    "S", "a",    "¡",    "%",     "W",   "·",   "~ ", "~"]
    while (position_of_r != -1):    
        modified_substring = modified_substring.replace("j~","",1)
        if modified_substring[position_of_r + 1] in set_of_matras:
            modified_substring = modified_substring[:position_of_r + 2] + "Z" + modified_substring[position_of_r + 2:]
        else:
            modified_substring = modified_substring[:position_of_r + 1] + "Z" + modified_substring[position_of_r + 1:]
        position_of_r = modified_substring.find("j~")
    modified_substring = modified_substring.strip()
    
    return modified_substring

def test_transliterate():
    print("Testing Unicode_to_KrutiDev...")
    # Test Name: विवेक सक्सेना
    output = Unicode_to_KrutiDev("विवेक सक्सेना")
    print(f"विवेक सक्सेना -> {output}")
    # In some Gist translations, Half-consonant mapping for क् might differ.
    # Let's assert if it maps correctly.
    assert "foosd" in output, "Failed to map विवेक to foosd"
    assert "lDlSuk" in output or "lDlsuk" in output or "lDsluk" in output, f"Failed to map सक्सेना: got {output}"
    print("✓ Unicode to KrutiDev test passed!")

if __name__ == "__main__":
    test_transliterate()
