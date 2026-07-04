# e-Panjiyan Sale Deed (SD) Mode Workflow Notes

This document logs the step-by-step requirements for the automated e-Panjiyan autofill process in **Sale Deed (SD)** Mode.

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
