# e-Panjiyan Sale Deed (SD) Mode Valuation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a separate chrome extension under `extensions/epanjiyan_sd_autofill/` to automate Sale Deed (SD) Mode property valuation on e-Panjiyan, including fuzzy colony matching, highest-DLC comparative selection, and unit conversions.

**Architecture:** Initialize a brand new Chrome extension specifically for SD mode to avoid code regression in the RM extension. The extension will scrape property details from LSR & Technical valuation reports, match colony names fuzzy-style, compare DLC rates programmatically, and save extracted calculations back to the Python backend case session.

**Tech Stack:** JavaScript (DOM, Chrome Extension API), Python (Flask/FastAPI backend).

## Global Constraints
- Devanagari numerals (`०-९`) must always be converted to standard English digits (`0-9`).
- Legacy non-Unicode fonts (such as `DevLys 010` or `Kruti Dev`) must **never** be used to style text inputs or textareas in the browser.
- Real-time English-to-Hindi transliteration workflow must remain intact.
- Do not modify KYC and Relation Extraction parsing pipelines without consent.

---

### Task 1: Extension Scaffolding and Setup

**Files:**
- Create: `extensions/epanjiyan_sd_autofill/manifest.json`
- Create: `extensions/epanjiyan_sd_autofill/popup.html`
- Create: `extensions/epanjiyan_sd_autofill/popup.js`
- Create: `extensions/epanjiyan_sd_autofill/content.js`
- Create: `extensions/epanjiyan_sd_autofill/workflow_notes_sd.md`
- Delete: `extensions/epanjiyan_autofill/workflow_notes_sd.md`

**Interfaces:**
- Consumes: None (setup task).
- Produces: A functional, isolated Chrome extension ready for SD automation.

- [ ] **Step 1: Create manifest.json**
  Define manifest version 3 with name "e-Panjiyan Sale Deed Autofill".
- [ ] **Step 2: Create popup.html and popup.js**
  Implement the trigger popup UI with case details list and a "Start One-Click Autofill" button.
- [ ] **Step 3: Create content.js base scaffolding**
  Copy the common helper functions (element selections, events trigger, date utils) from `extensions/epanjiyan_autofill/content.js` into the new `content.js`.
- [ ] **Step 4: Relocate workflow notes**
  Copy the contents of `extensions/epanjiyan_autofill/workflow_notes_sd.md` to `extensions/epanjiyan_sd_autofill/workflow_notes_sd.md` and delete the old file.
- [ ] **Step 5: Test and Commit**
  Verify the new extension loads successfully in developer mode and commit.
  ```bash
  git rm extensions/epanjiyan_autofill/workflow_notes_sd.md
  git add extensions/epanjiyan_sd_autofill/
  git commit -m "chore: scaffold separate e-Panjiyan Sale Deed autofill extension"
  ```

---

### Task 2: Document Details Page (`/PropertyValuation`) in SD Mode

**Files:**
- Modify: `extensions/epanjiyan_sd_autofill/content.js`

**Interfaces:**
- Consumes: Case data from backend (`amount`, SRO, Tehsil, purchasers' genders/castes).
- Produces: Fills `/PropertyValuation` page and submits.

- [ ] **Step 1: Write SD Category Selection logic**
  Implement category detection helper:
  ```javascript
  function determineSDCategory(caseData) {
      const isFemale = caseData.gender === 'female';
      const isSCSTBPL = caseData.caste === 'SC' || caseData.caste === 'ST' || caseData.isBPL;
      if (isFemale && isSCSTBPL) return '4'; // Female SC/ST/BPL card
      if (isFemale) return '3'; // Female other than SC/ST/BPL card
      if (caseData.isJoint) return '6'; // Male/Female Joint card
      return '1'; // Male (GEN) card
  }
  ```
- [ ] **Step 2: Automate Document Details fields**
  - Select "Self" radio: `document.getElementById('radioself').click()`.
  - In Category modal: click the card matching the value returned by `determineSDCategory(caseData)`.
  - Select Document Type: `"Sale Deed (Conveyance)"` (`#parentarticle_id`).
  - Select SubType: `"Sale Deed"` (`#ddlDocSubType`).
  - Select Category dropdown: `"Female SC/ST/BPL"`, `"Female other than SC/ST/BPL"`, or `"General"` (`#ddlCategory`).
  - Select SRO and Tehsil matching case.
  - Fill Service Provider fields:
    - Seva Pradata Name (`#sevaPradataName`): `"SANKALP LAW ASSOCIATES"`
    - Seva Pradata Mob (`#sevaPradataMobile`): `"9799967384"`
  - Click Save: `#savedocument`.
- [ ] **Step 3: Test and Commit**
  Run manual verification on Document Details page and commit.
  ```bash
  git add extensions/epanjiyan_sd_autofill/content.js
  git commit -m "feat: implement e-Panjiyan SD document details automation"
  ```

---

### Task 3: Add Property Address Page (`/PropertyValuation/AddPropertyAddress`) in SD Mode

**Files:**
- Modify: `extensions/epanjiyan_sd_autofill/content.js`

**Interfaces:**
- Consumes: Property details from case data (colony, plot number, area, boundaries, road width, lat/long).
- Produces: Auto-fills `/PropertyValuation/AddPropertyAddress` form and clicks Save.

- [ ] **Step 1: Implement String Fuzzy Matching and Colony Search**
  Add string similarity function. Normalize both inputs (lowercase, strip spaces/symbols/common suffixes) and match with similarity $\ge 85\%$.
- [ ] **Step 2: Implement Highest DLC Selection algorithm**
  Loop matching colony dropdown options, select sequentially, wait for AJAX load, compare read DLC rates, and finaly keep the highest rate option.
- [ ] **Step 3: Implement Plot Number splitting logic**
  Split plot number string to `plotNo1` (Block/Sector prefix), `plotNo2` (Primary number with slash), and `plotNo3` (Part/Suffix).
- [ ] **Step 4: Automate rest of the Location Details form**
  - Category Type: Select `"Residential"` (`select#ddlCategoryType`).
  - Location: Select `"Interior"` (`input[name="Location"][value="0"]`) if road width $\le 30$ ft, else `"Exterior"` (`input[name="Location"][value="1"]`).
  - Property Area: Convert Gaj to Sq Meters (`gaj * 0.8361`) and write to `input#txtPlotArea`.
  - Coordinates: Set `input#latitude` and `input#longitude`. Fallback to `"0"` if missing.
  - Boundaries: Fill `input#east`, `input#west`, `input#north`, and `input#south`.
  - Intermediate Documents: Select `"No"` via `input#radiointermediateNo` (`isChainDocument="0"`).
  - Save: Click `input#btnsaveproperty`.
- [ ] **Step 5: Test and Commit**
  Run manual verification on Add Property Address page and commit.
  ```bash
  git add extensions/epanjiyan_sd_autofill/content.js
  git commit -m "feat: implement location details and property address automation with fuzzy colony and highest DLC selection"
  ```

---

### Task 4: Calculate Stamp Duty Page Automation

**Files:**
- Modify: `extensions/epanjiyan_sd_autofill/content.js`

**Interfaces:**
- Consumes: ATS Consideration Amount (`amount`) and execution date details from case data.
- Produces: Submits the calculation parameters and triggers the fee summary generation.

- [ ] **Step 1: Automate Calculate Duty navigation**
  On `/PropertyValuation/PropertyDetail`, click **Calculate Duty** button (`button[formaction="/PropertyValuation/CalculateDuty"]`).
- [ ] **Step 2: Automate Calculate Stamp Duty parameters**
  On `/PropertyValuation/CalculateDuty`:
  - Set Execution Date: Programmatically select today's date in `input#execution_date`.
  - Set Face Value: Write the case's **ATS Consideration Amount** (`amount`) into `input#face_value`.
  - Click Calculate & Save: `document.querySelector('input[type="submit"][value="Calculate & Save"]').click()`.
- [ ] **Step 3: Test and Commit**
  Run manual verification and commit.
  ```bash
  git add extensions/epanjiyan_sd_autofill/content.js
  git commit -m "feat: implement Calculate Stamp Duty navigation and fields using ATS consideration amount"
  ```

---

### Task 5: Quotation Scraping and State Pausing

**Files:**
- Modify: `extensions/epanjiyan_sd_autofill/content.js`
- Modify: `app.py`

- [ ] **Step 1: Extract calculation table**
  On the valuation calculation summary page, scrape:
  - Stamp Duty
  - Registration Fees
  - Cesses/Surcharges
  - Total Fee
- [ ] **Step 2: Send data to Python backend case session**
  POST the quote values to backend: `/api/case/<case_id>/save_valuation_quote`.
  Update `app.py` to save these charges into the case database.
- [ ] **Step 3: Pause state and clear automation**
  Set `oneClickRunning = false` and show an alert/toast indicating valuation estimation is complete.
- [ ] **Step 4: Test and Commit**
  ```bash
  git add extensions/epanjiyan_sd_autofill/content.js app.py
  git commit -m "feat: implement stamp duty quotation scraping, database saving, and automation pause state"
  ```
