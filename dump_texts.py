import docx
import os

def get_text(filename):
    doc = docx.Document(filename)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)

if __name__ == "__main__":
    actual_path = os.path.join('Test', 'ACTUAL.docx')
    ai_path = os.path.join('Test', 'AI.docx')
    
    print("--- ACTUAL.docx ---")
    print(get_text(actual_path))
    print("\n--- AI.docx ---")
    print(get_text(ai_path))
