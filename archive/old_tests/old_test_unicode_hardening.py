"""Regression tests for Unicode converter hardening. Checks specific problematic DevLys ASCII strings for proper Unicode conversion."""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

from utils.devlys_to_unicode import DevLysToUnicodeConverter

def test_words():
    # Format: (DevLys input, Expected Unicode Hindi)
    test_cases = [
        ("va’k", "अंश"),
        ("va'k", "अंश"),
        ("eq’rjdk", "मुश्तरका"),
        ("eq'rjdk", "मुश्तरका"),
        ("oÆ.kr", "वर्णित"),
        ("{kfriwÆr", "क्षतिपूर्ति"),
        ("jkf’k", "राशि"),
        ("jkf'k", "राशि"),
        ("if’pe", "पश्चिम"),
        ("if'pe", "पश्चिम"),
        ("r;’kqnk", "तयशुदा"),
        ("r;'kqnk", "तयशुदा"),
        ("Dr", "क्त"),
    ]
    
    # Let's add more real word examples
    # Alt+0198 is represented as '\u00c6' in python (Æ)
    
    print("=== RUNNING CONVERTER REGRESSION TESTS ===")
    failures = 0
    for idx, (inp, expected) in enumerate(test_cases):
        output = DevLysToUnicodeConverter.devlys_to_unicode_text(inp)
        if output == expected:
            print(f"PASS [{idx:2d}]: {inp!r} -> {output}")
        else:
            print(f"FAIL [{idx:2d}]: {inp!r} -> {output!r} (Expected: {expected!r})")
            failures += 1
            
    if failures == 0:
        print("\nSUCCESS: All converter tests passed!")
    else:
        print(f"\nFAILURE: {failures} converter tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    test_words()
