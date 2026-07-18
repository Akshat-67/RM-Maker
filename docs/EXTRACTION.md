# AI Fact Extraction & Document Auto-Cropping

This document describes the design of the AI extraction adapters, page pre-filtering logic, multi-key rotation system, and the advanced Aadhaar auto-cropping pipeline.

---

## 1. AI Infrastructure & Key Rotation
All Gemini requests are routed through `services/ai_client.py`:
- **Multi-Key Failover**: Automatically rotates through up to 5 configured API keys (`GEMINI_API_KEY_1` to `GEMINI_API_KEY_5`) to avoid rate limits and keep batch extractions running without interruptions.
- **Failover Retries**: Retries network calls on transient API errors with exponential backoff.

---

## 2. PDF Page Pre-Filtering
Scanned legal reports can be extremely long (often exceeding 50 pages). To save tokens and run extractions efficiently:
- **Keyword Pre-filtering**: Extracts text from PDFs using `pypdf` and scans pages for legal keywords (e.g., plot numbers, boundaries, dimensions).
- **Critical Page Selection**: Selects and sends only the most relevant pages (up to 12 pages) to the Gemini model.

---

## 3. Advanced Multi-Candidate Aadhaar Auto-Cropping
The document auto-cropping pipeline in [services/autocrop.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/services/autocrop.py) isolates document cards from camera/scanner backgrounds:

### A. Candidate Localization (`cv2.RETR_TREE`)
- Uses tree-based contour extraction to track the relationships of shapes.
- If an outer card boundary is found, any nested inner contours (such as face portraits, QR codes, or text blocks) are penalized, preventing the cropper from cutting internal details.

### B. Normalized Geometric Scoring
Contours are scored on a scale from `0.0` to `1.0`:
$$\text{Score} = w_{\text{aspect}} \cdot S_{\text{aspect}} + w_{\text{solidity}} \cdot S_{\text{solidity}} + w_{\text{vertex}} \cdot S_{\text{vertex}} + w_{\text{edge}} \cdot S_{\text{edge}} + w_{\text{hierarchy}} \cdot S_{\text{hierarchy}}$$
- **Edge Support**: Calculates how well the candidate lines align with actual image edges on a dilated Canny edge map.

### C. Perspective Warping & Refinement
- Sorts candidate corners in clockwise order.
- Applies perspective transformation (`cv2.getPerspectiveTransform`) to straighten skewed scans.
- Performs a secondary contour pass to shave off leftover background edges.

### D. Guided GrabCut Fallback
- If contour matching fails, the crop initializes a GrabCut segmentation guided by the highest-scored candidate bounding box.

### E. Visual Debugging
- When `AUTOCROP_DEBUG=true` is enabled, the cropper saves 12 debug stages (original image, edges, contours, candidate scores table, and crop states) inside an `autocrop_debug_<basename>/` directory.
- Wrote `test_nested_subfolder_classification` to ensure subfolders (`kyc/`, `legal/`) in ingestion are supported recursively by matching relative paths.
