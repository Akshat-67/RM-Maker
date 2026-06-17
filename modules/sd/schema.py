def prune_sd_data(data):
    if not isinstance(data, dict):
        return data
        
    cleaned = {}
    
    # Keep only SD allowed fields
    sd_keys = ["rd", "amount", "amount_words", "consideration", "tds", "hypothecation", "ss", "bs", "ps", "ws", "title_chain", "reg", "unassigned_aadhars"]
    for k in sd_keys:
        if k in data:
            cleaned[k] = data[k]
            
    # Prune ps items for SD
    if "ps" in cleaned and isinstance(cleaned["ps"], list):
        sd_ps_fields = ["adr", "plot_no", "scheme", "length_ew", "length_ns", "land_area", "unit", "n", "s", "e", "w", "ward", "state", "khasra", "parking_type", "parking_number", "area_type", "covered_area", "property_portion", "full_address", "dimension_text", "boundary_text"]
        clean_ps = []
        for p in cleaned["ps"]:
            if isinstance(p, dict):
                clean_ps.append({pk: p[pk] for pk in sd_ps_fields if pk in p})
            else:
                clean_ps.append(p)
        cleaned["ps"] = clean_ps
        
    # Prune bs items for SD
    if "bs" in cleaned and isinstance(cleaned["bs"], list):
        sd_bs_fields = ["n", "a", "c", "relation_text", "adr", "id", "pan"]
        clean_bs = []
        for b in cleaned["bs"]:
            if isinstance(b, dict):
                clean_bs.append({bk: b[bk] for bk in sd_bs_fields if bk in b})
            else:
                clean_bs.append(b)
        cleaned["bs"] = clean_bs

    # Prune ss items for SD
    if "ss" in cleaned and isinstance(cleaned["ss"], list):
        sd_ss_fields = ["n", "a", "c", "relation_text", "adr", "id", "pan"]
        clean_ss = []
        for s in cleaned["ss"]:
            if isinstance(s, dict):
                clean_ss.append({sk: s[sk] for sk in sd_ss_fields if sk in s})
            else:
                clean_ss.append(s)
        cleaned["ss"] = clean_ss
        
    return cleaned
