# e-Panjiyan Sale Deed (SD) Mode Valuation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and integrate Sale Deed (SD) Mode property valuation automation on e-Panjiyan, including fuzzy colony matching, highest-DLC comparative selection, and unit conversions.

**Architecture:** Extend the existing chrome extension `content.js` state machine to support SD mode. The script will fill `/PropertyValuation` and `/PropertyValuation/AddPropertyAddress` pages using case data, matching names fuzzy-style, comparing DLC rates programmatically, and saving extracted calculations back to the Python backend case session.

**Tech Stack:** JavaScript (DOM, Chrome Extension API), Python (Flask/FastAPI backend).

## Global Constraints
- Devanagari numerals (`०-९`) must always be converted to standard English digits (`0-9`).
- Legacy non-Unicode fonts (such as `DevLys 010` or `Kruti Dev`) must **never** be used to style text inputs or textareas in the browser.
- Real-time English-to-Hindi transliteration workflow must remain intact.
- Do not modify KYC and Relation Extraction parsing pipelines without consent.

---

### Task 1: Document Details Page (`/PropertyValuation`) in SD Mode

**Files:**
- Modify: `extensions/epanjiyan_autofill/content.js`

**Interfaces:**
- Consumes: Case data from backend (`amount`, SRO, Tehsil, purchasers' genders/castes).
- Produces: Fills `/PropertyValuation` page and submits.

- [ ] **Step 1: Write SD Category Selection logic in content.js**
  Implement category detection helper:
  ```javascript
  function determineSDCategory(caseData) {
      // Determine based on purchaser gender/caste
      const isFemale = caseData.gender === 'female';
      const isSCSTBPL = caseData.caste === 'SC' || caseData.caste === 'ST' || caseData.isBPL;
      if (isFemale && isSCSTBPL) return '4'; // Female SC/ST/BPL card
      if (isFemale) return '3'; // Female other than SC/ST/BPL card
      if (caseData.isJoint) return '6'; // Male/Female Joint card
      return '1'; // Male (GEN) card
  }
  ```
- [ ] **Step 2: Automate Document Details fields**
  Add conditions in `content.js` for Sale Deed Mode:
  - Select "Self" radio: `document.getElementById('radioself').click()`.
  - In Category modal: click the card matching the value returned by `determineSDCategory(caseData)`.
  - Select Document Type: `"Sale Deed (Conveyance)"` (value matching target select option).
  - Select SubType: `"Sale Deed"` (value matching target select option).
  - Select Category dropdown: `"Female SC/ST/BPL"`, `"Female other than SC/ST/BPL"`, or `"General"`.
  - Select SRO and Tehsil matching case.
  - Fill Seva Pradata Name: `"SANKALP LAW ASSOCIATES"` (`#sevaPradataName`).
  - Fill Seva Pradata Mob: `"9799967384"` (`#sevaPradataMobile`).
  - Click Save: `#savedocument`.
- [ ] **Step 3: Test and Commit**
  Run manual verification on the Document Details page and commit.
  ```bash
  git add extensions/epanjiyan_autofill/content.js
  git commit -m "feat: implement e-Panjiyan Sale Deed document details filling"
  ```

---

### Task 2: Add Property Address Page (`/PropertyValuation/AddPropertyAddress`) in SD Mode

**Files:**
- Modify: `extensions/epanjiyan_autofill/content.js`

**Interfaces:**
- Consumes: Property details from case data (colony, plot number, area, boundaries, road width, lat/long).
- Produces: Auto-fills `/PropertyValuation/AddPropertyAddress` form and clicks Save.

- [ ] **Step 1: Implement String Fuzzy Matching and Colony Search**
  Add a Jaro-Winkler or Levenshtein distance string similarity function to clean strings and compare.
  If similarity $\ge 85\%$, matching colony option is added to candidates.
- [ ] **Step 2: Implement Highest DLC Selection algorithm**
  Loop through candidate fuzzy-matched colony options, select each, wait for the portal's AJAX completion, read `#txtDLC` (or the returned DLC text input), keep the option with the highest rate, and finally select that option.
- [ ] **Step 3: Implement Plot Number splitting logic**
  Split plot number:
  - `plotNo1` (Block/Sector prefix).
  - `plotNo2` (Primary number with slash).
  - `plotNo3` (Part/Suffix).
- [ ] **Step 4: Automate rest of the Location Details form**
  - Category Type: Select `"Residential"` (`select#ddlCategoryType`).
  - Location: Select `"Interior"` (value `"0"`) if road width $\le 30$ ft, else `"Exterior"` (value `"1"`).
  - Property Area: Convert Gaj to Sq Meters (`gaj * 0.8361`) and write to `input#txtPlotArea`.
  - Coordinates: Set `input#latitude` and `input#longitude`. Fallback to `"0"` if missing.
  - Boundaries: Fill `input#east`, `input#west`, `input#north`, and `input#south`.
  - Intermediate Documents: Select `"No"` via `input#radiointermediateNo`.
  - Save: Click `input#btnsaveproperty`.
- [ ] **Step 5: Test and Commit**
  Run manual verification on Add Property Address page and commit.
  ```bash
  git add extensions/epanjiyan_autofill/content.js
  git commit -m "feat: implement location details and property address automation with fuzzy colony and highest DLC selection"
  ```

---

### Task 3: Calculate Stamp Duty Page Automation

**Files:**
- Modify: `extensions/epanjiyan_autofill/content.js`

**Interfaces:**
- Consumes: ATS Consideration Amount (`amount`) and execution date details from case data.
- Produces: Submits the calculation parameters and triggers the fee summary generation.

- [ ] **Step 1: Automate Calculate Duty navigation**
  On `/PropertyValuation/PropertyDetail`, find and click the **Calculate Duty** button:
  `document.querySelector('button[formaction="/PropertyValuation/CalculateDuty"]').click()`.
- [ ] **Step 2: Automate Calculate Stamp Duty parameters**
  On `/PropertyValuation/CalculateDuty`:
  - Set Execution Date: Programmatically select today's date in `input#execution_date`.
  - Set Face Value: Write the case's **ATS Consideration Amount** (`amount`) into `input#face_value`.
  - Click Calculate & Save: `document.querySelector('input[type="submit"][value="Calculate & Save"]').click()`.
- [ ] **Step 3: Test and Commit**
  Run manual verification and commit.
  ```bash
  git add extensions/epanjiyan_autofill/content.js
  git commit -m "feat: implement Calculate Stamp Duty navigation and fields using ATS consideration amount"
  ```

---

### Task 4: Quotation Scraping and State Pausing

**Files:**
- Modify: `extensions/epanjiyan_autofill/content.js`
- Modify: `app.py`

- [ ] **Step 1: Extract calculation table**
  On the valuation calculation summary page, scrape:
  - Stamp Duty
  - Registration Fees
  - Cesses/Surcharges
  - Total Fee
- [ ] **Step 2: Send data to Python backend case session**
  Use `fetch` to POST the quote values to backend: `/api/case/<case_id>/save_valuation_quote`.
  Update `app.py` to save these charges into the case database.
- [ ] **Step 3: Pause state and clear automation**
  Set `oneClickRunning = false` and show an alert/toast indicating valuation estimation is complete and quotation is saved.
- [ ] **Step 4: Test and Commit**
  ```bash
  git add extensions/epanjiyan_autofill/content.js app.py
  git commit -m "feat: implement stamp duty quotation scraping, database saving, and automation pause state"
  ```
