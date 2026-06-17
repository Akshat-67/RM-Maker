# SD Runtime Schema

This document details all the fields that are actually populated and available in the execution context during Sale Deed (SD) template generation. These variables are constructed from case data and parsed on-the-fly.

## Scalar Fields

* **`rd`**: Execution Date of the deed (formatted as `DD.MM.YYYY`, defaults to today's date).
* **`amount`**: Consideration amount in digits (formatted currency string, e.g., `"20,00,000"`).
* **`amount_words`**: Consideration amount in Unicode Hindi words (e.g., `"वीस लाख रुपये मात्र"`).
* **`hypothecation`**: Existing mortgage bank name (e.g., `"Home First Finance Company India Limited"`).
* **`chain_text`**: Pre-rendered chronological title history narrative block in Hindi prose.

## Entities & Lists

### `ss` (Sellers)
An array of seller objects. Each object contains the following fields:
* **`n`**: Name (Unicode Hindi).
* **`a`**: Age.
* **`c`**: Caste (Unicode Hindi).
* **`r`**: Relation type abbreviation (e.g., `"iqr Jh"` / `"Son of"` or `"iRuh Jh"` / `"Wife of"`, parsed on-the-fly from `relation_text`).
* **`rn`**: Relative Name (Unicode Hindi, parsed on-the-fly from `relation_text`).
* **`adr`**: Seller's Residential Address.
* **`id`**: Aadhaar Number.
* **`pan`**: PAN Number.
* **`relation_text`**: Consolidated relation phrase (e.g., `"पुत्र श्री भीवा राम"`).

### `bs` (Buyers)
An array of buyer objects. Each object contains the following fields:
* **`s`**: Salutation prefix (e.g., `"Mr."`, `"Mrs."`, parsed on-the-fly from `n`).
* **`n`**: Name (Unicode Hindi).
* **`a`**: Age.
* **`c`**: Caste (Unicode Hindi).
* **`r`**: Relation type abbreviation (parsed on-the-fly from `relation_text`).
* **`rn`**: Relative Name (Unicode Hindi, parsed on-the-fly from `relation_text`).
* **`adr`**: Buyer's Residential Address.
* **`id`**: Aadhaar Number.
* **`pan`**: PAN Number.
* **`relation_text`**: Consolidated relation phrase (e.g., `"पुत्री श्री रामअवतार मीणा"`).

### `ps` (Properties)
An array containing property objects (typically 1 for SD). Each object contains:
* **`adr`**: Raw property address.
* **`plot_no`**: Plot/Flat Number.
* **`scheme`**: Scheme Name.
* **`village`**: Village Name.
* **`tehsil`**: Tehsil Name.
* **`dist`**: District Name.
* **`land_area`**: Land Area (digits).
* **`const_area`**: Construction Area (digits).
* **`unit`**: Area Unit (e.g., `"वर्ग गज"`).
* **`n`**: North boundary description.
* **`s`**: South boundary description.
* **`e`**: East boundary description.
* **`w`**: West boundary description.
* **`ward`**: Ward Name.
* **`state`**: State Name (defaults to `"राजस्थान"`).
* **`khasra`**: Khasra Number.
* **`length_ew`**: Dimensions East-West.
* **`length_ns`**: Dimensions North-South.
* **`full_address`**: Dynamically compiled formal Hindi address (stripped of leading residential qualifiers).
* **`dimension_text`**: Dynamically compiled dimensions/area sentence in Hindi.
* **`boundary_text`**: Dynamically compiled boundary block in Hindi.

### `ws` (Witnesses)
An array of witness objects (typically 2). Each object contains:
* **`n`**: Witness Name.
* **`relation_text`**: Consolidated relation phrase (e.g., `"पुत्र श्री रामेश्वर प्रसाद"`).
* **`r`**: Relation type abbreviation (parsed on-the-fly from `relation_text`).
* **`rn`**: Relative Name (parsed on-the-fly from `relation_text`).
* **`adr`**: Residential Address.

### `title_chain` (Chronological Chain Records)
An array of ownership transfer records extracted from the TSR. Each record contains:
* **`event_type`**: Type of transfer event (e.g., `"ALLOTMENT"`, `"SALE_DEED"`, `"POA"`, `"RELINQUISHMENT"`).
* **`document_name`**: Hindi translation of the document name.
* **`date`**: Event date (dots formatted, e.g. `11.07.2019`).
* **`consideration_amount`**: Currency digits.
* **`executant_name`**: Seller/Principal in Hindi.
* **`claimant_name`**: Buyer/Allottee in Hindi.
* **`reg_office`**: Sub-Registrar Office name.
* **`reg_date`**: Registration date.
* **`reg_book`**: Registry Book number.
* **`reg_vol`**: Registry Volume number.
* **`reg_page`**: Registry Page number.
* **`reg_no`**: Registry serial registration number.
* **`reg_add_book`**: Additional Book number.
* **`reg_add_vol`**: Additional Volume number.
* **`reg_add_page`**: Additional Page number.
* **`is_registered`**: Boolean registration flag.
* **`confidence`**: Confidence rating (`"High"`, `"Medium"`, `"Low"`).
* **`source_text`**: TSR source context.

### `reg` (Registration Details of the Current Deed)
Global registration dictionary containing:
* **`office`**: Sub-Registrar Office name.
* **`reg_date`**: Registration date.
* **`book`**: Registry Book number.
* **`vol`**: Registry Volume number.
* **`page`**: Registry Page number.
* **`reg_no`**: Registry serial registration number.
