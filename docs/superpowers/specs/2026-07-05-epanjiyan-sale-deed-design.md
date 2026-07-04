# Design Spec: e-Panjiyan Sale Deed (SD) Mode Automation

This design specification details the implementation plan for adding Sale Deed (SD) Mode automation to the e-Panjiyan Chrome extension.

## Proposed Changes

### 1. Document Details Form Automation (`content.js`)
* **Goal**: Automate the `/PropertyValuation` page in Sale Deed mode.
* **Mechanism**:
  * Set Location Type to Urban (`#radiourban` or equivalent).
  * Set Transfer Status to Self (`#radioself`).
  * In the Category/Gender selection modal:
    * Select `Female SC/ST/BPL` (card `4`) if the buyer is female and her caste is SC, ST, or BPL.
    * Select `Female other than SC/ST/BPL` (card `3`) if the buyer is female and general/OBC.
    * Select `Male/Female Joint` (card `6`) if the buyers are a joint male-female couple.
    * Select `Male (GEN)` (card `1`) if the buyer is male.
  * Set Document Type to `"Sale Deed (Conveyance)"` (`#parentarticle_id`).
  * Set SubType to `"Sale Deed"` (`#ddlDocSubType`).
  * Set Category Dropdown (`#ddlCategory`):
    * If female SC/ST/BPL $\rightarrow$ select `"Female SC/ST/BPL"`.
    * If female General/OBC $\rightarrow$ select `"Female other than SC/ST/BPL"`.
    * Otherwise $\rightarrow$ select `"General"`.
  * Set SRO (`#ddlSRO`) and Tehsil (`#ddlTehsil`) dynamically from case details.
  * Fill Service Provider fields:
    * Seva Pradata Name (`#sevaPradataName`): `"SANKALP LAW ASSOCIATES"`
    * Seva Pradata Mob. No. (`#sevaPradataMobile`): `"9799967384"`
  * Click Save (`#savedocument`).

### 2. Location Details & Property Address Form Automation (`content.js`)
* **Goal**: Automate the `/PropertyValuation/AddPropertyAddress` page.
* **Mechanism**:
  * **Property Type**: Select `"Plot"`, `"FLAT"`, or `"HOUSE"` based on construction/flat keywords or area flags.
  * **Colony**: Select SRO-level colony (`select#ddlColony`):
    * **Fuzzy Match (Typo-Resistant)**: Normalize both target and options (lowercase, remove spaces/special characters, strip suffixes like colony, road, nagar, scheme). If Jaro-Winkler/Levenshtein similarity is $\ge 85\%$, it's a match (handles e.g. "luv kush" vs "lav kush").
    * **Highest DLC Selection**: If multiple fuzzy matching options are found (e.g. main road vs sector options), the extension sequentially selects each, queries the loaded `Applicable DLC` value from the portal via AJAX, and submits the option yielding the highest DLC rate.
    * **Priority Hierarchy**:
      1. Highest DLC among fuzzy matched options.
      2. JDA Converted fallback (`"JDA Converted"` / `"जे.डी.ए. स्वीकृत"`).
      3. Manual fallback/user prompt if no matches.
  * **Plot No.**: Parse plot number string and split into `plotNo1` (Block/Sector), `plotNo2` (Number + slash), and `plotNo3` (Part/Suffix).
  * **Road Width**: Input road width in feet.
  * **Location**: Check `Interior` (`input[name="Location"][value="0"]` if road width $\le 30$ ft) or `Exterior` (`input[name="Location"][value="1"]` if road width $> 30$ ft).
  * **Property Area**: Input area in Square Meters (`input#txtPlotArea`). Convert from Square Yards if necessary (`gaj * 0.8361`).
  * **Latitude & Longitude**: Input coordinates from Technical Valuation Report (`input#latitude`, `input#longitude`).
  * **Boundaries**: Input East (`#east`), West (`#west`), North (`#north`), and South (`#south`) text descriptions.
  * **Intermediate Documents**: Always select `"No"` using `input#radiointermediateNo` (`isChainDocument="0"`).
  * Click Save (`input#btnsaveproperty`).

### 3. Calculation & Quotation Extraction (`content.js`)
* **Goal**: Extract the stamp duty calculation from the portal, send it to the backend database, and pause.
* **Mechanism**:
  * After the portal calculates the fees, the extension reads the breakdown table (Stamp Duty, Registration Fee, Surcharges, Total) and saves it to local storage.
  * Sends a background payload to the backend: `/api/case/<case_id>/save_valuation_quote` to store the calculated charges.
  * Pauses execution (`oneClickRunning = false`).

## Verification Plan

### Automated Tests
* Create unit tests in `tests/test_sd_valuation.py` asserting correct property type detection and plot splitting.

### Manual Verification
1. Run a test Sale Deed case in e-Panjiyan, verifying the SRO, Colony selection hierarchy, Seva Pradata fields, and boundary values are populated correctly.
2. Verify that the calculated charges are scraped and saved to the backend database session.
