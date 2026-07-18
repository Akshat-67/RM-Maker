# AI Fact Extraction & Document Auto-Cropping

This document describes the design of the AI extraction adapters, page pre-filtering logic, multi-key rotation system, and the advanced Aadhaar auto-cropping pipeline.

---

## 1. AI Infrastructure & Key Rotation
All Gemini requests are routed through `services/ai_client.py`:
- *For details on the separation of AI fact extraction and static template phrasing, see [ADR-0004: AI Extracts Facts, Templates Own Legal Language](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/adr/ADR-0004.md).*
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

## Preprocessing Pipeline Architecture

The document preprocessing pipeline (located primarily in `services/autocrop.py` and `services/orientation.py`) operates through a resilient, multi-layered approach to automatically crop, correct perspective, and orient document images before OCR:

1. **Geometry/Contour Detection:** The pipeline first uses OpenCV (Canny edges, Morphological closing) to locate distinct quadrilaterals matching known document aspect ratios (Aadhaar/PAN, A4, US Letter).
2. **Perspective Warping:** The highest-scoring valid contour is used to perspective-warp the image back into a clean, flat scan.
3. **GrabCut Fallback:** If contour detection fails (e.g., due to background clutter or poor contrast), the pipeline falls back to an edge-directed `cv2.grabCut` mask to extract the document.
4. **Validation:** Cropped results are passed through `services.crop_validation` which analyzes minimum resolution, retained area ratio, and aspect ratio. If the crop is bad, it gracefully falls back to the original image.
5. **Orientation Correction:** Finally, `pytesseract` OSD detects the rotational orientation of the cropped document (0, 90, 180, 270 degrees) and correctly rotates it upright for maximum OCR reliability.
6. **VLM Fallback:** If local OpenCV heuristics completely fail, a Gemini Vision language model is queried to estimate the document bounding box as a last resort.
