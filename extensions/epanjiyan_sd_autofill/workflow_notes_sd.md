# e-Panjiyan Sale Deed (SD) Mode Workflow Notes

This document logs the step-by-step requirements for the automated e-Panjiyan autofill process in **Sale Deed (SD)** Mode.

## Data Sources (LSR & Technical Reports)
Property details are extracted from:
1. **Legal Search Report (LSR)**: For property address, owner names, chain of title, and boundaries.
2. **Technical Valuation Report**: For exact plot area, construction area (if any), latitude/longitude coordinates, road width, SRO, Tehsil, and property photos.

## Property Type Detection Rules (Section 4.1 Underlying Select)
* **Plot**: Extracted plot area > 0 AND construction area is 0/empty. No flat/apartment keywords.
* **FLAT**: Flat/Apartment keywords detected in address (e.g. Flat, Apartment, Tower, Block) OR only super built-up/constructed area is present with 0 land plot area.
* **HOUSE**: Both plot area > 0 AND construction area > 0 are present.

## Step 1: District Selection & Navigation (Dashboard)
* **Action:** Click "+ Add New Valuation" (`#addnewproperty`), wait for the modal, select "JAIPUR" from the District dropdown (`#ddlDistrict`), and submit the modal.

## Step 2: Document Details Page (`/PropertyValuation`)
* **Action 2.1 (Location Type):** Ensure "Urban (शहरी)" is checked.
* **Action 2.2 (Transfer Status):** Click the **Self (स्वयं)** radio button (HTML: `input#radioself`).
* **Action 2.3 (Self Category Selection Modal):**
  * Check the purchaser(s) (claimants/buyers in Sale Deed) gender and caste.
  * **Option A**: If the purchaser is a **Female** and her caste is **SC or ST** (or BPL), select **Female SC/ST/BPL** card (HTML modal individualdata value: `4` or match text).
  * **Option B**: If the purchaser is a **Female** but her caste is General/OBC, select **Female other than SC/ST/BPL** card (HTML modal individualdata value: `3`).
  * **Option C**: If the purchaser is a **Male**, select **Male (GEN)** card (HTML modal individualdata value: `1`).
  * **Option D**: If the purchase is **Joint (Male & Female)**, select **Male/Female Joint** card (HTML modal individualdata value: `6`).
  * Click **Continue** button in the modal footer (`button[onclick*="setdatass"]`).
* **Action 2.4 (Document Type Dropdown):** Select **"Sale Deed (Conveyance)"** (`select#parentarticle_id`).
* **Action 2.5 (SubType Dropdown):** Select **"Sale Deed"** (`select#ddlDocSubType`).
* **Action 2.6 (Category Dropdown):**
  * If female SC/ST/BPL, select **"Female SC/ST/BPL"** (`select#ddlCategory`).
  * If female General/OBC, select **"Female other than SC/ST/BPL"** (`select#ddlCategory`).
  * Otherwise (Male / Joint), select **"General"** (`select#ddlCategory`).
* **Action 2.7 (SRO Dropdown):** Select the case SRO, e.g., **"JAIPUR-VII"** (`select#ddlSRO`).
* **Action 2.8 (Tehsil Dropdown):** Select the case Tehsil, e.g., **"JAIPUR"** (`select#ddlTehsil`).
* **Action 2.9 (Seva Pradata Name):** Populate `input#sevaPradataName` with `"SANKALP LAW ASSOCIATES"`.
* **Action 2.10 (Seva Pradata Mob. No.):** Populate `input#sevaPradataMobile` with `"9799967384"`.
* **Action 2.11 (Save Form):** Click **Save** button (`button#savedocument`).

## Step 3: Add Property Navigation (`/PropertyValuation/PropertyDetail`)
* **Action 3.1 (Click Add Property):** Find and click the **Add Property** button (HTML: `button[formaction="/PropertyValuation/AddPropertyAddress"]`).

## Step 4: Location Details / Property Address Form (`/PropertyValuation/AddPropertyAddress`)
This page is divided into multiple sections:

### Section 4.1: DLC Address
* **Property Type / संपत्ति का प्रकार**: (Dropdown)
* **Colony / कॉलोनी**: (Dropdown select element ID: `select#ddlColony` / Select2 styled wrapper `span#select2-ddlColony-container`)
  * **Fuzzy Typo-Resistant Matching**:
    * Clean both target name (from case) and option names (lowercase, remove spaces, special chars, and common suffixes like "colony", "nagar", "road", "gali", "scheme").
    * Compute string similarity (using Levenshtein or Jaro-Winkler). If score $\ge 85\%$, treat it as a potential match (resolves typos like `"luv kush"` vs `"lav kush"`).
  * **Highest DLC Selection Logic**:
    * If multiple options match the colony (e.g., `"Patrakar Colony Road"`, `"Patrakar Colony Sector"`), the extension will programmatically select each candidate option sequentially.
    * For each candidate, wait for the portal's AJAX request to finish, read the updated `Applicable DLC` value from the text input field, and compare.
    * Keep the colony option that yields the **highest DLC rate**.
  * **Selection Hierarchy**:
    1. Highest DLC among fuzzy colony matches.
    2. JDA Converted fallback (`"JDA Converted"` / `"जे.डी.ए. स्वीकृत"`).
    3. Manual override/prompt if no matches found.
* **Area / क्षेत्र**: (Auto-populated upon Colony selection)
* **Zone / जोन**: (Auto-populated upon Colony selection)
* **Category Type / श्रेणी का प्रकार**: (Dropdown select element ID: `select#ddlCategoryType` / Select2 wrapper `span#select2-ddlCategoryType-container`)
  * **Rule**: Always select **"Residential"** by default.
* **Location / स्थान**: (Radio buttons: Interior `input[name="Location"][value="0"]` / Exterior `input[name="Location"][value="1"]`)
  * **Rule**: Road width-dependent:
    * If road width next to property $\le 30\text{ ft} \rightarrow$ select **"Interior"** (value `"0"`).
    * If road width next to property $> 30\text{ ft} \rightarrow$ select **"Exterior"** (value `"1"`).
  * **Data Source**: Obtained from the boundaries (East/West/North/South) in the LSR, scanning for "Road" (or "सड़क") and its width.
* **Applicable DLC / लागू डीएलसी**: (Auto-populated or input)

### Section 4.2: Property Address
* **Plot No. / प्लॉट नं**: Three side-by-side inputs:
  * Element IDs: `input#plotNo1`, `input#plotNo2`, `input#plotNo3`.
  * **Splitting Heuristics**:
    * **Input 1 (`plotNo1`)**: Block / Sector (e.g. `"F"`, `"A"`, `"Sec-3"`). Extracted if the plot number starts with a block letter followed by a hyphen or space (like `"F-101"` $\rightarrow$ `plotNo1="F"`).
    * **Input 2 (`plotNo2`)**: Primary Plot Number (e.g. `"101 /"`). If the remaining plot number contains a slash (like `"101/200A"`), the part before the slash including the slash is set here (e.g. `"101 /"`).
    * **Input 3 (`plotNo3`)**: Suffix / Part / Flat Number (e.g. `"200A"`). The part after the slash is set here.
    * *Fallback*: If no complex patterns are found, leave `plotNo1` and `plotNo3` empty, and write the entire plot string to `plotNo2`.
* **Colony/Village / (कॉलोनी/गाँव)**: (Dropdown select element ID: `select#othercolonyvillage` / Select2: `span#select2-othercolonyvillage-container`)
  * **Rule**: Select the same colony name selected in Section 4.1.
* **City / (शहर)**: (Dropdown select element ID: `select#city` / Select2: `span#select2-city-container`)
  * **Rule**: Select the case city, e.g., `"JAIPUR"`.
* **Issuing Authority / जारी करने वाला प्राधिकरण**: (Dropdown)
* **Road Width / सड़क की चौड़ाई**: (Input in feet)
  * **Rule**: Set to the road width extracted from the boundary details.
* **Corner Plot / कॉर्नर प्लॉट**: (Radio: Yes / No)
  * **Rule**: Default to "No" unless specified otherwise.
* **Property Area / संपत्ति क्षेत्र**: (Input element ID: `input#txtPlotArea`)
  * **Rule**: Set to property area. If the value in the report is in **Square Yards (Gaj)**, convert it to **Square Meters** by multiplying by **0.8361** (e.g. `gaj * 0.8361`).
* **Other Detail / अन्य विवरण**: (Input)
* **Latitude & Longitude**: (Input element IDs: `input#latitude`, `input#longitude`)
  * **Rule**: Set to coordinates from the Technical Valuation Report. If missing/not available, default both values to `"0"`.
* **Property Id**: (Input)

### Section 4.3: Other Details & Boundaries
* **East / पूर्व**: (Input element ID: `input#east` / name `east`)
  * **Rule**: Set to East boundary description from the Legal Search Report.
* **West / पश्चिम**: (Input element ID: `input#west` / name `west`)
  * **Rule**: Set to West boundary description from the Legal Search Report.
* **North / उत्तर**: (Input element ID: `input#north` / name `north`)
  * **Rule**: Set to North boundary description from the Legal Search Report.
* **South / दक्षिण**: (Input element ID: `input#south` / name `south`)
  * **Rule**: Set to South boundary description from the Legal Search Report.
* **Intermediate Documents / मध्यवर्ती दस्तावेज़**: (Radio: Yes / No, ID: `input#radiointermediateNo`, name: `isChainDocument`, value: `"0"`, default "No")
* **Commission / कमीशन**: (Radios, default "N/A")
* **Save**: Click Save button at the bottom of the page (`input#btnsaveproperty`).

## Step 5: Calculate Duty Navigation (`/PropertyValuation/PropertyDetail`)
* **Action 5.1 (Click Calculate Duty):** Click the **Calculate Duty** button (HTML element: `button[formaction="/PropertyValuation/CalculateDuty"]` with class `"btn-success submit-btn"`).

## Step 6: Calculate Stamp Duty (`/PropertyValuation/CalculateDuty`)
* **Action 6.1 (Set Execution Date):** Programmatically select today's date in the read-only Execution Date input (`input#execution_date`).
* **Action 6.2 (Set Face Value):** Enter the **Consideration Amount / ATS Transaction Value** from the case data (instead of loan amount) in the Face Value input (`input#face_value`).
* **Action 6.3 (Calculate & Save):** Click **Calculate & Save** button (HTML input/button with value `"Calculate & Save"`).
