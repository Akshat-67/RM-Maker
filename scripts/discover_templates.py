# scripts/discover_templates.py
import os
import sys
import json
import glob
from docx import Document
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Reconfigure stdout and stderr to handle UTF-8 and avoid Windows terminal encoding crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')

# Add project root to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from utils.config import DEFAULT_GEMINI_API_KEYS
    from modules.sd.chain_templates import CHAIN_TEMPLATES, CHAIN_TEMPLATE_METADATA
except ImportError:
    print("Error: Could not import project modules. Ensure you run the script from the project root.")
    sys.exit(1)

# Load all configured API keys
API_KEYS = DEFAULT_GEMINI_API_KEYS if DEFAULT_GEMINI_API_KEYS else []
if not API_KEYS and os.getenv("GEMINI_API_KEY"):
    API_KEYS = [os.getenv("GEMINI_API_KEY")]

if not API_KEYS:
    print("Error: No Gemini API key found. Please set GEMINI_API_KEY in your .env file.")
    sys.exit(1)

# Keep track of current key index
current_key_idx = 0
client = genai.Client(api_key=API_KEYS[current_key_idx])

def rotate_api_key():
    """Rotate to the next available Gemini API key in the list."""
    global current_key_idx, client
    if len(API_KEYS) <= 1:
        return False
    current_key_idx = (current_key_idx + 1) % len(API_KEYS)
    print(f"  [Key Rotation] Rotating to API Key #{current_key_idx + 1}...")
    client = genai.Client(api_key=API_KEYS[current_key_idx])
    return True

# Relevant keywords to identify prior title chain paragraphs in full deeds (handles both Unicode and legacy DevLys/Kruti Dev)
CHAIN_KEYWORDS = [
    # Standard Unicode & English Keywords
    "पट्टा", "आवंटन", "विक्रय", "बेचान", "रजिस्ट्री", "स्वर्गवास", "देहान्त", "मृत्यु", 
    "उत्तराधिकार", "उत्तराधिकारी", "हकत्याग", "मुख्तियारनामा", "बख्शीश", "दानपत्र", "वसीयत",
    "बंटवारा", "लीज", "lease", "allotment", "deed", "will", "poa",
    # Legacy DevLys / Kruti Dev Keywords (ASCII equivalent representations)
    "rRi’pkr~", "rRi'pkr~", ";g fd", "lEifRr", "lEifÙk", "lEifÙ", "fodz;", "vkoaVu", 
    "iêk", "jftLVªh", "jftLVh", "dk;kZy;", "LoXkZokl", "gDR;kx", "eqgfr;kjukek", 
    "eqf[r;kjukek", "olh;rukek", "gLrkUrj.k", "gLrkUrj"
]

def is_candidate_paragraph(text):
    """Filter paragraphs that are likely to contain historical title chain events."""
    t = text.strip().lower()
    if len(t) < 40 or len(t) > 1500:
        return False
    # Must contain at least one key term
    return any(kw in t for kw in CHAIN_KEYWORDS)

def extract_text_from_file(filepath):
    """Extract candidate paragraphs from .docx or .txt files."""
    ext = os.path.splitext(filepath)[1].lower()
    paragraphs = []
    
    if ext == ".docx":
        try:
            doc = Document(filepath)
            for p in doc.paragraphs:
                txt = p.text.strip()
                if is_candidate_paragraph(txt):
                    paragraphs.append(txt)
            # Also check tables in the doc (some chains are stored in tables)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        txt = cell.text.strip()
                        if is_candidate_paragraph(txt) and txt not in paragraphs:
                            paragraphs.append(txt)
        except Exception as e:
            print(f"  Error reading Word file {os.path.basename(filepath)}: {e}")
    elif ext == ".txt":
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                # If separated by double newlines, split. Otherwise, check lines
                parts = content.split("\n\n") if "\n\n" in content else content.split("\n")
                for part in parts:
                    txt = part.strip()
                    if len(txt) > 20:
                        paragraphs.append(txt)
        except Exception as e:
            print(f"  Error reading text file {os.path.basename(filepath)}: {e}")
            
    return paragraphs

def analyze_and_parameterize(paragraph):
    """Call Gemini to convert raw legal text into a parameterized template and metadata."""
    global client
    
    prompt = f"""
    You are an expert Indian property lawyer. Analyze the following real-world Hindi title chain paragraph:
    "{paragraph}"
    
    Tasks:
    1. Identify the core legal event type. It MUST be one of these exact enums:
       [ALLOTMENT, SALE_DEED, GIFT_DEED, HAK_TYAG, POA, DEATH, CONSTRUCTION, TRANSFER, WILL]
       
    2. Convert the paragraph into a reusable template string by replacing specific names, dates, amounts, registration details, project names, and share fractions with the following exact placeholders:
       - {{prefix}}          -> Use at the very beginning of the paragraph.
       - {{executant}}       -> The party transferring the right/owner/deceased.
       - {{claimant}}        -> The party receiving the right/buyer/heir.
       - {{date}}            -> The execution date of the document.
       - {{reg_details}}     -> The entire registration details phrase. Place this placeholder precisely where registry book/volume/page/number details are written in the sentence.
       - {{amount}}          -> The consideration amount.
       - {{share_fraction}}  -> Any undivided share fraction (e.g. आधा, 1/2, 1/3, तिहाई).
       - {{project_name}}    -> The name of the residential project/apartment (for construction).
       - {{document_name}}   -> The exact name of the deed (e.g., पट्टा विलेख, विक्रय पत्र, हकत्याग पत्र).
       
       *IMPORTANT*: Keep all other legal phrasing, grammar, punctuations, and Hindi sentence structures EXACTLY intact. Do not simplify or summarize the legalese.
       
    3. Generate a descriptive, unique uppercase template key (e.g., ALLOTMENT_SOCIETY_RECEIPT, DEATH_MULTIPLE_HEIRS_NO_SPOUSE).
    
    4. Write a clean 1-sentence English description of the specific legal scenario this template represents.
    
    5. Write a user-friendly label (in English/Hindi, e.g. "Allotment via Society (समिति आवंटन)").
    
    Return your response strictly as a single JSON object with these keys:
    {{
        "event_type": "...",
        "template_key": "...",
        "label": "...",
        "template": "...",
        "description": "..."
    }}
    """
    
    max_retries = len(API_KEYS)
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.1
                }
            )
            return json.loads(response.text.strip())
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                # If we have more keys and haven't exhausted our retries
                if len(API_KEYS) > 1 and attempt < max_retries - 1:
                    rotate_api_key()
                    continue
                else:
                    print(f"  Gemini API error (All API keys exhausted): {e}")
                    return None
            else:
                print(f"  Gemini API error: {e}")
                return None
    return None

def run_discovery():
    raw_dir = os.path.join("Reference Materials", "raw_deeds")
    files = glob.glob(os.path.join(raw_dir, "*.docx")) + glob.glob(os.path.join(raw_dir, "*.txt"))
    
    if not files:
        print(f"No files found in '{raw_dir}'. Please drop some .docx or .txt files there first.")
        return
        
    print(f"=== Starting Title Chain Template Discovery ===")
    print(f"Found {len(files)} file(s) to scan.")
    
    candidate_paras = []
    for filepath in files:
        print(f"Scanning {os.path.basename(filepath)}...")
        paras = extract_text_from_file(filepath)
        print(f"  Found {len(paras)} prior ownership candidate paragraph(s).")
        for p in paras:
            if p not in candidate_paras:
                candidate_paras.append(p)
                
    if not candidate_paras:
        print("No candidate prior chain paragraphs could be isolated. Check your files' contents.")
        return
        
    print(f"\nTotal unique candidate paragraphs to analyze: {len(candidate_paras)}")
    print("Analyzing with Gemini to extract reusable templates...")
    
    new_templates = {}
    new_metadata = {}
    matched_count = 0
    new_count = 0
    
    # Load existing custom templates if they exist
    custom_json_path = os.path.join("modules", "sd", "custom_chain_templates.json")
    custom_data = {"templates": {}, "metadata": {}}
    if os.path.exists(custom_json_path):
        try:
            with open(custom_json_path, "r", encoding="utf-8") as f:
                custom_data = json.load(f)
        except Exception:
            pass
            
    for idx, para in enumerate(candidate_paras):
        print(f"[{idx+1}/{len(candidate_paras)}] Processing snippet: {para[:60]}...")
        result = analyze_and_parameterize(para)
        if not result:
            continue
            
        tpl_key = result.get("template_key")
        template_str = result.get("template")
        event_type = result.get("event_type")
        description = result.get("description")
        label = result.get("label")
        
        if not tpl_key or not template_str or not event_type:
            print("  Skipping: Invalid JSON structure returned from AI.")
            continue
            
        # De-duplicate: Check if it matches any system default template
        is_duplicate = False
        for sys_key, sys_tpl in CHAIN_TEMPLATES.items():
            # Check if strings are extremely similar (ignoring spaces and placeholders)
            clean_sys = "".join(c for c in sys_tpl if c.isalnum())
            clean_new = "".join(c for c in template_str if c.isalnum())
            if clean_sys == clean_new or sys_key == tpl_key:
                print(f"  -> Matches existing system template: {sys_key}")
                matched_count += 1
                is_duplicate = True
                break
                
        if is_duplicate:
            continue
            
        # Add to custom templates
        new_templates[tpl_key] = template_str
        new_metadata[tpl_key] = {
            "label": label,
            "description": description,
            "event_type": event_type
        }
        print(f"  -> Discovered NEW Variation: {tpl_key}")
        print(f"     Label: {label}")
        print(f"     Description: {description}")
        new_count += 1
        
    if new_count > 0:
        # Merge with existing custom templates
        custom_data["templates"].update(new_templates)
        custom_data["metadata"].update(new_metadata)
        
        # Save custom templates back to JSON
        try:
            with open(custom_json_path, "w", encoding="utf-8") as f:
                json.dump(custom_data, f, indent=4, ensure_ascii=False)
            print(f"\nSuccessfully wrote {new_count} new template(s) to '{custom_json_path}'.")
            print("They are now instantly active in the visual card editor and backend compiler!")
        except Exception as e:
            print(f"\nError writing custom templates JSON: {e}")
    else:
        print("\nNo new variations were discovered. All scanned snippets matched existing templates.")
        
    print(f"\n=== Discovery Complete ===")
    print(f"Scanned files: {len(files)}")
    print(f"Scanned snippets: {len(candidate_paras)}")
    print(f"Matched to system defaults: {matched_count}")
    print(f"New variations ingested: {new_count}")

if __name__ == "__main__":
    run_discovery()
