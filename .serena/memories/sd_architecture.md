# Sale Deed (SD) Architecture Memory

The Sale Deed (SD) module handles AI extraction, data normalization, title chain mapping, and generation of formal deed agreements (e.g. flat or land transfers).

## Key Files
- Extractor: [extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/extractor.py) (uses Gemini Client to extract and map entities).
- Processor: [processor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/processor.py) (compiles data and handles DevLys rendering).
- Narrative Engine: [narrative.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/narrative.py) (generates title-chain narratives in Hindi matching firm style).
- Chain Templates: [chain_templates.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/chain_templates.py) (has template mappings for chain narratives).
- Schema: [schema.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/schema.py) (implements `prune_sd_data`).

## Core Data Schema Structures
- **`ss` / `sellers`**: Array of seller entities. Fields: `n` (name), `n_en` (English name), `a` (age), `c` (caste), `relation_text`, `rn` (relation name), `adr`, `pan`, `id` (Aadhaar).
- **`bs` / `buyers`**: Array of buyer entities. Fields: `n`, `n_en`, `a`, `c`, `relation_text`, `rn`, `adr`, `pan`, `id` (Aadhaar).
- **`ps` (Properties)**: Array of property entities. Holds dimensional and geographical boundaries: `plot_no`, `scheme`, `length_ew` (East-West length), `length_ns` (North-South length), `land_area`, `n`, `s`, `e`, `w`, `covered_area`, `flat_no`, `floor`, `building_name`, `project_name`, `village`, `tehsil`, `dist`.
- **`ws` (Witnesses)**: Array of witnesses.
- **`chain` / `title_chain`**: Array of historical deeds describing the ownership lineage.

## Schema Parity & Unification
- `prune_sd_data` maintains complete parity between list structures by mirroring `sellers` to `ss` and `buyers` to `bs` dynamically based on which list is more populated.
- Extracted property fields are normalized and concatenated into derived strings like `full_address`, `dimension_text`, and `boundary_text` for template compatibility.
