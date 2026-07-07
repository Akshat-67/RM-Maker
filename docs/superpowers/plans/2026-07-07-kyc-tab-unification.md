# Unified KYC Tab and Structured AI Extraction Implementation Plan
 
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
 
**Goal:** Consolidate multiple KYC files (Aadhaar Front, Aadhaar Back, PAN Card) belonging to the same person under a single collapsed tab named `<Role> [KYC]`, powered by Gemini classifying document types during the extraction step.
 
**Architecture:** Classify document pages at extraction time (Aadhaar Front vs Back vs PAN) and map them in `localStorage`. The frontend hides duplicate tabs and renders a 3-way toggle toolbar (`[Front]`, `[Back]`, `[PAN]`) in the preview pane.
 
**Tech Stack:** Python, HTML5, Javascript (Vanilla), Bootstrap 5.
 
## Global Constraints
* Hindi text must use Unicode Devanagari fonts (Segoe UI / Mangal).
* Real-time transliteration workflows and Aadhaar relations in RM mode must not be modified or disabled.
* The customization constraints in AGENTS.md must be respected at all times.
 
---
 
### Task 1: Structured AI KYC Document Classification
 
**Files:**
- Modify: [modules/rm/extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/extractor.py)
- Modify: [modules/sd/extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/extractor.py)
- Test: [tests/test_pdf_preprocessor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/tests/test_pdf_preprocessor.py)
 
**Interfaces:**
- Consumes: Multimodal filename tagging.
- Produces: `unassigned_aadhars` list where each element's `files` field contains objects of the shape `{"file": "filename", "type": "aadhar_front|aadhar_back|pan"}`.
 
- [ ] **Step 1: Update RM Prompt Schema**
  Update the `unassigned_aadhars` JSON structure and Rule 4 inside the RM extraction prompt in [modules/rm/extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/extractor.py):
  ```python
  # In JSON STRUCTURE:
  "unassigned_aadhars": [{"s":"Mr/Mrs/Ms", "n":"Name", "a":"Age", "dob":"DOB", "relation_text":"Complete Relation Phrase", "adr":"Address", "id":"Aadhar Number", "pan":"PAN", "files": [{"file": "exact filename", "type": "aadhar_front|aadhar_back|pan"}]}]
  
  # In RULES:
  4. AADHAAR & PAN CARDS: Extract details from uploaded cards into 'unassigned_aadhars' EXCLUSIVELY. For each card, populate a 'files' array containing objects with 'file' (the exact filename from headers) and 'type' (identifying if the file is 'aadhar_front', 'aadhar_back', or 'pan' based on visual contents).
  ```
 
- [ ] **Step 2: Update SD Prompt Schemas**
  Update the JSON structure and Rule 1/4 inside both SD prompts in [modules/sd/extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/extractor.py):
  ```python
  # Prompt 1 Schema:
  "unassigned_aadhars": [{"s": "Mr/Mrs/Ms", "n": "Name", "n_en": "English Name", "a": "Age", "dob": "DOB", "relation_text": "Relation", "rn_en": "Relative English Name", "adr": "Address", "adr_en": "English Address", "id": "Aadhar", "pan": "PAN", "files": [{"file": "exact filename", "type": "aadhar_front|aadhar_back|pan"}]}]
  
  # Prompt 2 Schema:
  "unassigned_aadhars": [{"s":"Mr/Mrs/Ms", "n":"Name in Hindi", "n_en":"Name in English script", "a":"Age", "dob":"DOB", "relation_text":"Relation in Hindi", "rn_en":"Relative Father Name", "adr":"Address in Hindi", "adr_en":"Address in English", "id":"Aadhar", "pan":"PAN", "files": [{"file": "exact filename", "type": "aadhar_front|aadhar_back|pan"}]}]
  ```
 
- [ ] **Step 3: Run py_compile to check syntax**
  Run: `python -m py_compile modules/rm/extractor.py modules/sd/extractor.py`
  Expected output: Exit code 0 (no errors).
 
- [ ] **Step 4: Commit changes**
  ```bash
  git add modules/rm/extractor.py modules/sd/extractor.py
  git commit -m "feat: restructure AI prompts to classify front, back, and PAN document types"
  ```
 
---
 
### Task 2: Update Unassigned Table Markup and Role Assignment Logic
 
**Files:**
- Modify: [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)
 
**Interfaces:**
- Consumes: `unassigned_aadhars` rows with `files` list containing types.
- Produces: `localStorage` mapping where `roles[file] = { role: "Borrower 1", type: "aadhar_front|aadhar_back|pan" }`.
 
- [ ] **Step 1: Update table row `data-files` serializing**
  Update the `tr` element loop in [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html):
  ```html
  <tr id="ua-row-{{ loop.index0 }}" 
      ...
      data-files="{{ ua.get('files', []) | tojson | forceescape }}">
  ```
 
- [ ] **Step 2: Update assignment JS mapping inside `assignSelectedAadhars`**
  Modify `assignSelectedAadhars` to record the structured role objects in `localStorage`:
  ```javascript
  const filesAttr = row.getAttribute('data-files');
  if (filesAttr) {
      try {
          const rowFiles = JSON.parse(filesAttr);
          if (Array.isArray(rowFiles)) {
              rowFiles.forEach(item => {
                  if (item && item.file) {
                      roles[item.file] = {
                          role: role,
                          type: item.type || 'aadhar_front'
                      };
                  }
              });
          }
      } catch (e) {
          console.error("Failed to parse data-files", e);
      }
  }
  ```
 
- [ ] **Step 3: Commit changes**
  ```bash
  git add web_templates/case.html
  git commit -m "feat: serialize and assign structured KYC file roles to localStorage"
  ```
 
---
 
### Task 3: Implement Collapsed Tab and Sidebar Grouping
 
**Files:**
- Modify: [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)
 
**Interfaces:**
- Consumes: `localStorage` roles mapping structure.
- Produces: `window.CURRENT_ACTIVE_GROUPINGS` dictionary mapping each role prefix to its list of file paths.
 
- [ ] **Step 1: Rewrite `updateFileTabLabels`**
  Update `updateFileTabLabels` to scan files and group them:
  ```javascript
  function updateFileTabLabels() {
      const storageKey = 'case_file_roles_' + CASE_ID;
      const roles = JSON.parse(localStorage.getItem(storageKey) || '{}');
      
      // Group files by role
      const groups = {};
      const allFiles = Array.from(document.querySelectorAll('.file-preview-btn, span[data-filename-span]'))
                            .map(el => el.getAttribute('data-filename') || el.getAttribute('data-filename-span'))
                            .filter(Boolean);
      const uniqueFiles = [...new Set(allFiles)];
      
      uniqueFiles.forEach(file => {
          const mapping = roles[file];
          if (mapping && typeof mapping === 'object' && mapping.role) {
              const r = mapping.role;
              if (!groups[r]) groups[r] = [];
              groups[r].push({ file: file, type: mapping.type });
          } else if (mapping && typeof mapping === 'string') {
              // Backward compatibility for simple strings
              const r = mapping;
              if (!groups[r]) groups[r] = [];
              groups[r].push({ file: file, type: file.toLowerCase().includes('pan') ? 'pan' : 'aadhar_front' });
          }
      });
      
      window.CURRENT_ACTIVE_GROUPINGS = groups;
      
      // Keep track of which files are representatives and which are hidden
      const hiddenFiles = new Set();
      const representativeFiles = {}; // role -> file
      
      Object.keys(groups).forEach(role => {
          const filesList = groups[role];
          // Find representative file: front -> back -> pan
          let rep = filesList.find(f => f.type === 'aadhar_front') ||
                    filesList.find(f => f.type === 'aadhar_back') ||
                    filesList.find(f => f.type === 'pan') ||
                    filesList[0];
          
          if (rep) {
              representativeFiles[role] = rep.file;
              filesList.forEach(f => {
                  if (f.file !== rep.file) {
                      hiddenFiles.add(f.file);
                  }
              });
          }
      });
      
      // Helper function to resolve displayName
      function getRoleDisplayName(role) {
          const parts = role.split('.');
          let prefix = '';
          let idx = 0;
          if (parts.length === 2) {
              prefix = parts[0];
              idx = parseInt(parts[1]);
          } else {
              prefix = role;
          }
          
          let displayPrefix = '';
          if (prefix === 'bs') displayPrefix = 'Borrower';
          else if (prefix === 'ws') displayPrefix = 'Witness';
          else if (prefix === 'ss') displayPrefix = 'Seller';
          else if (prefix === 'buyers') displayPrefix = 'Buyer';
          else if (prefix === 'sellers') displayPrefix = 'Seller';
          else if (prefix === 'bsign') return 'Bank Signer [KYC]';
          else return `${role} [KYC]`;
          
          return `${displayPrefix} ${idx + 1} [KYC]`;
      }
      
      // Update elements
      uniqueFiles.forEach(file => {
          const mapping = roles[file];
          const role = mapping && typeof mapping === 'object' ? mapping.role : mapping;
          const isRepresentative = role && (representativeFiles[role] === file);
          const isHidden = hiddenFiles.has(file);
          
          // Select tab buttons and sidebar elements
          const tabs = document.querySelectorAll(`[id="file-tab-${file.replace(/\./g, '_')}"]`);
          const sidebarItems = document.querySelectorAll(`[data-sidebar-file="${file}"]`);
          
          if (isHidden) {
              tabs.forEach(t => t.style.display = 'none');
              sidebarItems.forEach(s => s.style.display = 'none');
          } else {
              tabs.forEach(t => t.style.display = '');
              sidebarItems.forEach(s => s.style.display = '');
              
              let displayName = file;
              if (isRepresentative) {
                  displayName = getRoleDisplayName(role);
              }
              
              tabs.forEach(t => {
                  const textEl = t.querySelector('span') || t;
                  textEl.textContent = '📄 ' + displayName;
              });
              
              const sidebarSpan = document.querySelector(`span[data-filename-span="${file}"]`);
              if (sidebarSpan) {
                  sidebarSpan.textContent = displayName;
                  sidebarSpan.title = displayName;
              }
          }
      });
  }
  ```
 
- [ ] **Step 2: Commit changes**
  ```bash
  git add web_templates/case.html
  git commit -m "feat: implement unified KYC tab collapsing and hide subsidiary files"
  ```
 
---
 
### Task 4: Implement 3-Way Toggles in Document Preview
 
**Files:**
- Modify: [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)
 
**Interfaces:**
- Consumes: `window.CURRENT_ACTIVE_GROUPINGS` and active file tab.
- Produces: Live document display switching in iframe/img preview frame.
 
- [ ] **Step 1: Replace Front/Back Toggles in Preview Toolbar with 3-Way Selector**
  Modify preview file toggle container markup in [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html):
  ```html
  <div id="frontBackToggleContainer" style="display: none; gap: 6px;">
      <button id="btnToggleFront" class="btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white" style="font-size: 0.68rem; display: none;" onclick="showGroupedFile('aadhar_front')">Front</button>
      <button id="btnToggleBack" class="btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white" style="font-size: 0.68rem; display: none;" onclick="showGroupedFile('aadhar_back')">Back</button>
      <button id="btnTogglePan" class="btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white" style="font-size: 0.68rem; display: none;" onclick="showGroupedFile('pan')">PAN</button>
  </div>
  ```
 
- [ ] **Step 2: Implement JS helper `showGroupedFile` and rewrite `previewFile`**
  Modify preview helper logic inside script section of [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html):
  ```javascript
  let activeGroupFiles = [];
  
  function showGroupedFile(type) {
      const match = activeGroupFiles.find(f => f.type === type);
      if (match) {
          previewFileDirect(match.file);
          // Highlight buttons
          const btnFront = document.getElementById('btnToggleFront');
          const btnBack = document.getElementById('btnToggleBack');
          const btnPan = document.getElementById('btnTogglePan');
          
          btnFront.className = type === 'aadhar_front' ? "btn btn-primary btn-xs fw-bold px-2.5 py-1" : "btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white";
          btnBack.className = type === 'aadhar_back' ? "btn btn-primary btn-xs fw-bold px-2.5 py-1" : "btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white";
          btnPan.className = type === 'pan' ? "btn btn-primary btn-xs fw-bold px-2.5 py-1" : "btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white";
      }
  }
  
  function previewFileDirect(filename) {
      const iframe = document.getElementById('previewIframe');
      const img = document.getElementById('previewImg');
      const placeholder = document.getElementById('previewPlaceholder');
      
      iframe.style.display = 'none';
      img.style.display = 'none';
      placeholder.style.display = 'none';
      
      const fileUrl = `/case/${CASE_ID}/file/${filename}`;
      const ext = filename.split('.').pop().toLowerCase();
      if (ext === 'pdf') {
          iframe.src = fileUrl;
          iframe.style.display = 'block';
      } else if (['png', 'jpg', 'jpeg'].includes(ext)) {
          img.src = fileUrl;
          img.style.display = 'block';
      } else {
          placeholder.style.display = 'block';
          placeholder.querySelector('span:last-child').textContent = `Preview not supported for .${ext} files.`;
      }
  }
  
  function previewFile(filename) {
      // Deactivate all buttons highlights
      document.querySelectorAll('.file-preview-btn').forEach(btn => btn.classList.remove('active-preview'));
      
      // Find role and matching group
      const storageKey = 'case_file_roles_' + CASE_ID;
      const roles = JSON.parse(localStorage.getItem(storageKey) || '{}');
      const mapping = roles[filename];
      const role = mapping && typeof mapping === 'object' ? mapping.role : mapping;
      
      const toggleContainer = document.getElementById('frontBackToggleContainer');
      const btnFront = document.getElementById('btnToggleFront');
      const btnBack = document.getElementById('btnToggleBack');
      const btnPan = document.getElementById('btnTogglePan');
      
      if (role && window.CURRENT_ACTIVE_GROUPINGS && window.CURRENT_ACTIVE_GROUPINGS[role]) {
          activeGroupFiles = window.CURRENT_ACTIVE_GROUPINGS[role];
          toggleContainer.style.display = 'flex';
          
          const hasFront = activeGroupFiles.some(f => f.type === 'aadhar_front');
          const hasBack = activeGroupFiles.some(f => f.type === 'aadhar_back');
          const hasPan = activeGroupFiles.some(f => f.type === 'pan');
          
          btnFront.style.display = hasFront ? 'inline-block' : 'none';
          btnBack.style.display = hasBack ? 'inline-block' : 'none';
          btnPan.style.display = hasPan ? 'inline-block' : 'none';
          
          // Determine active type of the selected file
          const currentMap = activeGroupFiles.find(f => f.file === filename);
          const currentType = currentMap ? currentMap.type : 'aadhar_front';
          showGroupedFile(currentType);
      } else {
          activeGroupFiles = [];
          toggleContainer.style.display = 'none';
          previewFileDirect(filename);
      }
      
      // Highlight the tab itself
      const safeId = 'file-tab-' + filename.replace(/\./g, '_');
      const activeBtn = document.getElementById(safeId);
      if (activeBtn) {
          activeBtn.classList.add('active-preview');
      }
      
      const titleEl = document.getElementById('previewTitle');
      if (titleEl) {
          titleEl.textContent = filename;
          titleEl.title = filename;
      }
  }
  ```
 
- [ ] **Step 3: Commit changes**
  ```bash
  git add web_templates/case.html
  git commit -m "feat: implement 3-way toggle button display in the preview toolbar"
  ```
