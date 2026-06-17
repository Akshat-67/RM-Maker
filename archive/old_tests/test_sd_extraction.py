import os
import json
import sys
from modules.sd.extractor import SDDataExtractor as DataExtractor

# Setup API Keys from environment
API_KEYS = [os.getenv("GEMINI_API_KEY")]
if not any(API_KEYS):
    print("ERROR: GEMINI_API_KEY not found in environment.")
    sys.exit(1)

def test_sd_extraction():
    extractor = DataExtractor(api_keys=API_KEYS)
    
    # Path to sample SD documents (as identified in Phase 1)
    # Using the first available sample for the POC
    sample_files = ["templates/SALE_DEED/SD_JDA_2SD_Flat_2S_1B.docx"]
    
    print(f"--- Running Test SD Extraction: {sample_files[0]} ---")
    
    try:
        extracted_data = extractor.extract_with_ai(
            file_paths=sample_files,
            selected_model="gemini-1.5-flash",
            doc_type="SD",
            expected_sellers=2,
            expected_buyers=1,
            current_data={}
        )
        
        if "error" in extracted_data:
            print(f"AI ERROR: {extracted_data['error']}")
            return

        print("\n--- EXTRACTED JSON (PHASE 2B VALIDATION) ---")
        print(json.dumps(extracted_data, indent=2, ensure_ascii=False))
        
        # Schema Validation Check
        required_keys = ["doc_type", "rd", "ss", "bs", "ps", "title_chain"]
        missing = [k for k in required_keys if k not in extracted_data]
        if missing:
            print(f"\nVALIDATION FAILED: Missing keys {missing}")
        else:
            print("\nVALIDATION SUCCESS: Schema shape is correct.")
            
    except Exception as e:
        print(f"TEST FAILED: {str(e)}")

if __name__ == "__main__":
    test_sd_extraction()
