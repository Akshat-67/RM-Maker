import docx
import difflib
import re

def clean(text):
    # Remove extra spaces and normalized characters for parity check
    t = text.strip()
    t = re.sub(r'\s+', ' ', t)
    return t

def compare_docs(actual_path, ai_path):
    doc_actual = docx.Document(actual_path)
    doc_ai = docx.Document(ai_path)
    
    # Filter out empty paragraphs
    actual_paras = [clean(p.text) for p in doc_actual.paragraphs if p.text.strip()]
    ai_paras = [clean(p.text) for p in doc_ai.paragraphs if p.text.strip()]
    
    print(f"Total Content Paras - ACTUAL: {len(actual_paras)}, AI: {len(ai_paras)}")
    
    # Surgical comparison
    for i in range(min(len(actual_paras), len(ai_paras))):
        act = actual_paras[i]
        gen = ai_paras[i]
        
        if act != gen:
            print(f"\n[PARA {i}]")
            print(f"ACTUAL: {act}")
            print(f"GEN   : {gen}")
            
            # Find first index of difference
            for j in range(min(len(act), len(gen))):
                if act[j] != gen[j]:
                    ctx_start = max(0, j-10)
                    ctx_end = min(len(act), j+30)
                    print(f"DIFF AT {j}: ...{act[ctx_start:ctx_end]}...")
                    print(f"            ...{gen[ctx_start:ctx_end]}...")
                    break
            
if __name__ == "__main__":
    compare_docs("Test/ACTUAL.docx", "Validated_AI.docx")
