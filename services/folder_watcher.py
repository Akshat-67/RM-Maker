import os
import re
import time
import datetime
import threading
import logging

import utils.config
from services.session_manager import save_case_session, CASES_DIR
from services.ingestion_pipeline import start_inbox_ingestion_thread

logger = logging.getLogger("FolderWatcher")
logger.setLevel(logging.INFO)

# A thread lock to ensure we don't start multiple scans concurrently
watcher_lock = threading.Lock()
_watcher_running = False

def start_folder_watcher():
    """Starts the background folder watcher thread if not already running."""
    global _watcher_running
    with watcher_lock:
        if _watcher_running:
            return
        _watcher_running = True
        
    thread = threading.Thread(target=_watcher_loop, daemon=True)
    thread.start()
    logger.info("Background folder watcher thread started.")

def _watcher_loop():
    """Main loop for the folder watcher."""
    while True:
        try:
            scan_inbox_directory()
        except Exception as e:
            logger.error(f"Error in scan_inbox_directory: {e}")
        time.sleep(5)

def scan_inbox_directory():
    """Scans the monitored folder for subfolders ending in '-EX' to auto-extract."""
    inbox_dir_val = os.getenv("CASE_INBOX_DIR", utils.config.CASE_INBOX_DIR)
    if not inbox_dir_val:
        return
        
    inbox_dir_val = inbox_dir_val.strip("'\"")
    inbox_path = os.path.abspath(inbox_dir_val)
    
    if not os.path.exists(inbox_path):
        return

    for d in os.listdir(inbox_path):
        sub_path = os.path.join(inbox_path, d)
        if not os.path.isdir(sub_path):
            continue
            
        # Check if the folder name ends with '-EX' (case insensitive, strip whitespaces)
        d_stripped = d.strip()
        if not d_stripped.upper().endswith("-EX"):
            continue
            
        # Clean folder name (remove -ex suffix) for case ID generation
        d_clean = re.sub(r'-ex$', '', d_stripped, flags=re.IGNORECASE).strip()
        
        # Sanitize name to form case ID
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', d_clean.lower())
        sanitized = re.sub(r'_+', '_', sanitized).strip('_')
        case_id = f"inbox_{sanitized}"
        
        case_dir = os.path.join(CASES_DIR, case_id)
        session_path = os.path.join(case_dir, "session.json")
        
        # If case session doesn't exist, create it and start ingestion
        if not os.path.exists(session_path):
            logger.info(f"Auto-watcher detected new folder '{d}', starting auto-ingestion for case_id '{case_id}'")
            
            # Determine initial doc_type
            doc_type = "SD" if "SD" in d_clean.upper() or "SALE DEED" in d_clean.upper() else "RM"
            
            today_str = datetime.date.today().strftime("%d.%m.%Y")
            
            # Save new session details
            save_case_session(
                case_id=case_id,
                data={"rd": today_str},
                files=[],
                verified_fields=set(),
                bank="ICICI",
                borrower_count="1",
                loan_count="1",
                properties_count="1",
                doc_type=doc_type,
                is_auto_extraction=True,
                case_inbox_path=sub_path,
                status="processing",
                case_name=d_clean,
                borrower_name=d_clean
            )
            
            # Trigger ingestion
            start_inbox_ingestion_thread(case_id)
        else:
            # Case already exists — check for NEW files dropped into the folder since last scan.
            from services.session_manager import load_case_session
            from services.ingestion_pipeline import start_incremental_ingestion_thread
            sess = load_case_session(case_id)
            if not sess:
                continue

            # Only poll when the case is idle (not mid-extraction or mid-processing)
            if sess.get("status") in ("processing", "extracting"):
                continue

            # Gather current files on disk
            allowed_ext = {'.pdf', '.docx', '.png', '.jpg', '.jpeg', '.txt'}
            current_files = set()
            for root, _, files in os.walk(sub_path):
                for f in files:
                    _, ext = os.path.splitext(f.lower())
                    if ext in allowed_ext and not f.startswith("~$") and f != "session.json":
                        current_files.add(os.path.join(root, f))

            processed_files = set(sess.get("processed_files", []))
            new_files = current_files - processed_files

            if new_files:
                logger.info(
                    f"Auto-watcher found {len(new_files)} new file(s) in '{d}' — "
                    f"triggering incremental ingestion for case '{case_id}'"
                )
                start_incremental_ingestion_thread(case_id, sorted(new_files))
