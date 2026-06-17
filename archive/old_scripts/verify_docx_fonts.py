from docx import Document
from docx.oxml.ns import qn
import os

def main():
    try:
        import sys
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    f_path = "scratch/converted_manoj_kumar.docx"
    if not os.path.exists(f_path):
        print("Converted file not found")
        return
        
    doc = Document(f_path)
    print("Verifying font settings for first 5 paragraphs with runs...")
    
    count = 0
    for p_idx, p in enumerate(doc.paragraphs):
        if not p.text.strip():
            continue
            
        print(f"\nParagraph {p_idx}: {repr(p.text[:50])}...")
        for r_idx, run in enumerate(p.runs):
            font = run.font
            print(f"  Run {r_idx}: {repr(run.text)}")
            print(f"    Font Name: {font.name}")
            
            # Check OXML font settings
            try:
                rPr = run._r.get_or_add_rPr()
                rFonts = rPr.get_or_add_rFonts()
                ascii_font = rFonts.get(qn('w:ascii'))
                hAnsi_font = rFonts.get(qn('w:hAnsi'))
                cs_font = rFonts.get(qn('w:cs'))
                
                # Check lang settings
                lang = rPr.find(qn('w:lang'))
                lang_val = lang.get(qn('w:val')) if lang is not None else None
                lang_bidi = lang.get(qn('w:bidi')) if lang is not None else None
                
                # Check cs element
                has_cs_tag = rPr.find(qn('w:cs')) is not None
                
                print(f"    XML Fonts: ascii={ascii_font}, hAnsi={hAnsi_font}, cs={cs_font}")
                print(f"    XML Lang: val={lang_val}, bidi={lang_bidi} | Has CS Tag: {has_cs_tag}")
            except Exception as e:
                print(f"    XML Fonts lookup failed: {e}")
                
        count += 1
        if count >= 5:
            break

if __name__ == "__main__":
    main()
