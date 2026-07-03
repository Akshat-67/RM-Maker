def prune_sd_data(data):
    if not isinstance(data, dict):
        return data
        
    def get_list_completeness(lst):
        if not lst or not isinstance(lst, list): return 0
        score = 0
        for item in lst:
            if isinstance(item, dict):
                score += sum(1 for v in item.values() if v)
        return score

    if "sellers" in data or "ss" in data:
        s_score = get_list_completeness(data.get("sellers"))
        ss_score = get_list_completeness(data.get("ss"))
        if ss_score >= s_score:
            data["sellers"] = data.get("ss", [])
        else:
            data["ss"] = data.get("sellers", [])

    if "buyers" in data or "bs" in data:
        b_score = get_list_completeness(data.get("buyers"))
        bs_score = get_list_completeness(data.get("bs"))
        if bs_score >= b_score:
            data["buyers"] = data.get("bs", [])
        else:
            data["bs"] = data.get("buyers", [])

    cleaned = {}
    
    # Keep only SD allowed fields (including both backend aliases and frontend keys)
    sd_keys = ["rd", "amount", "amount_words", "consideration", "tds", "hypothecation", "ss", "bs", "ps", "ws", "reg", "unassigned_aadhars", "sellers", "buyers", "chain_text", "payments", "seller_label", "buyer_label"]
    for k in sd_keys:
        if k in data:
            cleaned[k] = data[k]
            
    # Prune ps items for SD
    if "ps" in cleaned and isinstance(cleaned["ps"], list):
        sd_ps_fields = ["adr", "adr_en", "area", "area_unit", "plot_no", "scheme", "length_ew", "length_ns", "land_area", "unit", "n", "n_en", "s", "s_en", "e", "e_en", "w", "w_en", "ward", "state", "khasra", "parking_type", "parking_number", "area_type", "covered_area", "property_portion", "full_address", "dimension_text", "boundary_text", "flat_no", "floor", "building_name", "project_name", "village", "tehsil", "dist", "landmark", "const_area", "const_unit"]
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

