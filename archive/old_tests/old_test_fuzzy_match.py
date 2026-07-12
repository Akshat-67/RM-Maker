import re
import difflib

def find_fuzzy_match_improved(text, target, threshold=0.85):
    # Normalize spaces
    haystack = re.sub(r"\s+", " ", text).strip().casefold()
    target_clean = re.sub(r"\s+", " ", target).strip().casefold()
    
    if not target_clean or not haystack:
        return None
        
    # Exact match first
    exact_pattern = re.escape(target_clean).replace(r"\ ", r"\s+")
    m = re.search(exact_pattern, haystack, re.IGNORECASE)
    if m:
        return m.start(), m.end()
        
    # If not exact match and target is long enough, do sliding window fuzzy match
    if len(target_clean) >= 15:
        n = len(target_clean)
        best_ratio = 0
        best_span = None
        
        # Slide window of size n (with a small padding of +/- 5 characters)
        for w_size in range(n - 3, n + 4):
            for i in range(len(haystack) - w_size + 1):
                sub = haystack[i:i+w_size]
                ratio = difflib.SequenceMatcher(None, target_clean, sub).ratio()
                if ratio > best_ratio and ratio >= threshold:
                    best_ratio = ratio
                    best_span = (i, i + w_size)
                    
        if best_span:
            print(f"Fuzzy matched with ratio {best_ratio:.2f}: span {best_span} -> '{haystack[best_span[0]:best_span[1]]}'")
            return best_span
            
    return None

def main():
    text = "Jh foLoukFk iq= Jh Hkxoku flag] fuoklh%& ¶ySV u- 007 ch] 2 CykWd] vuqie vikVZesUV] izrku uxj] lkaxkusj] lsDVj 11 t;iqj jktLFkku&302033"
    target = "¶ySV u- 007 ch] 2 CykWd] vuqie vikVZesUV] izrku uxj] lkaxkusj] lsDVr 11 t;iqr jktLFkku&302033"
    
    match = find_fuzzy_match_improved(text, target)
    print(f"Match result: {match}")

if __name__ == "__main__":
    main()
