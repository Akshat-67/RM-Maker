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
  * **Selection Hierarchy**:
    1. Search options for the exact colony name match (e.g. `"Patrakar Colony"`).
    2. If not found, search for `"JDA Converted"` / `"जे.डी.ए. स्वीकृत"` options.
    3. If still not found, search for the nearest zone, sector, or landmark, or prompt the user for manual override.
* **Area / क्षेत्र**: (Auto-populated upon Colony selection)
* **Zone / जोन**: (Auto-populated upon Colony selection)
* **Category Type / श्रेणी का प्रकार**: (Dropdown select element ID: `select#ddlCategoryType` / Select2 wrapper `span#select2-ddlCategoryType-container`)
  * **Rule**: Always select **"Residential"** by default.
* **Location / स्थान**: (Radio buttons)
  * **Rule**: Road width-dependent:
    * If road width next to property $\le 30\text{ ft} \rightarrow$ select **"Interior"** (आंतरिक) radio button.
    * If road width next to property $> 30\text{ ft} \rightarrow$ select **"Exterior"** (बाहरी) radio button.
  * **Data Source**: Obtained from the boundaries (East/West/North/South) in the LSR, scanning for "Road" (or "सड़क") and its width.
* **Applicable DLC / लागू डीएलसी**: (Auto-populated or input)

### Section 4.2: Property Address
* **Plot No. / प्लॉट नं**: Three side-by-side inputs
* **Colony/Village / कॉलोनी/गाँव**: (Dropdown)
* **Issuing Authority / जारी करने वाला प्राधिकरण**: (Dropdown)
* **Road Width / सड़क की चौड़ाई**: (Input in feet)
* **Corner Plot / कॉर्नर प्लॉट**: (Radio: Yes / No)
* **Property Area / संपत्ति क्षेत्र**: (Input)
* **Other Detail / अन्य विवरण**: (Input)
* **City / शहर**: (Dropdown / Input)
* **Latitude & Longitude**: (Inputs)
* **Property Id**: (Input)

### Section 4.3: Other Details & Boundaries
* **East / पूर्व**: (Input)
* **West / पश्चिम**: (Input)
* **North / उत्तर**: (Input)
* **South / दक्षिण**: (Input)
* **Intermediate Documents / मध्यवर्ती दस्तावेज़**: (Radio: Yes / No, default No)
* **Commission / कमीशन**: (Radios, default N/A)
* **Save**: Click Save button at the bottom of the page.

