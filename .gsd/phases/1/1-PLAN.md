---
phase: 1
plan: 1
wave: 1
---

# Plan 1.1: Stabilize and Verify Web UI Migration & Flask Server

## Objective
Stabilize, test, and verify the newly migrated Flask web application (which replaced the Tkinter UI), ensuring full feature parity and absolute reliability in session loading, smart-merging, and document generation.

## Context
- [.gsd/SPEC.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/.gsd/SPEC.md)
- [.gsd/ROADMAP.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/.gsd/ROADMAP.md)
- [app.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/app.py)
- [extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/extractor.py)
- [processor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/processor.py)
- [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/web_templates/case.html)

## Tasks

<task type="auto">
  <name>Web App Verification & Linting</name>
  <files>c:\Users\aksha\Documents\RM Generator\RM-Maker\app.py</files>
  <action>
    Run a full syntax and compilation validation check across the entire migrated codebase. Ensure Flask starts up correctly in a verification test run and there are no syntax errors or unresolved imports (such as obsolete tkinter references) in app.py, extractor.py, or processor.py.
  </action>
  <verify>python -m py_compile app.py extractor.py processor.py</verify>
  <done>
    - Command output shows successful compilation without errors.
    - No references to legacy 'tkinter' modules remain in app.py or other core files except in conditional fallback cases.
  </done>
</task>

<task type="auto">
  <name>Verify Server Endpoints & Case Persistence</name>
  <files>c:\Users\aksha\Documents\RM Generator\RM-Maker\app.py</files>
  <action>
    Perform an automated endpoint verification using python-request or curl to query the Flask local server at http://127.0.0.1:5000/ and verify the HTTP status code is 200. Test the /new_case session initialization route and ensure a new JSON case file is created correctly under the cases/ directory.
  </action>
  <verify>powershell -Command "Invoke-WebRequest -Uri 'http://127.0.0.1:5000/' -UseBasicParsing"</verify>
  <done>
    - HTTP response code is 200 OK.
    - Running Invoke-WebRequest on http://127.0.0.1:5000/new_case redirects correctly or creates a new case session file under cases/case_[timestamp]/session.json.
  </done>
</task>

<task type="checkpoint:human-verify">
  <name>Visual Scrutiny of Web Dashboard and Aadhaar Assignment Table</name>
  <files>c:\Users\aksha\Documents\RM Generator\RM-Maker\web_templates\case.html</files>
  <action>
    Manually inspect the UI by opening http://127.0.0.1:5000 in the browser. Test creating a new case, selecting a bank, uploading document files, and assigning Aadhaar card details dynamically using the role mapping dropdown and verifying they populate the fields correctly.
  </action>
  <verify>Manual confirmation of layout layout stability and role assignment logic in the browser.</verify>
  <done>
    - The dual-panel UI renders without layout truncation or overlapping text.
    - Clicking the 'Apply' button on an unassigned Aadhaar card successfully populates the target borrower/witness input fields and checks their respective 'Verify' checkboxes.
  </done>
</task>

## Success Criteria
- [ ] Flask web interface is fully operational and loads without server-side crashes.
- [ ] Session files are generated under `cases/` and can be loaded back dynamically.
- [ ] Smart-merge correctly protects manually verified entries on subsequent extraction.
