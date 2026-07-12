# LegalDoc Automator (RM-Maker) - V2.0

RM-Maker is a production-hardened legal document automation system designed to extract entity data from KYC files, manage template schedules, perform automated cross-document discrepancies checks, and compile Registered Mortgage (RM) and Sale Deed (SD) documents.

---

## 🏛️ Architecture Overview

The core pipeline follows this sequence:
```
Upload → Extraction → Schema Validation → Processing & Transliteration → Template Context Generation → docxtpl Rendering
```

### Key Subsystems:
1. **AI Extraction Subsystem:** Utilizes the new `google-genai` SDK and model adapters to perform structured fact extraction from PDFs and images.
2. **Verification Workspace:** An interactive 3-step GUI for reviewing entity fields, applying real-time transliteration, validating details, and structuring property title chains.
3. **Validation Framework:** Extensible, domain-oriented validators (e.g. Identity, Property, Title Chain) that run complex legal/format checks (e.g., Aadhaar Verhoeff checksums, duplicate identity markers).
4. **Optimistic Concurrency Engine:** Server-side locks and case revision checks to prevent data loss or silent overwrites in concurrent-user scenarios.
5. **e-Panjiyan Autofill Extension:** Integrated content-scripts that pull verified case data and auto-populate state registration portals.

---

## 🛠️ Feature Support

### Registered Mortgage (RM)
- Core RM entity mapping: Borrowers, Loans, Properties, Witnesses, Bank Signatories, and Document Schedules.
- Automatic formatting of currency values and ordinal dates.
- High stability and production-hardened pipeline compatibility.

### Sale Deed (SD)
- Sale Deed entity support: Sellers (`ss`), Buyers (`bs`), Witnesses (`ws`), and Properties (`ps`).
- Automatic timeline narrative compiler generating a chronological Hindi ownership history block using LLM synthesis.

---

## 🚦 Validation & Safety Framework

The V2.0 engine checks structural parameters before document compilation:
- **Identity Checks:** Verifies Aadhaar 12-digit format, validates Verhoeff checksums, executes PAN regex format validation, and flags duplicate PANs or Aadhaars across all parties.
- **Case Health Badges:** Renders real-time feedback (🟢 Ready, 🟡 Mismatches, 🔴 Blocked) to prevent compiling documents with invalid or unverified details.
- **Server Safety Gate:** Rejects compile requests via a strict server-side validation block if critical fields (such as buyer/seller names, execution dates, consideration amounts) are absent.

---

## 📂 Codebase Directory Structure

- `routes/`: Blueprint controllers managing cases, uploads, e-Panjiyan, and generation routes.
- `services/`: Core logic including session manager, compile safety gate, file storage services, e-Panjiyan integration, and the validation framework.
- `modules/`: Pipeline extractors, processors, schemas, and narrative builders segmented by domain:
  - `modules/rm/`: Stable Registered Mortgage modules.
  - `modules/sd/`: Sale Deed modules and timeline template narrative generators.
- `utils/`: Address splitters, Hindi font converter engines (DevLys 010 <-> Unicode), API configuration parameters, and common validation helpers.
- `extensions/`: Content scripts for Chrome/Firefox integrations.
- `templates/`: Categorized Word (`.docx`) template directories.

---

## 🚀 Installation & Setup

1. **Prerequisites:** Python 3.10+ and Node.js (for Playwright e2e checks).
2. **Python Setup:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment Setup:** Copy `.env.example` to `.env` and fill in your Gemini API keys:
   ```env
   GEMINI_API_KEY_1=your_key_here
   GEMINI_API_KEY_2=your_key_here
   ```
4. **Running the Application:**
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your web browser.

---

## 🧪 Testing and Verification Suite

### Pytest (Unit & Integration Tests)
Runs backend validations, revision counters, Verhoeff checksums, and template compiling:
```bash
pytest
```

### Playwright (E2E Browser Tests)
Validates UI updates, verification badges, conflict resolution dialogs, and keyboard mappings:
1. Install browsers:
   ```bash
   npx playwright install
   ```
2. Run tests:
   ```bash
   npx playwright test
   ```

---

## 🔄 Development Engineering Workflow

All future code contributions must follow the strict sequence outlined in `AGENTS.md`:
1. Review Serena memories and Rules.
2. Review Graphify knowledge representation.
3. Implement minimal changes respecting domain isolation.
4. Run Pytest suite & Playwright suite.
5. Verify zero regressions on RM and SD pipelines.
6. Regenerate Graphify database (`graphify update .`).
