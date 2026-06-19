# SD Extraction Reliability Audit

## Objective
The mission was to perform a full SD extraction reliability audit and remediation. We observed symptoms such as missing seller/buyer arrays, incomplete property information, and `MISSING:*` placeholders in rendered SDs.

## Extraction Flow Map
The SD extraction pipeline traces the following path:
1. **Gemini Extraction (`modules/sd/extractor.py`)**: Uses Google Gemini to extract JSON data from the OCR texts. It uses fallback prompts and key rotation if it hits quota limits.
2. **Normalization (`modules/sd/extractor.py`)**: `_normalize_sd_response` standardizes dates, amounts, relations, and explicitly calls `_force_count` to ensure arrays like `ss` (sellers) and `bs` (buyers) have the expected length.
3. **Schema Validation / Pruning (`app.py` / `modules/sd/schema.py`)**: Calls `prune_case_data` which removes extraneous fields and ensures only SD-specific fields survive.
4. **Smart Merge (`app.py`)**: Calls `smart_merge(old_data, new_data, verified_fields)`. This function updates session data by merging newly extracted properties with the existing ones to avoid overwriting manually verified fields.
5. **Context Generation (`app.py` / `modules/sd/processor.py`)**: The `/generate` endpoint converts extracted session aliases (e.g. `adr`, `id`) back to the Word template fields (`address`, `aadhaar`) and generates boundary/dimension Hindi narrations via the extractor.
6. **Rendering (`modules/sd/processor.py`)**: The `DocxTemplate` replaces placeholders, converts the document back to KrutiDev using the `Unicode_to_KrutiDev` mappings, and highlights missing variables as `MISSING:*`.

## Root Cause Analysis
We developed a test harness (`tools/audit_sd_extraction.py`) and ran trace simulations. The audit revealed that **the primary cause of valid extracted data disappearing is NOT Gemini hallucination or schema pruning, but data loss occurring during state merges in `app.py`.**

Specifically, two severe bugs were found:

### 1. `smart_merge` Alias Mismatch (SS/BS Override)
- The `smart_merge` utility checks a hardcoded list of keys to perform unique-key list merging instead of index-based blind merging:
  `if path in ["ls", "ps", "unassigned_aadhars", "sellers", "buyers", "title_chain"]:`
- **The Bug:** For Sale Deeds, the application heavily uses the aliases `"ss"`, `"bs"`, and `"ws"`. Because these aliases were missing from the list, the system fell back to blindly overwriting the lists by index. If a subsequent AI incremental extraction returned empty `{"n": "", "relation_text": ""}` objects, or if the UI was loaded without the elements and saved, it completely wiped the valid extracted arrays.

### 2. `smart_merge` Property Duplication (PS Displacement)
- The unique key for properties (`"ps"`) in `smart_merge` is hardcoded to `"adr"`.
- **The Bug:** Gemini often extracts properties with a `plot_no` and `scheme` but leaves `adr` as an empty string `""` because the full address string isn't explicitly written in one block. When `smart_merge` encountered a new property with an empty `adr` key, it incorrectly treated it as a brand-new unique property instead of matching it with the existing `ps[0]` property.
- This caused properties to be **appended** to the array rather than merged. The template engine only renders `ps[0]`, pushing the incrementally extracted land area and dimensions to `ps[1]`, causing `MISSING:*` placeholders to appear on the final document.

### 3. UI Save Overwrites Arrays
- When a user views the case in the frontend and clicks the "Save" button without populating the empty padded inputs, the UI sends back an array filled with empty strings `""`.
- The `/save` endpoint blindly copied these empty arrays over the extracted session data.

## Fixes Implemented
The root causes were found and patched directly in `app.py`:

1. **`smart_merge` Fix:** Added `"ss"`, `"bs"`, and `"ws"` to the target paths for unique-key matching using the name (`"n"`) as the key.
2. **`smart_merge` PS Fix:** Added fallback logic where if the unique key (`adr` or `n`) is empty, and we are updating an item at an existing index, it safely merges by index instead of duplicating/appending new items.
3. **UI Save Fix:** Intercepted the `/save` endpoint in `app.py`. If the incoming UI payload arrays for `ss`, `bs`, `ws`, or `ps` consist entirely of empty strings, but valid data already exists in the backend session, the backend safely ignores the empty UI override and preserves the extracted data.

## Deliverables
- Extraction Test Harness: `tools/audit_sd_extraction.py`
- Demonstration Scripts: `demonstrate_bugs.py` (proves property duplication and seller override) and `demonstrate_bugs_part2.py` (proves UI save wipeout).
- Code patches applied to `app.py`.

## Validation
By running `tools/audit_sd_extraction.py` against `validation_cases` and checking the simulation pipeline, we verified that:
- Sellers, Buyers, and Property data are now correctly merged and preserved across multiple AI extractions.
- Duplicate appends for properties missing the `adr` key have been eliminated.
- Missing field issues (Aadhaar, address) are gracefully padded without overwriting existing data.
