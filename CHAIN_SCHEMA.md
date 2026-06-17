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
      "executant": {
        "name": "महेश चंद तोदवाल",
        "relation": "पुत्र श्री",
        "relative_name": "रामलाल तोदवाल"
      },
      "claimant": {
        "name": "राजबाला",
        "relation": "पत्नी श्री",
        "relative_name": "महेश चंद तोदवाल"
      },
      "registration": {
        "is_registered": true,
        "office": "जयपुर सप्तम",
        "date": "19.04.2018",
        "book": "1",
        "vol": "464",
        "page": "98",
        "reg_no": "201803021103534",
        "add_book": "1",
        "add_vol": "1855",
        "add_page": "1026"
      },
      "consideration_amount": "500000",
      "document_name": "विक्रय पत्र"
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
- `claimant.name` (String): The party receiving the right/title.

### Registration Fields (Mapping to DevLys Document Terms)
If `registration.is_registered == true`:
- `registration.office` (String): Sub-Registrar Office (उप-पंजीयक).
- `registration.date` (String): Date of registration.
- `registration.book` (String): Book number (पुस्तक संख्या).
- `registration.vol` (String): Volume number (जिल्द संख्या).
- `registration.page` (String): Page number (पृष्ठ संख्या).
- `registration.reg_no` (String): Registration/Serial number (क्रम संख्या).
- `registration.add_book`: Additional Book (अतिरिक्त पुस्तक संख्या).
- `registration.add_vol`: Additional Volume (अतिरिक्त जिल्द संख्या).
- `registration.add_page`: Additional Page (अतिरिक्त पृष्ठ संख्या).

### Optional / Contextual Fields
- `executant` (Object): The party transferring the right. (Often omitted in JDA/Society allotments if the authority name is hardcoded).
- `consideration_amount` (String): Required for Sale Deeds and ATS.

## 4. Normalization Rules
- **Ordering**: Events MUST be sorted chronologically by `date`.
- **Script Consistency**: All textual values must be stored in **Unicode Hindi**, which will be converted to DevLys 040 during final rendering.
