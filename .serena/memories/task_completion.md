# Task Completion Memory

Follow this checklist before considering any coding task complete in this repository:

## 1. Run Verification Tests
- Ensure all Python unit tests pass by running:
  ```powershell
  pytest
  ```
- Pay special attention to:
  - `tests/test_sd_kyc_relation.py` (checks relation parsing/splitting)
  - `tests/test_e2e_rm.py` and `tests/test_e2e_sd.py` (checks docx output generation)

## 2. Compile and Verify UI Styles
- If any frontend HTML or static CSS assets were modified, rebuild the Tailwind bundle:
  ```powershell
  npm run build:css
  ```
- Verify the UI layout in the browser to ensure no styling errors.

## 3. Verify Generated Word Documents
- Check output folders (typically `cases/`) for generated `.docx` files.
- Verify that document files exist and have a valid size (usually >10KB).
- Ensure that fonts display legacy Devanagari text correctly if converted, and standard Unicode in the web viewer.

## 4. Update the Knowledge Graph
- Since this project tracks a knowledge graph in `graphify-out/`, always run the update script after changing source files to keep the AST graph current:
  ```powershell
  graphify update .
  ```

## 5. Check Serena Memories
- Verify that memories references are correct and there are no stale memories:
  ```powershell
  serena memories check
  ```
