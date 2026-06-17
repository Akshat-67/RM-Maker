# Sale Deed (SD) Data Contract & Schema (VALIDATED)

This document defines the definitive JSON schema for Sale Deed document processing, updated after real-world document validation.

## 1. Core Principles
- **Naming**: Use shorthand keys (e.g., `ss` for Sellers) to match existing RM structures.
- **Script**: All textual fields must be stored in **Unicode Hindi**.
- **Hierarchy**: Case -> Parties (ss/bs) -> Property (ps) -> Title Chain -> Registration.

## 2. Definitive JSON Schema

```json
{
  "doc_type": "SD",
  "rd": "25.05.2026",
  "amount": "1500000",
  "amount_words": "पंद्रह लाख",
  "hypothecation": "Canfin Homes Ltd.",
  "ss": [
    {
      "n": "Seller Name",
      "a": "45",
      "c": "Yadav",
      "r": "पुत्र",
      "rn": "Relative Name",
      "adr": "Full Address",
      "id": "Aadhar Number",
      "pan": "PAN Number"
    }
  ],
  "bs": [
    {
      "n": "Buyer Name",
      "a": "32",
      "c": "Meena",
      "r": "पुत्री",
      "rn": "Relative Name",
      "adr": "Full Address",
      "id": "Aadhar Number",
      "pan": "PAN Number"
    }
  ],
  "ps": [
    {
      "adr": "Property Address",
      "plot_no": "72",
      "scheme": "Shiv Enclave",
      "village": "Gawar Brahmani",
      "tehsil": "Sanganer",
      "dist": "Jaipur",
      "land_area": "63.33",
      "const_area": "570",
      "unit": "Sq. Yards / Sq. Ft",
      "n": "North Boundary",
      "s": "South Boundary",
      "e": "East Boundary",
      "w": "West Boundary"
    }
  ],
  "ws": [
    {
      "n": "Witness Name",
      "r": "पुत्र",
      "rn": "Relative Name",
      "adr": "Full Address"
    }
  ],
  "title_chain": [
    {
      "event_type": "SALE_DEED",
      "document_name": "विक्रय पत्र",
      "date": "10.01.2015",
      "executant_name": "Seller Name",
      "claimant_name": "Buyer Name",
      "is_registered": "true",
      "reg_office": "Jaipur VII",
      "reg_date": "10.01.2015",
      "reg_book": "1",
      "reg_vol": "100",
      "reg_page": "50",
      "reg_no": "2015010101",
      "reg_add_book": "1",
      "reg_add_vol": "200",
      "reg_add_page": "1-10"
    }
  ],
  "chain": [
    "NOTE: 'chain' is an alias for 'title_chain' used in some templates."
  ],
  "reg": {
    "office": "Jaipur VII",
    "book": "1",
    "vol": "1234",
    "page": "56",
    "reg_no": "2026010101",
    "reg_date": "25.05.2026"
  }
}
```

## 3. Field Definitions (New & Updated)

| Field | Name | Script | Reason |
| :--- | :--- | :--- | :--- |
| `ss[i].c` / `bs[i].c` | Caste | Unicode Hindi | Legally required identification in deeds. |
| `ps[i].land_area` | Land Area | Numeric | Total area of the plot. |
| `ps[i].const_area`| Cons. Area | Numeric | Area of the built structure (if any). |
| `ps[i].unit` | Area Unit | Unicode Hindi | e.g. oxZxt (Sq. Yards) or oxZQhV (Sq. Ft). |
| `ps[i].tehsil` | Tehsil | Unicode Hindi | Required for administrative tracking. |
| `ss[i].adr` / `bs[i].adr` | Address | Unicode Hindi | Alias for full address string. |
| `ss[i].relation_text` | Relation Phrase | Unicode Hindi | Full relative phrase (e.g., 'पुत्र श्री'). Used as an alias/composition of `r` + `rn`. |
| `hypothecation` | Bank Name | Unicode Hindi | Records if the property is currently under mortgage. |
| `title_chain[i]` | Chain Event | Object | Full registration metadata for every ownership transfer (can also use `chain` alias). |

## 4. Normalization Rules
1.  **Relation (`r`)**: Extract exact Hindi term (पुत्र, पुत्री, पत्नी) from the document.
2.  **Boundaries**: Ensure cardinal directions (iwoZ, if'pe, mÙkj, nf{k.k) are mapped correctly to e, w, n, s.
3.  **Title Chain**: If registration numbers are mixed in a string, the AI must parse them into the structured `title_chain` object fields.
