def prune_sd_data(data):
    if not isinstance(data, dict):
        return data
        
    # Force alignment between sellers/ss and buyers/bs
    if "sellers" in data:
        data["ss"] = data["sellers"]
    elif "ss" in data:
        data["sellers"] = data["ss"]

    if "buyers" in data:
        data["bs"] = data["buyers"]
    elif "bs" in data:
        data["buyers"] = data["bs"]

    if "chain" in data:
        data["title_chain"] = data["chain"]
    elif "title_chain" in data:
        data["chain"] = data["title_chain"]
        
    cleaned = {}
    
    # Keep only SD allowed fields (including both backend aliases and frontend keys)
    sd_keys = ["rd", "amount", "amount_words", "consideration", "tds", "hypothecation", "ss", "bs", "ps", "ws", "title_chain", "reg", "unassigned_aadhars", "sellers", "buyers", "chain"]
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
        
    # Prune bs and buyers items for SD
    sd_bs_fields = ["n", "n_en", "a", "c", "relation_text", "rn", "rn_en", "adr", "adr_en", "id", "pan", "r"]
    for k in ["bs", "buyers"]:
        if k in cleaned and isinstance(cleaned[k], list):
            clean_list = []
            for item in cleaned[k]:
                if isinstance(item, dict):
                    clean_list.append({field: item[field] for field in sd_bs_fields if field in item})
                else:
                    clean_list.append(item)
            cleaned[k] = clean_list

    # Prune ss and sellers items for SD
    sd_ss_fields = ["n", "n_en", "a", "c", "relation_text", "rn", "rn_en", "adr", "adr_en", "id", "pan", "r"]
    for k in ["ss", "sellers"]:
        if k in cleaned and isinstance(cleaned[k], list):
            clean_list = []
            for item in cleaned[k]:
                if isinstance(item, dict):
                    clean_list.append({field: item[field] for field in sd_ss_fields if field in item})
                else:
                    clean_list.append(item)
            cleaned[k] = clean_list
            
    return cleaned

