import os
import re
import shutil

from services.session_manager import CASES_DIR

TEMPLATES_DIR = "templates"


# --- Template Discovery ---
import time
import copy

_discover_cache = None
_discover_cache_mtime = 0

# --- Template Discovery ---
def discover_templates():
    global _discover_cache, _discover_cache_mtime
    
    if not os.path.exists(TEMPLATES_DIR):
        return {}, {}, []

    # Get combined mtime of TEMPLATES_DIR and bank folders to detect changes
    try:
        current_mtime = os.path.getmtime(TEMPLATES_DIR)
        for item in os.listdir(TEMPLATES_DIR):
            bank_dir = os.path.join(TEMPLATES_DIR, item)
            if os.path.isdir(bank_dir):
                current_mtime = max(current_mtime, os.path.getmtime(bank_dir))
    except Exception:
        # Fallback to force refresh on any mtime lookup error
        current_mtime = time.time()

    if _discover_cache is not None and _discover_cache_mtime == current_mtime:
        # Return copies so callers mutating lists/dicts won't pollute our cache
        return copy.deepcopy(_discover_cache[0]), copy.deepcopy(_discover_cache[1]), list(_discover_cache[2])

    template_map = {}
    sd_template_map = {}
    bank_folders = []

    for item in os.listdir(TEMPLATES_DIR):
        bank_dir = os.path.join(TEMPLATES_DIR, item)
        if not os.path.isdir(bank_dir):
            continue

        bank_name = item.upper()
        if bank_name == "SALE_DEED":
            for fname in os.listdir(bank_dir):
                if not fname.lower().endswith(".docx"):
                    continue
                # Parse: SD_{NAME}_{#S}S_{#B}B.docx or similar, or map via fallbacks
                m = re.search(r"(\d+)S_(\d+)B", fname, re.IGNORECASE)
                if m:
                    s_count = m.group(1)
                    b_count = m.group(2)
                else:
                    fname_lower = fname.lower()
                    if "vivek" in fname_lower or "saxena" in fname_lower:
                        s_count, b_count = "2", "1"
                    elif "manoj" in fname_lower or "monu" in fname_lower:
                        s_count, b_count = "1", "1"
                    elif "ganesh" in fname_lower or "pareek" in fname_lower:
                        s_count, b_count = "2", "1"
                    elif "balkishan" in fname_lower or "gurjar" in fname_lower:
                        s_count, b_count = "2", "1"
                    else:
                        s_count, b_count = "1", "1"
                if s_count not in sd_template_map:
                    sd_template_map[s_count] = {}
                sd_template_map[s_count][b_count] = os.path.join(bank_dir, fname)
            continue

        bank_folders.append(bank_name)
        template_map[bank_name] = {}

        for fname in os.listdir(bank_dir):
            if not fname.lower().endswith(".docx"):
                continue
            # Parse: RM_{BANK}_{#B}B_{#L}L_anything.docx, with looser fallbacks
            m = re.match(r"RM_" + re.escape(bank_name) + r"_(\d+)B_(\d+)L", fname, re.IGNORECASE)
            if not m:
                # Fallback to RM_(\d+)B_(\d+)L without bank name
                m = re.match(r"RM_(\d+)B_(\d+)L", fname, re.IGNORECASE)
            if not m:
                # Fallback to (\d+)B_(\d+)L without RM_ and bank name
                m = re.match(r"(\d+)B_(\d+)L", fname, re.IGNORECASE)
                
            if m:
                b_count = m.group(1)   # "1", "2", "3" etc.
                l_count = m.group(2)   # "1", "2", "3" etc.
                
                # Check if it specifies two properties in the filename (e.g. "two properties", "2p", or "2_properties")
                fname_lower = fname.lower()
                is_two_props = "two properties" in fname_lower or "2p" in fname_lower or "2_properties" in fname_lower
                p_count = "2" if is_two_props else "1"
                
                if b_count not in template_map[bank_name]:
                    template_map[bank_name][b_count] = {}
                if l_count not in template_map[bank_name][b_count]:
                    template_map[bank_name][b_count][l_count] = {}
                template_map[bank_name][b_count][l_count][p_count] = os.path.join(bank_dir, fname)

    bank_folders.sort()
    if "ICICI" in bank_folders:
        bank_folders.remove("ICICI")
        bank_folders.insert(0, "ICICI")

    _discover_cache = (template_map, sd_template_map, bank_folders)
    _discover_cache_mtime = current_mtime

    return copy.deepcopy(template_map), copy.deepcopy(sd_template_map), list(bank_folders)


# --- Smart Merge Utility ---
def smart_merge(old, new, verified_fields, path=""):
    # If old is empty/falsy, take the new value (even if new is empty, this is correct for initialization)
    if not old:
        return new
        
    if isinstance(new, dict):
        merged = old.copy() if isinstance(old, dict) else {}
        for k, v in new.items():
            p = f"{path}.{k}" if path else k
            if p in verified_fields:
                continue
            merged[k] = smart_merge(merged.get(k), v, verified_fields, p)
        return merged
        
    elif isinstance(new, list):
        merged = list(old) if isinstance(old, list) else []
        
        # If it is one of our entity lists: 'ls', 'ps', 'unassigned_aadhars', 'sellers', 'buyers', 'ss', 'bs', 'ws', 'title_chain'
        # We merge them by unique keys rather than index to prevent overwriting during incremental scans
        if path in ["ls", "ps", "unassigned_aadhars", "sellers", "buyers", "ss", "bs", "ws", "title_chain",
                    "data.ls", "data.ps", "data.unassigned_aadhars", "data.sellers", "data.buyers", "data.ss", "data.bs", "data.ws", "data.title_chain"]:
            if "ls" in path: key_field = "n"
            elif "unassigned" in path: key_field = "id"
            elif "sellers" in path or "buyers" in path or "ss" in path or "bs" in path or "ws" in path: key_field = "n"
            elif "title_chain" in path: key_field = "date"
            else: key_field = "adr"
            
            # Start with existing items that actually contain values
            existing_entities = [item for item in merged if isinstance(item, dict) and any(item.values())]
            
            # Map existing entities by their unique normalized key
            existing_by_key = {}
            empty_existing_indices = []
            for i, item in enumerate(existing_entities):
                val = str(item.get(key_field, "")).strip().casefold()
                if val:
                    existing_by_key[val] = i
                else:
                    empty_existing_indices.append(i)
                    
            for idx, new_item in enumerate(new):
                if not isinstance(new_item, dict) or not any(new_item.values()):
                    continue
                new_val = str(new_item.get(key_field, "")).strip().casefold()
                
                if new_val and new_val in existing_by_key:
                    # Key match found: merge recursively
                    match_idx = existing_by_key[new_val]
                    merged_item = smart_merge(existing_entities[match_idx], new_item, verified_fields, f"{path}.MATCH")
                    existing_entities[match_idx] = merged_item
                elif new_val and empty_existing_indices:
                    # Merge extracted item into an empty UI slot
                    empty_idx = empty_existing_indices.pop(0)
                    merged_item = smart_merge(existing_entities[empty_idx], new_item, verified_fields, f"{path}.{empty_idx}")
                    existing_entities[empty_idx] = merged_item
                    existing_by_key[new_val] = empty_idx
                elif not new_val and len(existing_entities) > idx and ("ps" in path or "ss" in path or "bs" in path or "ws" in path):
                    # Same index fallback for items if key is missing but we're updating the same position
                    merged_item = smart_merge(existing_entities[idx], new_item, verified_fields, f"{path}.{idx}")
                    existing_entities[idx] = merged_item
                else:
                    # New unique key or safely appending
                    existing_entities.append(new_item)
                    if new_val:
                        existing_by_key[new_val] = len(existing_entities) - 1
                    else:
                        empty_existing_indices.append(len(existing_entities) - 1)
                    
            return existing_entities
            
        # Standard merge by index for other lists (like 'bs', 'ws' where count is fixed)
        while len(merged) < len(new):
            merged.append({})
        
        result = []
        for i in range(max(len(merged), len(new))):
            old_item = merged[i] if i < len(merged) else None
            new_item = new[i] if i < len(new) else None
            result.append(smart_merge(old_item, new_item, verified_fields, f"{path}.{i}"))
        return result
        
    # For primitive values (strings, numbers, etc.)
    if new == "" or new is None:
        return old  # Keep old value if new is empty
    return new


# --- Case Directory Operations ---
def delete_case_directory(case_id):
    """Delete the entire case directory from disk. Pure filesystem operation."""
    case_path = os.path.join(CASES_DIR, case_id)
    if os.path.exists(case_path):
        shutil.rmtree(case_path)
        return True
    return False


def resolve_case_file_path(case_id, filename):
    """Search across all bucket directories and return the absolute path if found."""
    safe_case_id = os.path.basename(case_id)
    case_dir = os.path.abspath(os.path.join(CASES_DIR, safe_case_id))
    search_dirs = [
        os.path.join(case_dir, "buckets", "kyc"),
        os.path.join(case_dir, "buckets", "legal"),
        os.path.join(case_dir, "buckets", "ats"),
        os.path.join(case_dir, "buckets", "title_chain"),
        os.path.join(case_dir, "buckets", "ocr"),
        os.path.join(case_dir, "files"),
        os.path.join(case_dir, "legal_reports"),
        case_dir
    ]
    
    # Local import to prevent circular import issues
    from services.session_manager import load_case_session
    session = load_case_session(case_id)
    if session and session.get("case_inbox_path"):
        inbox_path = session.get("case_inbox_path")
        if os.path.exists(inbox_path):
            search_dirs.append(inbox_path)
            for root, dirs, _ in os.walk(inbox_path):
                for d in dirs:
                    search_dirs.append(os.path.join(root, d))
                    
    safe_filename = os.path.basename(filename)
    for directory in search_dirs:
        file_path = os.path.join(directory, safe_filename)
        if os.path.exists(file_path):
            return directory, safe_filename
    return None, safe_filename


def save_uploaded_file_to_bucket(case_id, bucket_name, filename, file_bytes):
    """Save raw file bytes to the appropriate bucket directory. Returns the saved filepath."""
    case_bucket_dir = os.path.join(CASES_DIR, case_id, "buckets", bucket_name)
    os.makedirs(case_bucket_dir, exist_ok=True)
    filepath = os.path.join(case_bucket_dir, filename)
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    return filepath


def remove_file_from_disk(case_id, filename, bucket=None):
    """Remove a file from disk. Returns (success, error_message)."""
    filename = os.path.basename(filename)

    if bucket:
        bucket_dir = os.path.join(CASES_DIR, case_id, "buckets", bucket)
        file_path = os.path.join(bucket_dir, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True, ""
            except Exception as e:
                return False, str(e)
        return False, "File not found"
    else:
        # Try files/ directory first
        case_files_dir = os.path.join(CASES_DIR, case_id, "files")
        file_path = os.path.join(case_files_dir, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True, ""
            except Exception as e:
                return False, str(e)

        # Try legal_reports/ directory
        legal_dir = os.path.join(CASES_DIR, case_id, "legal_reports")
        file_path = os.path.join(legal_dir, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True, ""
            except Exception as e:
                return False, str(e)

        return False, "File not found"
