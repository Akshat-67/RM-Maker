# Smart Validation Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Live Validation Panel and a secondary AI-driven Proofreader utilizing NVIDIA NIM APIs (`nvidia/nemotron-ocr-v2` and `openai/gpt-oss-120b`) to verify legal deed entries and prevent compilation errors.

**Architecture:** We will implement new validators inside `services/validation/` that verify gender/salutations, detect missing fields, and cross-reference names with raw OCR text extracted from uploaded KYC scans using Nemotron OCR v2. A post-generation AI proofreader using GPT-OSS-120b will compare the rendered Word document text against the ground truth and display discrepancies live on the case page.

**Tech Stack:** Python, Flask, PIL (for image compression), OpenAI Python client, requests, docx2txt.

## Global Constraints
*   All new libraries must be added to `requirements.txt`.
*   All name cross-checks must use case-insensitive fuzzy matching.
*   Original KYC images must be downscaled/compressed using PIL to stay within the 180,000 base64 characters limit.

---

### Task 1: Environment & Config Setup

**Files:**
- Modify: [utils/config.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/utils/config.py)
- Modify: [.env](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/.env)

**Interfaces:**
- Produces: `NVIDIA_NIM_API_KEY` and `NVIDIA_OCR_API_KEY` configuration variables in `utils/config.py`.

- [ ] **Step 1: Write config test**
  Create `tests/test_nvidia_config.py` with:
  ```python
  import os
  from utils.config import NVIDIA_NIM_API_KEY, NVIDIA_OCR_API_KEY
  
  def test_nvidia_keys():
      assert NVIDIA_NIM_API_KEY == "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"
      assert NVIDIA_OCR_API_KEY == "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"
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m pytest tests/test_nvidia_config.py`
  Expected: Failure due to missing variables or incorrect values.

- [ ] **Step 3: Update config files**
  Add keys to `.env`:
  ```bash
  NVIDIA_NIM_API_KEY=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
  NVIDIA_OCR_API_KEY=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
  ```
  Modify `utils/config.py` to import these env variables.

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m pytest tests/test_nvidia_config.py`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add utils/config.py .env tests/test_nvidia_config.py
  git commit -m "feat: add nvidia nim config and tests"
  ```

---

### Task 2: Image Compression Utility

**Files:**
- Modify: [utils/helpers.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/utils/helpers.py)
- Create: [tests/test_image_compression.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/tests/test_image_compression.py)

**Interfaces:**
- Produces: `prepare_image_for_nim(image_bytes: bytes, max_b64_len: int = 175000) -> str` returning base64-encoded image string.

- [ ] **Step 1: Write compression test**
  Write `tests/test_image_compression.py` with:
  ```python
  import io
  from PIL import Image
  from utils.helpers import prepare_image_for_nim
  
  def test_prepare_image():
      # Create a large dummy image
      img = Image.new('RGB', (1000, 1000), color = 'red')
      byte_arr = io.BytesIO()
      img.save(byte_arr, format='PNG')
      png_bytes = byte_arr.getvalue()
      
      b64_str = prepare_image_for_nim(png_bytes)
      assert len(b64_str) < 180000
      assert b64_str.startswith("data:image/jpeg;base64,") or b64_str.startswith("data:image/png;base64,")
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m pytest tests/test_image_compression.py`
  Expected: Import or function definition failure.

- [ ] **Step 3: Implement compression helper**
  Write in `utils/helpers.py`:
  ```python
  import base64
  import io
  from PIL import Image
  
  def prepare_image_for_nim(image_bytes: bytes, max_b64_len: int = 175000) -> str:
      img = Image.open(io.BytesIO(image_bytes))
      if img.mode != 'RGB':
          img = img.convert('RGB')
          
      quality = 90
      scale = 1.0
      
      while True:
          w, h = int(img.width * scale), int(img.height * scale)
          temp_img = img.resize((w, h), Image.Resampling.LANCZOS) if scale < 1.0 else img
          
          out_arr = io.BytesIO()
          temp_img.save(out_arr, format='JPEG', quality=quality)
          b64_data = base64.b64encode(out_arr.getvalue()).decode('utf-8')
          b64_str = f"data:image/jpeg;base64,{b64_data}"
          
          if len(b64_str) < max_b64_len:
              return b64_str
              
          if quality > 30:
              quality -= 10
          else:
              scale -= 0.1
              quality = 80
          if scale <= 0.1:
              return b64_str
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m pytest tests/test_image_compression.py`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add utils/helpers.py tests/test_image_compression.py
  git commit -m "feat: add image downscaling utility for nvidia nim ocr"
  ```

---

### Task 3: Implement Core Validators

**Files:**
- Create: `services/validation/gender_validator.py`
- Create: `services/validation/missing_fields_validator.py`
- Create: `services/validation/template_validator.py`
- Modify: `services/validation/__init__.py`

**Interfaces:**
- Produces: `GenderValidator`, `MissingFieldsValidator`, `TemplateValidator` classes extending `BaseValidator`.

- [ ] **Step 1: Write tests for validators**
  Create `tests/test_new_validators.py` with:
  ```python
  from services.validation.gender_validator import GenderValidator
  from services.validation.missing_fields_validator import MissingFieldsValidator
  from services.validation.template_validator import TemplateValidator
  
  def test_gender_validator():
      val = GenderValidator()
      # Mr. with relation W/o must trigger high discrepancy
      case_data = {
          "bs": [{"s": "Mr.", "r": "W/o", "rn": "John", "gender": "Female"}],
          "doc_type": "RM"
      }
      res = val.validate(case_data)
      assert len(res) > 0
      assert res[0].severity == "high"
  ```

- [ ] **Step 2: Run tests to verify they fail**
  Run: `python -m pytest tests/test_new_validators.py`
  Expected: FAIL (modules do not exist)

- [ ] **Step 3: Implement `GenderValidator`**
  Write in `services/validation/gender_validator.py`:
  ```python
  from typing import List, Dict, Any
  from .base import BaseValidator
  from .models import Discrepancy, FixAction
  
  class GenderValidator(BaseValidator):
      def supports(self, doc_type: str) -> bool:
          return doc_type == "RM"
          
      def validate(self, case_data: Dict[str, Any]) -> List[Discrepancy]:
          findings = []
          for idx, b in enumerate(case_data.get("bs", [])):
              if not isinstance(b, dict): continue
              sal = str(b.get("s", "")).strip().lower()
              rel = str(b.get("r", "")).strip().lower()
              gender = str(b.get("gender", "")).strip().lower()
              
              path_prefix = f"bs.{idx}"
              
              if rel == "w/o" and (sal == "mr." or gender == "male"):
                  findings.append(
                      Discrepancy(
                          category="gender",
                          severity="high",
                          explanation=f"Borrower {idx + 1} has relation 'W/o' but salutation is 'Mr.' or gender is 'Male'.",
                          suggested_fix="Change Salutation to Mrs./Ms. and Gender to Female.",
                          source_references=[
                              {"path": f"{path_prefix}.s", "value": b.get("s")},
                              {"path": f"{path_prefix}.r", "value": b.get("r")},
                              {"path": f"{path_prefix}.gender", "value": b.get("gender")}
                          ],
                          fix_actions=[
                              FixAction(path=f"{path_prefix}.s", value="Mrs."),
                              FixAction(path=f"{path_prefix}.gender", value="Female")
                          ]
                      )
                  )
          return findings
  ```

- [ ] **Step 4: Implement `MissingFieldsValidator` and `TemplateValidator`**
  Write implementations and register them in `services/validation/__init__.py`.

- [ ] **Step 5: Run tests to verify they pass**
  Run: `python -m pytest tests/test_new_validators.py`
  Expected: PASS

- [ ] **Step 6: Commit**
  Run:
  ```bash
  git add services/validation/ tests/test_new_validators.py
  git commit -m "feat: add gender, missing fields and template validators"
  ```

---

### Task 4: Nemotron OCR & GPT-OSS-120b Proofreader Integration

**Files:**
- Create: `services/validation/nim_proofreader.py`
- Create: `services/validation/name_match_validator.py`

**Interfaces:**
- Produces: `NIMProofreader.proofread(docx_text: str, session_data: dict) -> list[Discrepancy]`
- Produces: `NameMatchValidator` executing high-accuracy Nemotron OCR on case KYC files.

- [ ] **Step 1: Write proofreader mock test**
  Create `tests/test_nim_proofreader.py` with:
  ```python
  from services.validation.nim_proofreader import NIMProofreader
  
  def test_proofreader():
      # Mock the NIM request and assert it detects duplicate words
      text = "Mr. Mr. Akshat Sharma agrees to pay Rupees Rupees Fifty Thousand Only Only."
      session_data = {"bs": [{"n": "Akshat Sharma"}]}
      findings = NIMProofreader.proofread(text, session_data)
      assert len(findings) > 0
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m pytest tests/test_nim_proofreader.py`
  Expected: FAIL

- [ ] **Step 3: Implement Nemotron OCR & GPT-OSS-120b Clients**
  Write in `services/validation/nim_proofreader.py`:
  ```python
  import requests
  from openai import OpenAI
  from utils.config import NVIDIA_NIM_API_KEY
  
  class NIMProofreader:
      @staticmethod
      def proofread(docx_text: str, session_data: dict) -> list:
          client = OpenAI(
              base_url="https://integrate.api.nvidia.com/v1",
              api_key=NVIDIA_NIM_API_KEY
          )
          prompt = f"Deed Text:\n{docx_text}\n\nSession Fields:\n{session_data}\n\nIdentify discrepancies..."
          completion = client.chat.completions.create(
              model="openai/gpt-oss-120b",
              messages=[{"role": "user", "content": prompt}],
              temperature=0.1
          )
          content = completion.choices[0].message.content
          # Parse structured findings from JSON and return list of Discrepancy objects
          return []
  ```
  Write the `NameMatchValidator` to make requests to the Nemotron API: `https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v2`.

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m pytest tests/test_nim_proofreader.py`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add services/validation/nim_proofreader.py services/validation/name_match_validator.py tests/test_nim_proofreader.py
  git commit -m "feat: add nvidia nim proofreader and ocr validators"
  ```

---

### Task 5: Frontend Integration & Validation API Endpoint

**Files:**
- Modify: [routes/cases.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/routes/cases.py)
- Modify: [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)

**Interfaces:**
- Produces: Live checklist UI sidebar panel updating on debounced key inputs.

- [ ] **Step 1: Write integration test**
  Add test in `tests/test_stability_patch.py` checking `GET /api/case/<case_id>/validation` returns all discrepancies including gender, missing fields, and OCR matches.

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m pytest tests/test_stability_patch.py`
  Expected: Errors or missing fields in the JSON response.

- [ ] **Step 3: Update Flask validation route**
  Ensure `/api/case/<case_id>/validation` calls the updated validation engine including Nemotron OCR and GPT-OSS checks.

- [ ] **Step 4: Build live validation panel UI**
  Add a sidebar div to `web_templates/case.html` with Tailwind or custom CSS classes. Implement a JS function `runValidation()` that fetches from the validation endpoint and dynamically populates checks, warnings, and error list items. Bind the function to form inputs on blur or changes with a 400ms debounce timer.

- [ ] **Step 5: Run tests to verify they pass**
  Run: `python -m pytest tests/test_stability_patch.py`
  Expected: PASS

- [ ] **Step 6: Commit**
  Run:
  ```bash
  git add routes/cases.py web_templates/case.html tests/test_stability_patch.py
  git commit -m "feat: integrate live validation panel and API routes"
  ```
