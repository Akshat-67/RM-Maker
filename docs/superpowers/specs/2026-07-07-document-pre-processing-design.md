# Design Spec: Document Pre-processing (Page Selection) Pipeline

This document describes the design for implementing local PDF pre-processing in the RM-Maker extraction engine. It reduces token consumption, minimizes API costs, and accelerates Gemini processing times by filtering multi-page PDFs to only the relevant pages before sending them to the Gemini API.

## 1. Objectives & Key Rules
- **Hybrid Page Selection**: For multi-page PDFs, always include:
  - Page 1 & 2 (indices 0 and 1) - contains primary party names and execution dates.
  - The last page - contains signatures, stamps, and SRO registry details.
  - Any middle pages containing relevant keywords.
- **Capping**: Limit the final PDF/text context to a maximum of **5 pages**.
- **Scanned PDF Fallback**: If a PDF contains no extractable text, fallback to sending the entire PDF (Approach 1).
- **Text-Mode Optimization**: If the PDF is searchable, extract the raw text of the selected pages locally and send it as a plain-text payload to Gemini instead of the heavy binary file.

---

## 2. Proposed Changes

### Dependencies
Add `pypdf` to `requirements.txt` to handle PDF reading and writing.

### Extractor Modules

#### [MODIFY] [extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/extractor.py)
Update `_run_gemini_extraction` to pre-process PDFs:
1. If the file is a PDF:
   - Try to open and parse pages with `pypdf.PdfReader`.
   - If no text is extractable across all pages, fallback to sending the entire PDF file bytes.
   - If text is extractable:
     - Scan each page for target keywords based on the bucket type (e.g. KYC, title chain, legal).
     - Run the Hybrid Selection algorithm (pages 0, 1, last_page + matching pages, capped at 5).
     - Extract the raw text from those selected pages.
     - Send the combined plain-text string directly to the Gemini API.

#### [MODIFY] [extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/extractor.py)
Apply the same pre-processing/filtering optimization inside the RM extractor's extraction helper.

---

## 3. Verification Plan

### Automated Tests
* Create a test file `tests/test_pdf_processing.py` to verify the page selection algorithm and text extraction logic on sample dummy PDF data.

### Manual Verification
* Run a full AI extraction on a multi-page searchable PDF case and verify in logs that only selected page texts are sent to the API.
