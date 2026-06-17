import os
import json
import docx

keywords = ["ज्वारा", "jwara", "jvara", "jwara ram", "jvara ram", "madhuban", "मधुबन"]

def search_text(text, filepath):
    text_lower = text.lower()
    for kw in keywords:
        if kw in text_lower:
            print(f"MATCH '{kw}' in file: {filepath}")
            # print snippet
            idx = text_lower.find(kw)
            start = max(0, idx - 50)
            end = min(len(text), idx + len(kw) + 100)
            print(f"Snippet: ... {text[start:end]} ...")

def search_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            text = json.dumps(data, ensure_ascii=False)
            search_text(text, filepath)
    except Exception as e:
        # Try raw read
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                search_text(f.read(), filepath)
        except Exception:
            pass

def search_docx(filepath):
    try:
        doc = docx.Document(filepath)
        fullText = []
        for para in doc.paragraphs:
            fullText.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    fullText.append(cell.text)
        text = "\n".join(fullText)
        search_text(text, filepath)
    except Exception as e:
        pass

def search_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext in ['.json', '.txt', '.py', '.log', '.html', '.css', '.md']:
        search_json(filepath)
    elif ext in ['.docx']:
        search_docx(filepath)

def walk_and_search(directory):
    for root, dirs, files in os.walk(directory):
        # Skip virtualenvs or git if any
        if '.git' in dirs:
            dirs.remove('.git')
        if '.gemini' in dirs:
            dirs.remove('.gemini')
        for file in files:
            path = os.path.join(root, file)
            search_file(path)

if __name__ == "__main__":
    print("Searching workspace...")
    walk_and_search(".")
