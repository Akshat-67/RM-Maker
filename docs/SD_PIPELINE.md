# Sale Deed (SD) Document Pipeline

This document describes the design, entity shorthands, narrative timeline generator, and template rendering for the Sale Deed (SD) pipeline.

---

## 1. Pipeline Overview
The SD pipeline extracts seller/buyer particulars, property boundary coordinates, and historical title transaction sequences to generate a formal, legally compliant Sale Deed document.
- *(For pipeline separation rationale, see [ADR-0003: RM and SD Independent Pipelines](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/adr/ADR-0003.md).)*

```
KYC & Title Deeds → SDDataExtractor → SD Schema (session.json) → Title Chain Timeline & Narrative → SDTemplateProcessor → docxtpl
```

---

## 2. Canonical Shorthands
Preserve the exact shorthand entity lists inside SD session databases and templates:

| Shorthand | Meaning | Description |
| :--- | :--- | :--- |
| `ss` | Sellers | Details of the property sellers (names, age, address, PAN, Aadhaar, relations). |
| `bs` | Buyers | Details of the buyers. |
| `ws` | Witnesses | Witnesses to the transaction. |
| `ps` | Properties | Details of the property being sold (boundaries, dimension measurements). |
| `chain` | Title Chain | Chronological list of historical ownership transaction events. |

---

## 3. Title Chain & Narrative Engine
The SD pipeline features an automated Title-Chain Narrative Generator ([modules/sd/narrative.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/narrative.py)):
- *(For our fact-extraction principles, see [ADR-0004: AI Extracts Facts, Templates Own Legal Language](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/adr/ADR-0004.md).)*
- **Timeline Events**: Parses legal events (sales, gifts, inheritance, mortgage releases) representing the ownership history.
- **Narrative Compilation**: Compares the event list and sends structured prompts to Gemini. Gemini returns a formal, cohesive chronological narrative in Hindi (using standard legal phrasing like "विक्रय पत्र", "स्वामित्व", etc.).
- **Manual Mode Toggle**: Users can enable `chain_is_manual` in the UI. When active, it bypasses the AI compiler and allows engineers or legal proofreaders to type or edit the narrative text directly.

---

## 4. Rendering & Compiling
- **Address Formatting**: Title-cases addresses and removes duplicates (e.g. "Jaipur Jaipur" is simplified to "Jaipur").
- **Hindi Font Encoding**: Translates Unicode characters into legacy DevLys encoding at the document compilation boundary to render correct Hindi characters on custom templates (`templates/SALE_DEED/`).
- **Entity Pre-Padding**: The engine pads the lists of sellers, buyers, and witnesses to match the counts selected in the UI, ensuring no details are dropped during merge routines.
