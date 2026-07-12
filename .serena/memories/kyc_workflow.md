# KYC & Relation Workflow Memory

The KYC workflow extracts, normalizes, pairs, and split-parses personal identity information (Aadhaar cards and PAN cards) for all parties.

## Data Extraction & Parsing
- Extracted via Gemini vision/text inputs using structured prompts.
- **Deceased Prefixes**: Legacy prefixes (e.g. "Late", "स्व.", "स्व-", "स्वर्गीय") are normalized to a clean, standard Unicode Hindi prefix `"स्वर्गीय श्री "` or `"स्वर्गीय श्रीमती "`.
- **Gender-aware Salutation Assignment**: Assigns "Mr."/"Mrs." in English and "श्री"/"श्रीमती" in Hindi based on gender and relation types.
- **Relation Splitting**:
  - Split into Relative Type `r` (e.g. `S/o`, `W/o`, `D/o` in RM; `पुत्र`, `पत्नी`, `पुत्री` in SD) and Relative Name `rn`.
  - Stored separately inside backend case schemas and serialized cleanly.

## Aadhaar Image Pairing & Tab Renaming
- Aadhaar card front and back images are paired dynamically on upload.
- Displays structured data next to paired image thumbnails in the UI for verification.
- Uses dynamic tabs inside `case.html` labeled with the person's name once extracted.

## RM-Specific Unassigned Aadhaar Flow
- Unassigned Aadhaar card uploads go directly into `unassigned_aadhars`.
- Operators drag, drop, or select these unassigned records to assign them as primary borrowers (`bs`) or witnesses (`ws`) in the UI.
- The `r` and `rn` fields are computed and preserved during this transfer.
