# e-Panjiyan Automation Flow Notes

This document logs the step-by-step requirements for the automated e-Panjiyan autofill process as described by the user.

## Current Workflow Steps

### Step 1: District Selection & Navigation (Dashboard)
* **Action:** Click "+ Add New Valuation" (`#addnewproperty`), wait for the modal, select "JAIPUR" from the District dropdown (`#ddlDistrict`), and submit the modal.
* **Status:** Already automated and successfully executing.

### Step 2: Document Details Page (`/PropertyValuation`)
* **Action 2.1 (Location Type):** Ensure "Urban (शहरी)" is selected (it should always be on Urban).
* **Action 2.2 (Transfer Status):** As soon as the page loads, immediately click the **Self (स्वयं)** radio button (HTML element: `input#radioself`).
* **Action 2.3 (Self Category Modal):** Selecting "Self" displays the gender/category popup modal.
* **Action 2.4 (Gender Selection):** Based on the mortgagors' gender from the active case:
  * If **Male** only, select **General Male (पुरुष (GEN))** (HTML: `input[name="individualdata"][value="1"]`).
  * If **Female** only, select **General Female (महिला (GEN))** (HTML: `input[name="individualdata"][value="3"]`).
  * If **both Male and Female** (Joint), select **Male/Female Joint (पुरूष/महिला संयुक्त)** (HTML: `input[name="individualdata"][value="6"]`).
  * *Note:* Avoid all other SC/ST, BPL, or Disability options.
* **Action 2.5 (Continue Modal):** Once the correct category/gender card is selected, click the **Continue** button in the modal footer (HTML element: `button` with text `Continue` and `onclick="return setdatass()"`).
* **Action 2.6 (Document Type Dropdown):** Click the **Document Type (दस्तावेज़ का प्रकार)** dropdown (HTML underlying select: `select#parentarticle_id`, styled via Select2) and select the option matching **"Mortgage/ Charge"** (Hindi: "बंधक/भार").
* **Action 2.7 (SubType Dropdown):** Click the **SubType (उप-प्रकार)** dropdown (HTML underlying select: `select#ddlDocSubType`, styled via Select2) and select the option matching **"(b)Mortgage deed without possession"**.
* **Action 2.8 (Category Dropdown):** Click the **Category (श्रेणी)** dropdown (HTML underlying select: `select#ddlCategory`, styled via Select2) and select the option matching **"General"**.
* **Action 2.9 (SRO Dropdown):** Click the **SRO (उप पंजीयक)** dropdown (HTML underlying select: `select#ddlSRO`, styled via Select2) and select the option matching the active case SRO, e.g., **"JAIPUR-VII"** (or fallback to case value).
* **Action 2.10 (Tehsil Dropdown):** Click the **Tehsil (तहसील)** dropdown (HTML underlying select: `select#ddlTehsil`, styled via Select2) and select the option matching the active case Tehsil, e.g., **"JAIPUR"** (or fallback to case value).
* **Action 2.11 (Save Form):** Click the **Save** button at the bottom of the page (HTML element: `button#savedocument`).

## Step 3: Calculate Stamp Duty

### Page: Property Detail (`/PropertyValuation/PropertyDetail`)
* **Action 3.1 (Go to Calculate Duty):** Click the **Calculate Duty** button (HTML element: `button[formaction*="/PropertyValuation/CalculateDuty"]` or matching text "Calculate Duty" / "ड्यूटी की गणना करें").

### Page: Calculate Stamp Duty (`/PropertyValuation/CalculateDuty`)
* **Action 3.2 (Set Execution Date):** Select/enter today's date in the **Execution Date** field (HTML: `input#execution_date`). Since the field is `readonly`, programmatically select today's date (which is highlighted in yellow in the datepicker modal, e.g., click `td.ui-datepicker-today a` or set date via input value and trigger change event).
* **Action 3.3 (Set Face Value):** Sum up all loan amounts from the loaded case (if multiple exist) and enter the total final amount in the **Face Value** field (HTML element: `input#face_value` or labeled "Face Value").
* **Action 3.4 (Calculate & Save):** Click the **Calculate & Save** button (HTML element: `input[type="submit"][value="Calculate & Save"]` or `button`/`input` containing text "Calculate & Save" / "गण्ना और सहेजें").
* **Action 3.5 (Go to Party Details):** After saving, when redirected back to the Property Detail page (`/PropertyValuation/PropertyDetail`), click the **Party Detail** button (HTML element: `button[formaction*="/Party/viewparty"]` or matching text "Party Detail" / "पक्षकार विवरण") to move to the party details stage.
