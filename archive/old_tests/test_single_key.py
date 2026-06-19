import os
import sys
from google import genai
from docx import Document

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from template_tools.builder_core import get_discovery_prompt, DocManipulator

TEST_DOC_PATH = "templates/SALE_DEED/manoj kumar & Monu kumari MW +EAST PART OF BALAJI NAGAR+SO PATTA+3REC+SD.docx"
KEY = os.getenv("GEMINI_API_KEY_3")

def main():
    doc = Document(TEST_DOC_PATH)
    chunks = []
    for part_name, part in DocManipulator.iter_story_parts(doc):
        for p in DocManipulator.iter_paragraphs_deep(part):
            if p.text.strip():
                chunks.append(p.text.strip())
    content = "\n".join(chunks)
    prompt = get_discovery_prompt(content, "SD")
    
    print(f"Prompt length: {len(prompt)}")
    print("Initializing client...")
    client = genai.Client(api_key=KEY)
    
    print("Calling generate_content with gemini-2.5-flash...")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        print("SUCCESS!")
        print(f"Response length: {len(response.text)}")
        print(response.text[:200])
    except Exception as e:
        print(f"FAILED: {type(e)} - {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
