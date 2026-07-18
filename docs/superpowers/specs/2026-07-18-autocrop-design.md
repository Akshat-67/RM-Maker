# Spec - Automatic Aadhaar Image Cropping

We are adding an automatic, background-level image cropping feature for uploaded Aadhaar cards to clean up photos that contain fingers, borders, or irrelevant backgrounds. This is executed during the case file ingestion phase, ensuring downstream AI extraction runs on cropped, high-quality images.

---

## 1. Problem & Context
When users upload photos of Aadhaar cards (e.g. from mobile phones), the images often include significant background area, hands holding the card, or other documents. Downstream Gemini models perform much better when extracting text from pre-cropped document images. 
Traditional OpenCV contour/quadrilateral detection fails to handle rotation, low contrast, and complex backgrounds. Visual Language Models (VLMs) are much more robust.

---

## 2. Proposed Architecture

### Core Pipeline Integration
The cropping process will run synchronously inside `services/ingestion_pipeline.py` right after the EXIF auto-rotation step. 

```
Upload Files → Ingestion Thread → EXIF Auto-Rotate → Autocrop via NIM → AI Extraction
```

### Components
1. **NIM Bounding Box Detector**:
   - Query `meta/llama-3.2-90b-vision-instruct` on NVIDIA NIM.
   - Send the base64-encoded image and request normalized bounding box coordinates: `[ymin, xmin, ymax, xmax]` on a 0-1000 scale.
2. **Crop & Backup Engine**:
   - If an Aadhaar is detected, save the original image as `<original_name>.<ext>.original` in the same directory.
   - Crop the original file using PIL and overwrite `<original_name>.<ext>`.
   - If no Aadhaar is detected (e.g. a PAN card), skip cropping.

---

## 3. Detailed Technical Design

### Bounding Box Prompt & Schema
We request a strict JSON format from the NIM endpoint:
```json
{
  "type": "object",
  "properties": {
    "has_aadhar": { "type": "boolean" },
    "ymin": { "type": "integer" },
    "xmin": { "type": "integer" },
    "ymax": { "type": "integer" },
    "xmax": { "type": "integer" }
  },
  "required": ["has_aadhar", "ymin", "xmin", "ymax", "xmax"]
}
```

### Affected Files
- [services/ingestion_pipeline.py](file:///c:/Users/aksha/Documents/RM Generator/RM-Maker/RM-Maker-MAIN/services/ingestion_pipeline.py)
  - Add `autocrop_image_if_aadhar(filepath)` function.
  - Call it in the ingestion loop after `auto_rotate_image(filepath)`.

---

## 4. Verification Plan

### Automated Tests
- Create [tests/test_autocrop.py](file:///c:/Users/aksha/Documents/RM Generator/RM-Maker/RM-Maker-MAIN/tests/test_autocrop.py):
  - Mock the NVIDIA NIM OpenAI completions endpoint to return coordinates.
  - Verify that the backup `.original` file is created.
  - Verify that PIL crops the image correctly.
  - Verify that the ingestion pipeline calls the autocropper correctly.
