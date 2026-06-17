import os
import sys
import requests
from docx import Document

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from template_tools.builder_core import get_discovery_prompt, DocManipulator

TEST_DOC_PATH = "templates/SALE_DEED/manoj kumar & Monu kumari MW +EAST PART OF BALAJI NAGAR+SO PATTA+3REC+SD.docx"
NVIDIA_API_KEY = "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"
nvidia_url = "https://integrate.api.nvidia.com/v1/chat/completions"

def run_model(model_name, filename):
    doc = Document(TEST_DOC_PATH)
    chunks = []
    for part_name, part in DocManipulator.iter_story_parts(doc):
        for p in DocManipulator.iter_paragraphs_deep(part):
            if p.text.strip():
                chunks.append(p.text.strip())
    content = "\n".join(chunks)
    base_prompt = get_discovery_prompt(content, "SD")
    
    # Refined prompt instruction to avoid loops and duplicates
    prompt = base_prompt + "\nSTRICT CONSTRAINT: Each unique string from the document must appear as a key in the JSON dictionary EXACTLY ONCE. DO NOT output duplicate keys, and DO NOT repeat mappings. Keep the JSON compact and complete. Do not truncate the JSON output."

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "top_p": 0.7,
        "max_tokens": 4096
    }
    
    print(f"Requesting {model_name}...")
    try:
        res = requests.post(nvidia_url, headers=headers, json=payload, timeout=120)
        print(f"Status Code for {model_name}: {res.status_code}")
        if res.status_code == 200:
            raw = res.json()['choices'][0]['message']['content']
            out_path = f"scratch/{filename}"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(raw)
            print(f"Saved to {out_path} (length: {len(raw)})")
        else:
            print(f"Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"Failed for {model_name}: {e}")

def main():
    # Test Llama 3.1 8B first
    run_model("meta/llama-3.1-8b-instruct", "llama_8b_clean.txt")
    # Test Llama 3.3 70B second
    run_model("meta/llama-3.3-70b-instruct", "llama_70b_clean.txt")

if __name__ == "__main__":
    main()
