import os
import requests
import logging
from typing import List, Dict, Any
from .base import BaseValidator
from .models import Discrepancy
from utils.config import NVIDIA_OCR_API_KEY
from services.session_manager import CASES_DIR
from utils.helpers import prepare_image_for_nim


logger = logging.getLogger("NameMatchValidator")

class NameMatchValidator(BaseValidator):
    def supports(self, doc_type: str) -> bool:
        return doc_type == "RM"
        
    def validate(self, case_data: Dict[str, Any]) -> List[Discrepancy]:
        findings = []
        case_id = case_data.get("id")
        if not case_id:
            return findings
            
        case_dir = os.path.join(CASES_DIR, case_id)
        if not os.path.exists(case_dir):
            return findings
            
        # We search for images in 'buckets/kyc' and 'files'
        kyc_dir = os.path.join(case_dir, "buckets", "kyc")
        files_dir = os.path.join(case_dir, "files")
        ocr_cache_dir = os.path.join(case_dir, "buckets", "ocr")
        os.makedirs(ocr_cache_dir, exist_ok=True)
        
        image_files = []
        for directory in [kyc_dir, files_dir]:
            if os.path.exists(directory):
                for f in os.listdir(directory):
                    if f.lower().endswith((".png", ".jpg", ".jpeg")):
                        image_files.append(os.path.join(directory, f))
                        
        if not image_files:
            return findings
            
        # Build OCR corpus
        corpus_texts = []
        for img_path in image_files:
            filename = os.path.basename(img_path)
            cache_path = os.path.join(ocr_cache_dir, f"{filename}.txt")
            
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        corpus_texts.append(f.read())
                    continue
                except Exception:
                    pass
                    
            # Perform Nemotron OCR v2
            if not NVIDIA_OCR_API_KEY:
                logger.warning("NVIDIA OCR API key missing, skipping Nemotron OCR.")
                continue
                
            try:
                with open(img_path, "rb") as f:
                    img_bytes = f.read()
                
                # Compress/downscale to fit limits
                b64_str = prepare_image_for_nim(img_bytes)
                
                invoke_url = "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v2"
                headers = {
                    "Authorization": f"Bearer {NVIDIA_OCR_API_KEY}",
                    "Accept": "application/json"
                }
                payload = {
                    "input": [
                        {
                            "type": "image_url",
                            "url": b64_str
                        }
                    ]
                }
                
                response = requests.post(invoke_url, headers=headers, json=payload, timeout=30)
                res_json = response.json()
                
                # Extract text from Nemotron response format
                ocr_text = ""
                if isinstance(res_json, dict) and "predictions" in res_json:
                    predictions = res_json["predictions"]
                    if predictions and isinstance(predictions, list):
                        ocr_text = predictions[0].get("text", "")
                elif isinstance(res_json, dict) and "text" in res_json:
                    ocr_text = res_json.get("text", "")
                    
                if ocr_text:
                    # Write cache
                    with open(cache_path, "w", encoding="utf-8") as f:
                        f.write(ocr_text)
                    corpus_texts.append(ocr_text)
                    
            except Exception as e:
                logger.error(f"Nemotron OCR failed for {filename}: {e}")
                
        if not corpus_texts:
            return findings
            
        full_corpus = " ".join(corpus_texts).lower()
        
        # Check borrower names
        borrowers = case_data.get("bs", [])
        for idx, b in enumerate(borrowers):
            if not isinstance(b, dict): continue
            name = str(b.get("n", "")).strip()
            if not name: continue
            
            # Simple fuzzy lookup: is the name or parts of the name present?
            # Split into individual name tokens and check
            name_parts = [p.lower() for p in name.split() if len(p) > 2 and p.lower() not in ["mr", "mrs", "ms", "shri", "smt"]]
            if not name_parts:
                continue
                
            matches = sum(1 for part in name_parts if part in full_corpus)
            match_ratio = matches / len(name_parts)
            
            if match_ratio < 0.5:
                findings.append(
                    Discrepancy(
                        category="identity",
                        severity="high",
                        explanation=f"Borrower {idx + 1} Name '{name}' could not be verified in the uploaded KYC scans.",
                        suggested_fix="Verify the name spelling against their Aadhaar card / PAN card files."
                    )
                )
                
        return findings
