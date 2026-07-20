import os
import json
import time
import re
import threading
import requests
import numpy as np
import cv2
from PIL import Image
import pypdf

from utils.config import NVIDIA_OCR_API_KEY, CASE_INBOX_DIR
from services.session_manager import load_case_session, save_case_session, CASES_DIR
from utils.helpers import prepare_image_for_nim

# Initialize a logger
import logging
logger = logging.getLogger("IngestionPipeline")
logger.setLevel(logging.INFO)

def start_inbox_ingestion_thread(case_id):
    """Spawn a background thread to process a newly imported inbox case."""
    thread = threading.Thread(target=run_ingestion_pipeline, args=(case_id,))
    thread.daemon = True
    thread.start()
    logger.info(f"Spawned ingestion pipeline background thread for case: {case_id}")


def start_incremental_ingestion_thread(case_id, new_files):
    """Spawn a background thread to process only newly-added files for an existing case."""
    thread = threading.Thread(target=run_incremental_ingestion, args=(case_id, new_files))
    thread.daemon = True
    thread.start()
    logger.info(f"Spawned incremental ingestion thread for case: {case_id} ({len(new_files)} new file(s))")


def run_incremental_ingestion(case_id, new_files):
    """
    Incrementally ingests new files dropped into an already-processed -EX folder.

    Steps:
    1. Classify each new file into the correct bucket.
    2. Append new files to the session's file list and bucket lists.
    3. Run AI extraction on ONLY the new files.
    4. Smart-merge the new extraction into the existing session data.
    5. Mark all new files as processed so the watcher won't re-trigger them.
    """
    session = load_case_session(case_id)
    if not session:
        logger.error(f"Incremental ingestion: session not found for case {case_id}")
        return

    # Guard: don't run if another pipeline is already active
    if session.get("status") in ("processing", "extracting"):
        logger.info(f"Incremental ingestion skipped for {case_id} — pipeline already running")
        return

    logger.info(f"Starting incremental ingestion for {case_id}: {[os.path.basename(f) for f in new_files]}")

    case_inbox_path = session.get("case_inbox_path", "")

    # --- Step 1: Classify new files into buckets ---
    new_buckets = {"kyc": [], "legal": [], "ats": [], "title_chain": [], "ocr": []}
    for filepath in new_files:
        filename = os.path.basename(filepath)
        base_name, _ = os.path.splitext(filename)
        base_name_lower = base_name.lower().strip()

        rel_dir = ""
        if case_inbox_path:
            rel_dir = os.path.dirname(
                os.path.relpath(filepath, case_inbox_path)
            ).replace("\\", "/").lower()

        if "kyc" in rel_dir or "aadhar" in rel_dir or "pan" in rel_dir:
            new_buckets["kyc"].append(filepath)
        elif "legal" in rel_dir or "scrutiny" in rel_dir:
            new_buckets["legal"].append(filepath)
        elif "ats" in rel_dir or "sanction" in rel_dir:
            new_buckets["ats"].append(filepath)
        elif "title_chain" in rel_dir or "chain" in rel_dir:
            new_buckets["title_chain"].append(filepath)
        elif "ocr" in rel_dir or "tech" in rel_dir or "visit" in rel_dir or "valuation" in rel_dir:
            new_buckets["ocr"].append(filepath)
        elif re.match(r'^[\d,\-\s\(\)]+$', base_name_lower) or "aadhar" in base_name_lower or "pan" in base_name_lower:
            new_buckets["kyc"].append(filepath)
        elif base_name_lower in ("legal", "l") or "legal" in base_name_lower or "scrutiny" in base_name_lower:
            new_buckets["legal"].append(filepath)
        elif base_name_lower in ("sanction", "s") or re.match(r'^s\d+$', base_name_lower) or "sanction" in base_name_lower or "ats" in base_name_lower:
            new_buckets["ats"].append(filepath)
        elif base_name_lower in ("tech", "t") or "technical" in base_name_lower or "visit" in base_name_lower or "valuation" in base_name_lower:
            new_buckets["ocr"].append(filepath)
        else:
            # Unrecognised — add to KYC as a safe fallback so it still gets sent to the AI
            new_buckets["kyc"].append(filepath)

    # --- Step 2: Merge new files into the session's existing lists ---
    existing_files = session.get("files", [])
    existing_buckets = session.get("buckets", {b: [] for b in new_buckets})
    for bucket, files in new_buckets.items():
        for f in files:
            if f not in existing_files:
                existing_files.append(f)
            if f not in existing_buckets.get(bucket, []):
                existing_buckets.setdefault(bucket, []).append(f)

    session["files"] = existing_files
    session["buckets"] = existing_buckets
    session["status"] = "extracting"

    save_case_session(
        case_id=case_id,
        data=session.get("data", {}),
        files=existing_files,
        verified_fields=set(session.get("verified_fields", [])),
        bank=session.get("bank", "ICICI"),
        borrower_count=session.get("borrower_count", "1"),
        loan_count=session.get("loan_count", "1"),
        doc_type=session.get("doc_type", "RM"),
        status="extracting",
        buckets=existing_buckets,
    )

    # --- Step 3: Run AI extraction on only the new files ---
    try:
        doc_type = session.get("doc_type", "RM")
        current_data = session.get("data", {})
        verified_fields = set(session.get("verified_fields", []))

        from utils.config import DEFAULT_GEMINI_API_KEYS
        from services.file_service import smart_merge

        model = "gemini-2.5-flash"

        if doc_type == "SD":
            from modules.sd.extractor import SDDataExtractor
            extractor = SDDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS)
            extracted_data = extractor.extract_with_ai(
                new_files, model,
                expected_sellers=int(session.get("sellers_count", 1)),
                expected_buyers=int(session.get("buyers_count", 1)),
                expected_witnesses=2,
                seller_hints="", buyer_hints="", witness_hints="",
                current_data=current_data
            )
        else:
            from modules.rm.extractor import RMDataExtractor
            extractor = RMDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS)
            extracted_data = extractor.extract_buckets_with_ai(
                new_buckets, model,
                bank_name=session.get("bank", "ICICI"),
                expected_borrowers=int(session.get("borrower_count", 1)),
                expected_loans=int(session.get("loan_count", 1)),
                borrower_hints="", witness_hints="",
                current_data=current_data
            )

        if extracted_data.get("error"):
            raise RuntimeError(extracted_data["error"])

        # --- Step 4: Smart-merge new extraction into existing data ---
        merged_data = smart_merge(current_data, extracted_data, verified_fields)

        # Update extractions and confidence metadata
        session_extractions = session.get("extractions", {})
        session_extractions.update(extracted_data.get("extractions", {}))
        session_confidence = session.get("confidence_scores", {})
        session_confidence.update(extracted_data.get("confidence_scores", {}))

        # Normalise Hindi digits
        from utils.helpers import convert_hindi_digits_to_english
        merged_data = convert_hindi_digits_to_english(merged_data)

        # --- Step 5: Mark new files as processed ---
        processed_files = session.get("processed_files", [])
        for f in new_files:
            if f not in processed_files:
                processed_files.append(f)

        save_case_session(
            case_id=case_id,
            data=merged_data,
            files=existing_files,
            verified_fields=verified_fields,
            bank=session.get("bank", "ICICI"),
            borrower_count=session.get("borrower_count", "1"),
            loan_count=session.get("loan_count", "1"),
            doc_type=doc_type,
            status="ready",
            buckets=existing_buckets,
            extractions=session_extractions,
            confidence_scores=session_confidence,
            processed_files=processed_files,
        )
        logger.info(f"Incremental ingestion complete for {case_id}: merged {len(new_files)} new file(s)")

    except Exception as e:
        logger.error(f"Incremental ingestion failed for {case_id}: {e}", exc_info=True)
        session = load_case_session(case_id) or {}
        save_case_session(
            case_id=case_id,
            data=session.get("data", {}),
            files=session.get("files", []),
            verified_fields=set(session.get("verified_fields", [])),
            bank=session.get("bank", "ICICI"),
            borrower_count=session.get("borrower_count", "1"),
            loan_count=session.get("loan_count", "1"),
            doc_type=session.get("doc_type", "RM"),
            status="ready",  # go back to ready so the user can still work
        )



def run_ingestion_pipeline(case_id):
    """Main ingestion worker pipeline."""
    session = load_case_session(case_id)
    if not session:
        logger.error(f"Failed to load session for case: {case_id}")
        return

    # Set status to processing
    session["status"] = "processing"
    save_case_session(case_id, session.get("data", {}), session.get("files", []), 
                      set(session.get("verified_fields", [])), session.get("bank", ""),
                      session.get("borrower_count", "1"), session.get("loan_count", "1"),
                      doc_type=session.get("doc_type", "RM"))

    try:
        case_inbox_path = session.get("case_inbox_path")
        if not case_inbox_path or not os.path.exists(case_inbox_path):
            logger.error(f"Monitored folder path does not exist for case: {case_id}")
            session["status"] = "failed"
            session["error"] = "Monitored folder path not found."
            save_case_session(case_id, session.get("data", {}), session.get("files", []), 
                              set(session.get("verified_fields", [])), session.get("bank", ""),
                              session.get("borrower_count", "1"), session.get("loan_count", "1"),
                              doc_type=session.get("doc_type", "RM"))
            return

        # Scan folder for all raw files
        allowed_ext = {'.pdf', '.docx', '.png', '.jpg', '.jpeg', '.txt'}
        raw_files = []
        for root, _, files in os.walk(case_inbox_path):
            for file in files:
                _, ext = os.path.splitext(file.lower())
                if ext in allowed_ext and not file.startswith("~$") and file != "session.json":
                    raw_files.append(os.path.join(root, file))

        # Classify files into buckets for the case
        buckets = {
            "kyc": [],
            "legal": [],
            "ats": [],
            "title_chain": [],
            "ocr": []
        }
        for filepath in raw_files:
            filename = os.path.basename(filepath)
            base_name, _ = os.path.splitext(filename)
            base_name_lower = base_name.lower().strip()
            
            # Get relative directory path (excluding filename)
            rel_dir = os.path.dirname(os.path.relpath(filepath, case_inbox_path)).replace("\\", "/").lower()
            
            # Check relative directory names first to classify based on folder structure
            if "kyc" in rel_dir or "aadhar" in rel_dir or "pan" in rel_dir:
                buckets["kyc"].append(filepath)
            elif "legal" in rel_dir or "scrutiny" in rel_dir:
                buckets["legal"].append(filepath)
            elif "ats" in rel_dir or "sanction" in rel_dir:
                buckets["ats"].append(filepath)
            elif "title_chain" in rel_dir or "chain" in rel_dir:
                buckets["title_chain"].append(filepath)
            elif "ocr" in rel_dir or "tech" in rel_dir or "visit" in rel_dir or "valuation" in rel_dir:
                buckets["ocr"].append(filepath)
            # Fallback to filename-based matching
            elif re.match(r'^[\d,\-\s\(\)]+$', base_name_lower) or "aadhar" in base_name_lower or "pan" in base_name_lower:
                buckets["kyc"].append(filepath)
            elif base_name_lower in ("legal", "l") or "legal" in base_name_lower or "scrutiny" in base_name_lower:
                buckets["legal"].append(filepath)
            elif base_name_lower in ("sanction", "s") or re.match(r'^s\d+$', base_name_lower) or "sanction" in base_name_lower or "ats" in base_name_lower:
                buckets["ats"].append(filepath)
            elif base_name_lower in ("tech", "t") or "technical" in base_name_lower or "visit" in base_name_lower or "valuation" in base_name_lower:
                buckets["ocr"].append(filepath)

        # Update case session file list and buckets to point to classified files
        session["files"] = raw_files
        session["buckets"] = buckets
        save_case_session(case_id, session.get("data", {}), session["files"], 
                          set(session.get("verified_fields", [])), session.get("bank", ""),
                          session.get("borrower_count", "1"), session.get("loan_count", "1"),
                          doc_type=session.get("doc_type", "RM"),
                          buckets=buckets)

        # Files are accepted as-is; no automatic rotation or cropping is applied.

        # Save the updated files list (retaining original filenames) and mark as ready
        session = load_case_session(case_id) or session
        session["files"] = raw_files
        session["buckets"] = buckets
        session["status"] = "ready"
        
        save_case_session(case_id, session.get("data", {}), session["files"], 
                          set(session.get("verified_fields", [])), session.get("bank", ""),
                          session.get("borrower_count", "1"), session.get("loan_count", "1"),
                          doc_type=session.get("doc_type", "RM"),
                          status="ready",
                          buckets=buckets)
        
        if session.get("is_auto_extraction"):
            run_auto_ai_extraction(case_id)
        else:
            logger.info(f"Ingestion pipeline completed successfully for case: {case_id}")


    except Exception as e:
        logger.error(f"Error running ingestion pipeline: {e}")
        session["status"] = "failed"
        session["error"] = str(e)
        save_case_session(case_id, session.get("data", {}), session.get("files", []), 
                          set(session.get("verified_fields", [])), session.get("bank", ""),
                          session.get("borrower_count", "1"), session.get("loan_count", "1"),
                          doc_type=session.get("doc_type", "RM"))



def classify_file_type(filepath):
    """Classifies file type using text matching (local for PDFs, Nemotron OCR for images)."""
    _, ext = os.path.splitext(filepath.lower())
    
    # 1. Check filename keywords first (instant)
    base = os.path.basename(filepath).lower()
    if "pan" in base: return "PAN"
    if "aadhar" in base:
        if "back" in base: return "Aadhaar_Back"
        return "Aadhaar_Front"
    if "sanction" in base: return "Sanction_Letter"
    if "legal" in base or "scrutiny" in base: return "Legal_Report"
    if "technical" in base or "visit" in base: return "Technical_Report"
    
    # 2. PDF Local text search
    if ext == '.pdf':
        try:
            reader = pypdf.PdfReader(filepath)
            first_page_text = ""
            if len(reader.pages) > 0:
                first_page_text = reader.pages[0].extract_text() or ""
            
            text_lower = first_page_text.lower()
            if "sanction" in text_lower or "loan amount" in text_lower or "tenure" in text_lower:
                return "Sanction_Letter"
            if "scrutiny" in text_lower or "search report" in text_lower or "title search" in text_lower or "legal scrutiny" in text_lower:
                return "Legal_Report"
            if "visit details" in text_lower or "technical report" in text_lower or "nearby landmark" in text_lower:
                return "Technical_Report"
        except Exception as e:
            logger.error(f"Failed to extract PDF text for classification: {e}")
            
    # 3. Image OCR Classification
    elif ext in ['.jpg', '.jpeg', '.png'] and NVIDIA_OCR_API_KEY:
        try:
            with open(filepath, "rb") as f:
                img_bytes = f.read()
            
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
            res = requests.post(invoke_url, headers=headers, json=payload, timeout=20)
            res_json = res.json()
            
            ocr_text = ""
            if isinstance(res_json, dict):
                if "data" in res_json and isinstance(res_json["data"], list) and len(res_json["data"]) > 0:
                    detections = res_json["data"][0].get("text_detections", [])
                    texts = []
                    for det in detections:
                        if isinstance(det, dict) and "text_prediction" in det:
                            texts.append(det["text_prediction"].get("text", ""))
                    ocr_text = "\n".join(texts)
                elif "predictions" in res_json:
                    preds = res_json["predictions"]
                    if preds and isinstance(preds, list):
                        texts = []
                        for pred in preds:
                            if isinstance(pred, dict) and "text_prediction" in pred:
                                texts.append(pred["text_prediction"].get("text", ""))
                            elif isinstance(pred, dict) and "text" in pred:
                                texts.append(pred.get("text", ""))
                        ocr_text = "\n".join(texts)
            
            text_lower = ocr_text.lower()
            
            # Check Aadhaar Front/Back
            if any(k in text_lower for k in ["government of india", "unique identification", "enrollment", "dob:", "yob:"]):
                if any(k in text_lower for k in ["address", "पता", "c/o", "s/o", "w/o", "d/o"]):
                    return "Aadhaar_Back"
                return "Aadhaar_Front"
                
            # Check PAN
            if any(k in text_lower for k in ["permanent account number", "income tax", "signature of card holder", "father's name"]):
                return "PAN"
                
        except Exception as e:
            logger.error(f"Failed to classify image OCR: {e}")
            
    return None


def run_auto_ai_extraction(case_id):
    """Executes the automatic AI extraction pipeline for a watcher-imported case."""
    try:
        session = load_case_session(case_id)
        if not session:
            logger.error(f"Failed to load session for auto-extraction: {case_id}")
            return

        # Set status to extracting
        session["status"] = "extracting"
        save_case_session(case_id, session.get("data", {}), session.get("files", []), 
                          set(session.get("verified_fields", [])), session.get("bank", "ICICI"),
                          session.get("borrower_count", "1"), session.get("loan_count", "1"),
                          doc_type=session.get("doc_type", "RM"),
                          status="extracting")

        doc_type = session.get("doc_type", "RM")
        buckets = session.get("buckets", {})
        
        # Collect all files from buckets
        files_to_process = []
        for b_files in buckets.values():
            files_to_process.extend(b_files)

        if not files_to_process:
            logger.warning(f"No classified files to process for auto-extraction case {case_id}")
            session["status"] = "ready"
            save_case_session(case_id, session.get("data", {}), session.get("files", []), 
                              set(session.get("verified_fields", [])), session.get("bank", "ICICI"),
                              session.get("borrower_count", "1"), session.get("loan_count", "1"),
                              doc_type=doc_type,
                              status="ready")
            return

        from utils.config import DEFAULT_GEMINI_API_KEYS
        from services.file_service import smart_merge

        current_data = session.get("data", {})
        verified_fields = set(session.get("verified_fields", []))

        # Model defaults to gemini-2.5-flash
        model = "gemini-2.5-flash"

        if doc_type == "SD":
            # For SD, run SDDataExtractor
            from modules.sd.extractor import SDDataExtractor
            extractor = SDDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS)
            extracted_data = extractor.extract_with_ai(
                files_to_process, model,
                expected_sellers=1, expected_buyers=1,
                expected_witnesses=2, seller_hints="", buyer_hints="",
                witness_hints="", current_data=current_data
            )
        else:
            # For RM, run RMDataExtractor
            from modules.rm.extractor import RMDataExtractor
            extractor = RMDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS)
            extracted_data = extractor.extract_buckets_with_ai(
                buckets, model, bank_name="ICICI",
                expected_borrowers=1, expected_loans=1,
                borrower_hints="", witness_hints="",
                current_data=current_data
            )

        if extracted_data.get("error"):
            logger.error(f"Auto-extraction API error: {extracted_data['error']}")
            session["status"] = "failed"
            session["error"] = extracted_data["error"]
            save_case_session(case_id, session.get("data", {}), session.get("files", []), 
                              set(session.get("verified_fields", [])), session.get("bank", "ICICI"),
                              session.get("borrower_count", "1"), session.get("loan_count", "1"),
                              doc_type=doc_type,
                              status="failed")
            return

        # Update extraction metadata
        session_extractions = session.get("extractions", {})
        if "extractions" in extracted_data:
            session_extractions.update(extracted_data["extractions"])
        session["extractions"] = session_extractions

        session_confidence = session.get("confidence_scores", {})
        if "confidence_scores" in extracted_data:
            session_confidence.update(extracted_data["confidence_scores"])
        session["confidence_scores"] = session_confidence

        merged_data = smart_merge(current_data, extracted_data, verified_fields)
        session["data"] = merged_data

        # Determine property type
        ps_list = session["data"].get("ps", [{}])
        property_type = session.get("property_type", "Plot")
        if ps_list and isinstance(ps_list[0], dict):
            p0 = ps_list[0]
            if p0.get("flat_no") or p0.get("building_name") or p0.get("floor") or "flat" in str(p0.get("plot_no", "")).lower():
                property_type = "Flat"
        session["property_type"] = property_type
        session["data"]["property_type"] = property_type

        # 1. Map Extracted Bank to existing template directories dynamically
        from services.file_service import discover_templates
        _, _, bank_folders = discover_templates()
        extracted_bank = str(extracted_data.get("bank", "ICICI")).upper().strip()
        logger.info(f"AI extracted bank name: '{extracted_bank}'. Discovered bank folders: {bank_folders}")
        
        mapped_bank = "ICICI"
        for folder in bank_folders:
            # Match folder (e.g. 'HFFC') against extracted name (e.g. 'HOME FIRST FINANCE COMPANY (HFFC)')
            # or vice-versa
            cleaned_folder = folder.replace("_", "").replace(" ", "").upper()
            cleaned_extracted = extracted_bank.replace("_", "").replace(" ", "").upper()
            if cleaned_folder in cleaned_extracted or cleaned_extracted in cleaned_folder:
                mapped_bank = folder
                break
        else:
            mapped_bank = "ICICI"

        # 2. Extract borrower, loan, and property counts
        borrower_count = int(extracted_data.get("borrower_count", 1))
        loan_count = int(extracted_data.get("loan_count", 1))
        properties_count = int(extracted_data.get("properties_count", 1))
        
        # Enforce limits/sane bounds
        borrower_count = max(1, min(10, borrower_count))
        loan_count = max(1, min(10, loan_count))
        properties_count = max(1, min(10, properties_count))

        logger.info(f"AI extracted counts - Borrowers: {borrower_count}, Loans: {loan_count}, Properties: {properties_count}")

        # 3. Resize and pad entities arrays in data to match the extracted counts
        if "bs" not in merged_data or not isinstance(merged_data["bs"], list):
            merged_data["bs"] = []
        merged_data["bs"] = merged_data["bs"][:borrower_count]
        while len(merged_data["bs"]) < borrower_count:
            merged_data["bs"].append({})

        if "ls" not in merged_data or not isinstance(merged_data["ls"], list):
            merged_data["ls"] = []
        merged_data["ls"] = merged_data["ls"][:loan_count]
        while len(merged_data["ls"]) < loan_count:
            merged_data["ls"].append({})

        if "ps" not in merged_data or not isinstance(merged_data["ps"], list):
            merged_data["ps"] = []
        merged_data["ps"] = merged_data["ps"][:properties_count]
        while len(merged_data["ps"]) < properties_count:
            merged_data["ps"].append({})

        # Normalize Hindi digits to English inside merged_data
        from utils.helpers import convert_hindi_digits_to_english
        merged_data = convert_hindi_digits_to_english(merged_data)

        # Mark processed files
        processed_files = session.get("processed_files", [])
        for f in files_to_process:
            if f not in processed_files:
                processed_files.append(f)
        session["processed_files"] = processed_files

        # Save session
        save_case_session(
            case_id=case_id,
            data=merged_data,
            files=session["files"],
            verified_fields=verified_fields,
            bank=mapped_bank,
            borrower_count=str(borrower_count),
            loan_count=str(loan_count),
            properties_count=str(properties_count),
            processed_files=session["processed_files"],
            doc_type=doc_type,
            status="ready",
            extractions=session["extractions"],
            confidence_scores=session["confidence_scores"],
            buckets=buckets,
            property_type=property_type
        )
        logger.info(f"Auto-extraction AI workflow completed successfully for case: {case_id}")

    except Exception as e:
        logger.error(f"Error in run_auto_ai_extraction: {e}", exc_info=True)
        session = load_case_session(case_id)
        if session:
            session["status"] = "failed"
            session["error"] = str(e)
            save_case_session(case_id, session.get("data", {}), session.get("files", []), 
                              set(session.get("verified_fields", [])), session.get("bank", "ICICI"),
                              session.get("borrower_count", "1"), session.get("loan_count", "1"),
                              doc_type=session.get("doc_type", "RM"),
                              status="failed")

