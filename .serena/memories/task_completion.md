# Task Completion Memory

Follow this checklist before considering any coding task complete in this repository:

## 1. Run Verification Tests
- Ensure all Python unit tests pass by running:
  ```powershell
  $env:PYTHONPATH="."; pytest tests/ --ignore=tests/test_stability_patch.py -v
  ```
- Pay special attention to:
  - `tests/test_sd_kyc_relation.py` (checks relation parsing/splitting)
  - `tests/test_generation.py` (checks docx output generation)

## 2. Compile and Verify UI Styles
- Verify the UI layout in the browser to ensure no styling errors.

## 3. Verify Generated Word Documents
- Check output folders (typically `cases/`) for generated `.docx` files.
- Verify that document files exist and have a valid size (usually >10KB).
- Ensure that fonts display legacy Devanagari text correctly if converted, and standard Unicode in the web viewer.

## 4. Check Serena Memories
- Verify that memories references are correct and there are no stale memories:
  ```powershell
  serena memories check
  ```
