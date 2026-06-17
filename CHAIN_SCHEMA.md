# Title Chain Schema Architecture (`CHAIN_SCHEMA.md`)

This document defines the canonical JSON structure for handling property title chains in Sale Deeds, based on the analysis of real-world DevLys 040 legal documents.

## 1. Canonical Structure: `title_events[]`

The title chain is stored as an array of `title_events`, ordered chronologically from the root document (e.g., initial allotment/patta) to the immediate previous owner.

```json
{
  "title_chain": [
    {
      "event_id": "uuid-or-index",
      "event_type": "SALE_DEED",
      "date": "17.04.2018",
      "executant_name": "महेश चंद तोदवाल",
      "claimant_name": "राजबाला",
      "is_registered": "true",
      "reg_office": "जयपुर सप्तम",
      "reg_date": "19.04.2018",
      "reg_book": "1",
      "reg_vol": "464",
      "reg_page": "98",
      "reg_no": "201803021103534",
      "reg_add_book": "1",
      "reg_add_vol": "1855",
      "reg_add_page": "1026",
      "book_no": "1",
      "volume_no": "464",
      "page_no": "98",
      "additional_book_no": "1",
      "additional_volume_no": "1855",
      "additional_page_range": "1026",
      "consideration_amount": "500000",
      "document_name": "विक्रय पत्र",
      "document_number": "डी-2341",
      "project_name": "रॉयल एन्क्लेव",
      "unit_number": "एस-1",
      "confidence": "High",
      "source_text": "...",
      "event_property_type": "PLOT"
    }
  ]
}
```

## 2. Event Types (`event_type`)

Based on sample analysis, the system standardizes title events into the following canonical types:

1. `ALLOTMENT` (आवंटन पत्र / पट्टा विलेख) - Original grant of land by an authority/society (e.g., JDA).
2. `SALE_DEED` (विक्रय पत्र / बेचाननामा) - Transfer of ownership for consideration.
3. `GIFT_DEED` (बक्षिशनामा / दान पत्र) - Transfer of ownership without consideration.
4. `RELINQUISHMENT` (हकत्याग पत्र / रिलीज डीड) - Surrender of rights by co-owners.
5. `POA` (मुख्तियारनामा आम / खास) - Power of Attorney granting authority to act.
6. `AGREEMENT_TO_SALE` (इकरारनामा बेचान) - Agreement to sell.
7. `CORRECTION_DEED` (शुद्धि पत्र) - Rectification of errors in a previous deed.
8. `WILL` (वसीयतनामा) - Testamentary succession.

## 3. Field Definitions & Real-World Mapping

### Required Fields (All Events)
- `event_type` (String): Standardized enum value.
- `document_name` (String): The exact Hindi term used in the generated deed (e.g., "पट्टा विलेख").
- `date` (String): Execution date of the document (`DD.MM.YYYY`).
- `claimant_name` (String): The party receiving the right/title.

### Registration Fields (Mapping to DevLys Document Terms)
If `is_registered == "true"`:
- `reg_office` (String): Sub-Registrar Office (उप-पंजीयक).
- `reg_date` (String): Date of registration.
- `reg_no` (String): Registration/Serial number (क्रम संख्या).
- `reg_book` / `book_no` (String): Book number (पुस्तक संख्या).
- `reg_vol` / `volume_no` (String): Volume number (जिल्द संख्या).
- `reg_page` / `page_no` (String): Page number (पृष्ठ संख्या).
- `reg_add_book` / `additional_book_no`: Additional Book (अतिरिक्त पुस्तक संख्या).
- `reg_add_vol` / `additional_volume_no`: Additional Volume (अतिरिक्त जिल्द संख्या).
- `reg_add_page` / `additional_page_range`: Additional Page (अतिरिक्त पृष्ठ संख्या).

### Optional / Contextual Fields
- `executant_name` (String): The name of the party transferring the right.
- `claimant_name` (String): The name of the party receiving the right.
- `consideration_amount` (String): Required for Sale Deeds and ATS.
- `document_number` (String): Document number (often for Allotment/Patta).
- `project_name` (String): Used primarily for CONSTRUCTION events.
- `unit_number` (String): Flat/Unit number.
- `event_property_type` (String): Type of property (e.g., PLOT, FLAT).
- `confidence` (String): Extractor confidence score.
- `source_text` (String): Text snippet extracted by LLM to prove origin.
- `field_sources` (Object): Field-level source references.

## 4. Normalization Rules
- **Ordering**: Events MUST be sorted chronologically by `date`.
- **Script Consistency**: All textual values must be stored in **Unicode Hindi**, which will be converted to DevLys 040 during final rendering.
