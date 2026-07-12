import os
import json
import base64
import requests

CASES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cases")

def ocr_extract_text(case_id, file_paths):
    """
    Extracts text from document scans using NVIDIA NIM nemotron-ocr-v2.
    Uses Assets API fallback if base64 representation exceeds 180,000 characters.
    Caches the results locally to save API requests.
    """
    if not file_paths:
        return ""
        
    cache_dir = os.path.join(CASES_DIR, case_id)
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, "ocr_cache.json")
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f).get("text", "")
        except Exception:
            pass

    nvidia_key = os.environ.get("NVIDIA_API_KEY", "")
    if not nvidia_key:
        return "[Error: NVIDIA_API_KEY not configured]"

    headers = {
        "Authorization": f"Bearer {nvidia_key}",
        "Accept": "application/json"
    }

    full_texts = []
    for path in file_paths:
        if not os.path.exists(path):
            continue
            
        try:
            with open(path, "rb") as f:
                raw_bytes = f.read()
            b64_data = base64.b64encode(raw_bytes).decode()
            
            # NVIDIA Asset API threshold
            if len(b64_data) >= 180000:
                asset_res = requests.post(
                    "https://api.nvcf.nvidia.com/v2/nvcf/assets",
                    headers=headers,
                    json={"contentType": "image/png", "description": "Case source document page"}
                )
                if asset_res.status_code == 200:
                    asset_data = asset_res.json()
                    upload_url = asset_data["uploadUrl"]
                    asset_id = asset_data["assetId"]
                    
                    requests.put(upload_url, data=raw_bytes, headers={"Content-Type": "image/png"})
                    
                    payload = {
                        "input": [{"type": "image_url", "url": f"asset://{asset_id}"}]
                    }
                else:
                    continue
            else:
                payload = {
                    "input": [{"type": "image_url", "url": f"data:image/png;base64,{b64_data}"}]
                }

            res = requests.post(
                "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v2",
                headers=headers,
                json=payload
            )
            if res.status_code == 200:
                extracted = res.json().get("text", "")
                full_texts.append(extracted)
        except Exception as e:
            full_texts.append(f"[Error extracting from {os.path.basename(path)}: {str(e)}]")

    final_text = "\n\n".join(full_texts)
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"text": final_text}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return final_text
