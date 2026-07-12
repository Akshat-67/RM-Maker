# Registered Mortgage (RM) Architecture Memory

The Registered Mortgage (RM) system manages AI extraction, validation, and template rendering for mortgage deeds (e.g. ICICI Bank formats).

## Key Files
- Extractor: [extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/extractor.py) (uses Gemini Client to extract and map entities).
- Processor: [processor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/processor.py) (compiles data and handles DevLys rendering).
- Schema: [schema.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/schema.py) (implements `prune_rm_data` to serialize cases).

## Core Data Schema Structures
- **`bs` (Borrowers)**: Array of client entities. Key fields: `s` (salutation), `n` (name), `a` (age), `dob`, `r` (relation type, S/o, W/o), `rn` (relation name), `relation_text`, `adr`, `id`, `pan`.
- **`ls` (Loans)**: Array of loans. Key fields: `n` (LAN No), `a` (Figures), `w` (Words), `t` (Tenure/Type).
- **`ps` (Properties)**: Array of mortgaged property entities. Key fields: `adr`, `n`, `s`, `e`, `w` (boundaries).
- **`ws` (Witnesses)**: Array of witness entities. Key fields: `n`, `r`, `rn`, `relation_text`, `adr`, `id`, `a`, `dob`.
- **`bsign` (Bank Signatory)**: Bank officer signing the deed.
- **`unassigned_aadhars`**: Holds temporary Aadhaar card extractions prior to assignment.

## Workflows & Rules
- **Aadhaar Extraction**: In RM mode, Aadhaar card uploads are processed by AI and funneled exclusively into the `unassigned_aadhars` list.
- **Relation Preservation**: Ensure the `r` and `rn` fields are populated and retained during serialization in `prune_rm_data`. If only `relation_text` is present, it is parsed using `parse_relation_text` to extract `r` and `rn`.
