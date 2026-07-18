# Registered Mortgage (RM) Document Pipeline

This document describes the design, schema mapping, stability parameters, and template compiling for the Registered Mortgage (RM) pipeline.

---

## 1. Pipeline Overview
The RM pipeline extracts financing details, security terms, borrower lists, and witness parameters from files to compile a standard bank-compliant Registered Mortgage deed.
- *(For pipeline separation rationale, see [ADR-0003: RM and SD Independent Pipelines](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/adr/ADR-0003.md).)*

```
Sanction Letter / LSR → RMDataExtractor → RM Schema (session.json) → UI Verification → RMTemplateProcessor → docxtpl
```

---

## 2. Extraction & Data Schema
The RM pipeline stores case parameters inside `session.json` under specific lists:
- *(For our fact-extraction principles, see [ADR-0004: AI Extracts Facts, Templates Own Legal Language](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/adr/ADR-0004.md).)*

| Key | Entities | Description |
| :--- | :--- | :--- |
| `bs` | Borrowers | List of borrowers/co-borrowers, including names, age, addresses, Aadhaar, PAN, and normalized relations. |
| `ls` | Loans | Loan particulars: account number (LAN), sanction dates, interest rates, values in numeric and word format. |
| `ps` | Properties | Details of mortgaged properties: type, dimensions, landmarks, and structural boundaries. |
| `ws` | Witnesses | Witnesses' names, Aadhaar, and addresses. |
| `bsign` | Bank Signatory | Particulars of the bank's authorized signatory. |
| `ds` | Schedules | Schedules defining boundary markers and land areas. |

---

## 3. Context Processing & Template Rendering
The context is normalized by the `RMTemplateProcessor` ([modules/rm/processor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/processor.py)):

- **Ordinal Dates**: Dates (e.g. execution date, sanction date) are formatted into legal ordinals (e.g. "this 14th day of May, 2026").
- **Currency Mapping**: Loan amounts are converted into words and formatted with standard comma separators (e.g. `50,00,000` to "Fifty Lakh Only").
- **DevLys Conversion**: The processor traverses the context dictionary, converts all Unicode Hindi string values to legacy DevLys encoding, and outputs Kruti Dev compatible binary segments for rendering.
- **Run Repairing**: Uses `DocManipulator` to ensure Jinja braces are not split across separate XML run segments inside the Word template.

---

## 4. Stability Policies
The RM pipeline is a production-hardened system:
- **No Schema Changes**: Do not add, rename, or drop keys in the RM session dictionary or templates.
- **Backward Compatibility**: Any updates to processing rules must support older `session.json` files on disk.
- **Strict Matching**: Template placeholders (`{{bs[0].n}}`) are treated as strict API contracts. Verify references across bank templates (`templates/ICICI/`, `templates/HFFC/`, etc.) before making adjustments.
