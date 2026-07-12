# Spec: e-Panjiyan Automation Extension Design

This document details the updated automation design for the e-Panjiyan extension to handle the Document Details page and Stamp Duty Calculation steps using case data from the local RM-Maker app.

## Proposed Architecture & Flow

### 1. Document Details Autofill (`/PropertyValuation`)
When executing Document Details Autofill:
* **Location Type**: Programmatically ensure the radio option for "Urban (शहरी)" is checked.
* **Transfer Status**: Target `input#radioself` directly, check it, click it, and dispatch a change event to open the gender/category selection modal.
* **Gender/Category Selection Modal**:
  * Wait for the modal body to become visible in the DOM.
  * Map `data.gender_card` directly to the underlying radio inputs:
    * `MALE_GEN` $\rightarrow$ `input[name="individualdata"][value="1"]`
    * `FEMALE_GEN` $\rightarrow$ `input[name="individualdata"][value="3"]`
    * `JOINT` $\rightarrow$ `input[name="individualdata"][value="6"]`
  * Check and click the matching radio button, and dispatch a change event.
  * Wait 400ms, then click the modal continue button: `button[onclick*="setdatass"]`.
* **Select2 Dropdowns**: Target select elements directly by ID:
  * Document Type $\rightarrow$ `select#parentarticle_id`
  * SubType $\rightarrow$ `select#ddlDocSubType`
  * Category $\rightarrow$ `select#ddlCategory`
  * SRO $\rightarrow$ `select#ddlSRO`
  * Tehsil $\rightarrow$ `select#ddlTehsil`
* **Dropdown Option Selection**: Update the text matching in `setSelectValueByText` to include fallbacks for Hindi equivalents (e.g. mapping "Mortgage/ Charge" to "बंधक/भार").
* **Submit**: Click the save button `button#savedocument`, wait for the confirmation SweetAlert popup, and click OK.

### 2. Stamp Duty Calculation (`/PropertyValuation/PropertyDetail` and `/PropertyValuation/CalculateDuty`)
To prevent infinite navigation loops on the Property Detail page:
* Use a transient Chrome storage flag: `stampDutyCalculated` (boolean).
* **On `PropertyDetail` page**:
  * Check `chrome.storage.local` for `stampDutyCalculated`.
  * If `false` or not present: click the **Calculate Duty** button (`button[formaction*="/PropertyValuation/CalculateDuty"]`).
  * If `true`: click the **Party Detail** button (`button[formaction*="/Party/viewparty"]`) and remove the `stampDutyCalculated` flag from storage.
* **On `CalculateDuty` page**:
  * Set execution date in `input#execution_date` using the case execution date (or today's date formatted `dd-mm-yyyy`).
  * Set face value in `input#face_value` using the total loan amount from the case.
  * Click **Calculate & Save** (`input[type="submit"][value="Calculate & Save"]`).
  * Poll for the SweetAlert confirm button (OK). When clicked, write `stampDutyCalculated: true` to local storage, allowing the script to transition to Party Details on the next page load.

## Affected Components

### [content.js](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/extensions/epanjiyan_autofill/content.js)
* Update `autofillDetails` to use radio IDs and value mappings for the modal, target selects by ID directly, and use updated Select2 value selector.
* Update `autofillCalculateDuty` to check for `stampDutyCalculated` flag and handle routing/storage flag write.
* Update `setSelectValueByText` to support bilingual Hindi/English dropdown fallback matching.

## Verification Plan

### Manual Verification
1. Load the updated extension in Chrome (`chrome://extensions`).
2. Open the Rajasthan e-Panjiyan portal.
3. Select an active case in the extension popup.
4. Execute individual steps and one-click automation to verify:
   - Proper gender card is clicked in the Self category modal (Male, Female, or Joint).
   - Document Type, Subtype, Category, SRO, and Tehsil dropdowns are correctly set via Select2.
   - Execution date and summed face value are filled on the Calculate Stamp Duty page.
   - State transition from Calculate Duty to Party Details on the Property Detail page works without loops.
