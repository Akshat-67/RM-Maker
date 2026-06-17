from utils.helpers import parse_relation_text, normalize_relation_prefix

def prune_rm_data(data):
    if not isinstance(data, dict):
        return data
        
    cleaned = {}
    doc_type = "RM"
    
    # Keep only RM allowed fields
    rm_keys = ["rd", "ad", "bs", "ls", "ps", "bsign", "ws", "unassigned_aadhars", "second_schedule", "ds", "ds_text"]
    for k in rm_keys:
        if k in data:
            cleaned[k] = data[k]
            
    # Prune ps items for RM
    if "ps" in cleaned and isinstance(cleaned["ps"], list):
        rm_ps_fields = ["adr", "n", "s", "e", "w"]
        clean_ps = []
        for p in cleaned["ps"]:
            if isinstance(p, dict):
                clean_ps.append({pk: p[pk] for pk in rm_ps_fields if pk in p})
            else:
                clean_ps.append(p)
        cleaned["ps"] = clean_ps
        
    # Prune bs items for RM
    if "bs" in cleaned and isinstance(cleaned["bs"], list):
        rm_bs_fields = ["s", "n", "a", "r", "rn", "relation_text", "adr", "id", "pan"]
        clean_bs = []
        for b in cleaned["bs"]:
            if isinstance(b, dict):
                item = {bk: b[bk] for bk in rm_bs_fields if bk in b}
                if item.get("r"):
                    item["r"] = normalize_relation_prefix(item["r"], doc_type)
                if item.get("r") and item.get("rn"):
                    item["relation_text"] = f"{item['r']} {item['rn']}"
                elif item.get("relation_text"):
                    r, rn = parse_relation_text(item["relation_text"])
                    item["r"] = normalize_relation_prefix(r, doc_type)
                    item["rn"] = rn
                    if item.get("rn"):
                        item["relation_text"] = f"{item['r']} {item['rn']}"
                clean_bs.append(item)
            else:
                clean_bs.append(b)
        cleaned["bs"] = clean_bs

    # Prune ws items for RM
    if "ws" in cleaned and isinstance(cleaned["ws"], list):
        rm_ws_fields = ["n", "r", "rn", "relation_text", "adr", "id", "a"]
        clean_ws = []
        for w in cleaned["ws"]:
            if isinstance(w, dict):
                item = {wk: w[wk] for wk in rm_ws_fields if wk in w}
                if item.get("r"):
                    item["r"] = normalize_relation_prefix(item["r"], doc_type)
                if item.get("r") and item.get("rn"):
                    item["relation_text"] = f"{item['r']} {item['rn']}"
                elif item.get("relation_text"):
                    r, rn = parse_relation_text(item["relation_text"])
                    item["r"] = normalize_relation_prefix(r, doc_type)
                    item["rn"] = rn
                    if item.get("rn"):
                        item["relation_text"] = f"{item['r']} {item['rn']}"
                clean_ws.append(item)
            else:
                clean_ws.append(w)
        cleaned["ws"] = clean_ws

    # Prune bsign items for RM
    if "bsign" in cleaned and isinstance(cleaned["bsign"], dict):
        rm_bsign_fields = ["n", "a", "d", "r", "rn", "relation_text", "pan", "id"]
        item = {k: cleaned["bsign"][k] for k in rm_bsign_fields if k in cleaned["bsign"]}
        if item.get("r"):
            item["r"] = normalize_relation_prefix(item["r"], doc_type)
        if item.get("r") and item.get("rn"):
            item["relation_text"] = f"{item['r']} {item['rn']}"
        elif item.get("relation_text"):
            r, rn = parse_relation_text(item["relation_text"])
            item["r"] = normalize_relation_prefix(r, doc_type)
            item["rn"] = rn
            if item.get("rn"):
                item["relation_text"] = f"{item['r']} {item['rn']}"
        cleaned["bsign"] = item

    # Normalize unassigned_aadhars for RM
    if "unassigned_aadhars" in cleaned and isinstance(cleaned["unassigned_aadhars"], list):
        for ua in cleaned["unassigned_aadhars"]:
            if isinstance(ua, dict) and ua.get("relation_text"):
                r, rn = parse_relation_text(ua["relation_text"])
                r_norm = normalize_relation_prefix(r, doc_type)
                if r_norm and rn:
                    ua["relation_text"] = f"{r_norm} {rn}"

    return cleaned
