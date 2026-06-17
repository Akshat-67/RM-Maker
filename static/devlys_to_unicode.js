/**
 * DevLys 010 / Kruti Dev 010 to Unicode Hindi Converter
 * Standard Remington Mapping
 */

function isLikelyEnglish(text) {
    if (!text) return true;
    
    // 1. Check for common English legal/corporate words
    const commonEnglish = /\b(Home|First|Finance|Company|India|Limited|Bank|Loan|Agreement|Office|Court|Deed|Sale|Register|Mortgage|Borrower|Lender|Seller|Buyer|Witness|Property|Registration|Number|Date|Tehsil|District|Village|Scheme|Plot|Area|Amount|Words|Hypothecation)\b/i;
    if (commonEnglish.test(text)) return true;

    // 2. Check for sequences that look like English words (Consonant-Vowel-Consonant)
    // DevLys usually has 'vowels' in positions that don't match English (e.g. 'f' at start for 'i')
    const englishPattern = /^[A-Z][a-z]{2,10}(\s+[A-Z][a-z]{2,10})*$/;
    if (englishPattern.test(text)) return true;

    // 3. Alphanumeric codes are usually English (LAN, PAN, Reg No)
    if (/[0-9]/.test(text) && /[a-zA-Z]/.test(text) && text.length < 15) return true;

    return false;
}

function devlysToUnicode(text) {
    if (!text) return "";
    
    // 0. If it's already Unicode Hindi, skip
    if (/[\u0900-\u097F]/.test(text)) return text;

    // 1. Heuristic: If it looks like English, don't touch it
    if (isLikelyEnglish(text)) return text;

    let modified_substring = text;

    // Complete Remington Mapping (DevLys 010)
    const mapping = [
        ["ñ", "्र"], ["Q+Z", "त्त"], ["sas", "ँ"], ["aa", "ा"], [")Z", "ा"], ["ZZ", "ा"],
        ["å", "ॐ"], ["ƒ", "ऽ"], ["„", "।"], ["…", "‘"], ["†", "’"], ["‡", "“"], ["ˆ", "”"], ["‰", "्र"], ["Š", "्र"], ["‹", "्र"], ["Œ", "्र"],
        ["f", "ि"], ["i", "ी"], ["k", "ा"], ["A", "ा"], ["a", "ा"],
        ["q", "फ"], ["w", "ू"], ["e", "म"], ["r", "त"], ["t", "ज"], ["y", "ल"], ["u", "न"], ["o", "व"], ["p", "च"],
        ["s", "ए"], ["d", "क"], ["g", "ह"], ["h", "प"], ["j", "र"], ["l", "स"], [";", "य"], ["'", "श"],
        ["x", "ग"], ["c", "ब"], ["v", "अ"], ["b", "इ"], ["n", "द"], ["m", "उ"], [",", "ध"], [".", "ण्"], ["/", "ठ"],
        ["Q", "फ"], ["W", "ॅ"], ["E", "म्"], ["R", "त्"], ["T", "ज्"], ["Y", "ल्"], ["U", "न्"], ["I", "प्"], ["O", "व्"], ["P", "च्"],
        ["S", "ऐ"], ["D", "क्"], ["F", "थ्"], ["G", "ह"], ["H", "भ्"], ["J", "श्र"], ["K", "ज्ञ"], ["L", "स"], [":", "ष्"], ["\"", "ष्"],
        ["X", "घ्"], ["C", "ब्"], ["V", "अ"], ["B", "इ"], ["N", "छ"], ["M", "ड"], ["<", "ख"], [">", "झ"], ["?", "घ"],
        ["~", "्र"], ["`", "़"], ["1", "१"], ["2", "२"], ["3", "३"], ["4", "४"], ["5", "५"], ["6", "६"], ["7", "७"], ["8", "८"], ["9", "९"], ["0", "०"],
        ["-", "."], ["=", "ृ"], ["+", "ऋ"], ["_", ")"], ["[", "ख्"], ["]", ""], ["{", "क्ष्"], ["}", "द्व"], ["|", "्र"], ["\\", "़"]
    ];

    let result = "";
    for (let i = 0; i < modified_substring.length; i++) {
        let found = false;
        let char = modified_substring[i];
        for (let j = 0; j < mapping.length; j++) {
            if (char === mapping[j][0]) {
                result += mapping[j][1];
                found = true;
                break;
            }
        }
        if (!found) result += char;
    }

    // 2. Fix 'i' matra (ि) - it comes BEFORE the character in DevLys but AFTER in Unicode (logically)
    // Actually, in Unicode it's character + matra.
    // Remington 'f' is 'ि'. 'fk' is 'कि'.
    // Result of mapping 'fk' is 'ि' + 'क'. We need 'क' + 'ि'.
    
    // Reorder ि across single characters and conjuncts
    result = result.replace(/ि([\u0900-\u097F][्]?[\u0900-\u097F]?)/g, "$1ि");
    
    // 3. Fix 'Reph' (र्) 
    // In Remington, 'Z' is Reph and comes AFTER the character. 
    // 'kZ' (काZ) -> 'कार्'. 
    // Mapping 'kZ' -> 'क' + 'ा' + 'Z'. 
    // We need to find Z and move it to become 'र्' before the character.
    result = result.replace(/([\u0900-\u097F])Z/g, "र्$1");

    return result;
}
