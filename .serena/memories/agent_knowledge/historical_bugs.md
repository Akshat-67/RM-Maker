# Agent Knowledge: Historical Bugs

This memory summarizes recurring patterns of bugs and lessons from [historical_bugs.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/agent_knowledge/historical_bugs.md).

## Recurrent Regressions & Safeguards
- **DevLys & Font Conversion**:
  - Unicode internally.
  - Legacy DevLys conversion only at docx rendering boundary.
  - Do not force legacy fonts globally (forcing DevLys on Unicode runs causes Times New Roman fallback).
  - Splitting regex must exclude single legacy characters to avoid breaking text blocks.
- **Salutations & Normalization**:
  - Extract and separate prefix salutations (Mr./Mrs./Shri/Smt.) during AI extraction to prevent name nesting in UI inputs.
  - Automatically strip duplicate salutations (e.g. "श्री श्री") on session load.
- **Address Formatting**:
  - Always title-case addresses on save, load, and render. Clean up duplicate district tokens (e.g. "Jaipur Jaipur").
- **KYC merge**:
  - Null-check dictionary merges inside `_merge_kyc_results` to prevent `NoneType` attribute crashes.
  - Pair Aadhaar front/back scans phonetically and strip extra trailing digits.
- **UI State Loss**:
  - Ensure witness and bank officer variables are synchronized during front-end saves.
- **e-Panjiyan Automation**:
  - Skip navigation buttons when counting executants or parties.
  - Advance partyStage *before* form submits to prevent page reload race conditions.
  - Bind Flask server to `0.0.0.0` to receive MacroDroid OTP forwards.
- **Template Placeholders**:
  - Keys are contracts. Keep lowercase and capitalized variants (e.g. `chain_text` and `Chain_Text`) sync'd. Format dates based on pipeline (ordinals for RM, DD.MM.YYYY for SD).
