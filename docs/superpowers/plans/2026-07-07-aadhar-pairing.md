# Aadhaar Pairing & Dynamic Tab Renaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement client-side document pairing (Option A: keywords/alphabetical) and tabbed quick-toggle (Option C: floating buttons inside preview) alongside dynamic tab renaming based on manual party assignments to speed up verification.

**Architecture:** Client-side JavaScript enhancement in `case.html` that matches filenames against assignments and pairs front/back images dynamically.

**Tech Stack:** Vanilla JavaScript, HTML5, Bootstrap 5.

## Global Constraints
- **Case Sensitivity**: Lowercase all URLs when evaluating page locations (`/party/viewparty`, `/party/partyadd`).
- **No Schema Changes**: Must not modify database fields or change Flask APIs to keep the backend stable.

---

### Task 1: Add HTML Split-Screen Preview elements and Quick-Toggle styles

**Files:**
- Modify: [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)

**Interfaces:**
- Produces: Visual floating button placeholders `#frontBackToggleContainer` inside the document preview pane.

- [ ] **Step 1: Add HTML for quick-toggle container inside preview console**
  Find the element `<div style="position: relative; height: calc(100vh - 145px)...` in `case.html` (around line 900) and insert the HTML markup for the float controls:
  ```html
  <div id="frontBackToggleContainer" style="position: absolute; top: 12px; right: 12px; z-index: 100; display: none; gap: 6px;">
      <button id="btnToggleFront" class="btn btn-primary btn-xs fw-bold px-2.5 py-1" style="font-size: 0.68rem; box-shadow: 0 2px 4px rgba(0,0,0,0.15);" onclick="showPairedFile('front')">Front</button>
      <button id="btnToggleBack" class="btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white" style="font-size: 0.68rem; box-shadow: 0 2px 4px rgba(0,0,0,0.15);" onclick="showPairedFile('back')">Back</button>
  </div>
  ```

- [ ] **Step 2: Commit Task 1**
  ```bash
  git add web_templates/case.html
  git commit -m "feat: add quick-toggle button container to document preview pane"
  ```

---

### Task 2: Implement File Pairing JavaScript Logic

**Files:**
- Modify: [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)

**Interfaces:**
- Consumes: `#frontBackToggleContainer`, `previewFile(filename)`
- Produces: Javascript functions `findPairedFile(filename, allFiles)`, `showPairedFile(side)`

- [ ] **Step 1: Implement `findPairedFile` logic in `case.html` script block**
  Add the helper function inside the primary `<script>` tag:
  ```javascript
  const ALL_CASE_FILES = [
      {% for f in files %}"{{ f | basename }}",{% endfor %}
      {% for b_name, b_files in buckets.items() %}{% for f in b_files %}"{{ f | basename }}",{% endfor %}{% endfor %}
  ].filter((v, i, a) => a.indexOf(v) === i);

  function findPairedFile(filename) {
      const ext = filename.split('.').pop().toLowerCase();
      if (!['jpg', 'jpeg', 'png'].includes(ext)) return null;

      const base = filename.substring(0, filename.lastIndexOf('.'));
      const normalized = base.toLowerCase().replace(/[^a-z0-9]/g, '');

      // Keyword lists
      const frontKeywords = ['front', 'obverse', 'f', '1'];
      const backKeywords = ['back', 'reverse', 'b', '2'];

      // Helper to strip front/back suffix from normalized base
      const getPrefix = (str, keywords) => {
          for (const kw of keywords) {
              if (str.endsWith(kw)) {
                  return str.substring(0, str.length - kw.length);
              }
          }
          return null;
      };

      const frontPrefix = getPrefix(normalized, frontKeywords);
      const backPrefix = getPrefix(normalized, backKeywords);

      let targetPrefix = "";
      let targetKeywords = [];
      let isCurrentFront = false;

      if (frontPrefix !== null) {
          targetPrefix = frontPrefix;
          targetKeywords = backKeywords;
          isCurrentFront = true;
      } else if (backPrefix !== null) {
          targetPrefix = backPrefix;
          targetKeywords = frontKeywords;
          isCurrentFront = false;
      }

      if (targetPrefix) {
          // Look for matching file with opposite suffix
          for (const other of ALL_CASE_FILES) {
              const otherExt = other.split('.').pop().toLowerCase();
              if (!['jpg', 'jpeg', 'png'].includes(otherExt)) continue;
              if (other === filename) continue;

              const otherBase = other.substring(0, other.lastIndexOf('.'));
              const otherNorm = otherBase.toLowerCase().replace(/[^a-z0-9]/g, '');

              const otherPrefix = getPrefix(otherNorm, targetKeywords);
              if (otherPrefix === targetPrefix) {
                  return {
                      file: other,
                      side: isCurrentFront ? 'front' : 'back',
                      pairedFile: other,
                      pairedSide: isCurrentFront ? 'back' : 'front'
                  };
              }
          }
      }

      // Alphabetical pairing fallback: match files sharing 75%+ prefix length
      for (const other of ALL_CASE_FILES) {
          const otherExt = other.split('.').pop().toLowerCase();
          if (!['jpg', 'jpeg', 'png'].includes(otherExt)) continue;
          if (other === filename) continue;

          const otherBase = other.substring(0, other.lastIndexOf('.'));
          const otherNorm = otherBase.toLowerCase().replace(/[^a-z0-9]/g, '');

          // Check if bases are identical except for one character at the end
          if (Math.abs(otherNorm.length - normalized.length) <= 2) {
              let commonLen = 0;
              while (commonLen < normalized.length && commonLen < otherNorm.length && normalized[commonLen] === otherNorm[commonLen]) {
                  commonLen++;
              }
              if (commonLen >= Math.max(normalized.length, otherNorm.length) - 2) {
                  // Determine front/back based on alphabetical sorting
                  const currentIsFirst = filename.localeCompare(other) < 0;
                  return {
                      file: filename,
                      side: currentIsFirst ? 'front' : 'back',
                      pairedFile: other,
                      pairedSide: currentIsFirst ? 'back' : 'front'
                  };
              }
          }
      }

      return null;
  }
  ```

- [ ] **Step 2: Update `previewFile` and add `showPairedFile` toggler logic**
  Modify `previewFile(filename)` in `case.html` to integrate pairing:
  ```javascript
  let activePairedInfo = null;

  function showPairedFile(side) {
      if (!activePairedInfo) return;
      const targetFile = (side === activePairedInfo.side) ? activePairedInfo.file : activePairedInfo.pairedFile;
      
      // Load target file inside iframe or img
      const iframe = document.getElementById('previewIframe');
      const img = document.getElementById('previewImg');
      const fileUrl = `/case/${CASE_ID}/file/${targetFile}`;
      const ext = targetFile.split('.').pop().toLowerCase();

      if (ext === 'pdf') {
          img.style.display = 'none';
          iframe.src = fileUrl;
          iframe.style.display = 'block';
      } else {
          iframe.style.display = 'none';
          img.src = fileUrl;
          img.style.display = 'block';
      }

      // Update button highlights
      const btnFront = document.getElementById('btnToggleFront');
      const btnBack = document.getElementById('btnToggleBack');
      if (side === 'front') {
          btnFront.className = "btn btn-primary btn-xs fw-bold px-2.5 py-1";
          btnBack.className = "btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white";
      } else {
          btnFront.className = "btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white";
          btnBack.className = "btn btn-primary btn-xs fw-bold px-2.5 py-1";
      }
  }
  ```
  And inside `previewFile(filename)`, check for pairings:
  ```javascript
  // (In previewFile(filename) right before setting iframe/img source):
  const pairInfo = findPairedFile(filename);
  const toggleContainer = document.getElementById('frontBackToggleContainer');
  if (pairInfo) {
      activePairedInfo = pairInfo;
      toggleContainer.style.display = 'flex';
      
      const btnFront = document.getElementById('btnToggleFront');
      const btnBack = document.getElementById('btnToggleBack');
      
      if (pairInfo.side === 'front') {
          btnFront.className = "btn btn-primary btn-xs fw-bold px-2.5 py-1";
          btnBack.className = "btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white";
      } else {
          btnFront.className = "btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white";
          btnBack.className = "btn btn-primary btn-xs fw-bold px-2.5 py-1";
      }
  } else {
      activePairedInfo = null;
      toggleContainer.style.display = 'none';
  }
  ```

- [ ] **Step 3: Commit Task 2**
  ```bash
  git add web_templates/case.html
  git commit -m "feat: implement JavaScript pairing logic and quick-toggle buttons inside preview"
  ```

---

### Task 3: Implement Dynamic Tab/Header Renaming Logic

**Files:**
- Modify: [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)

**Interfaces:**
- Consumes: Assigned inputs (`field_bs_*_n`, `field_ws_*_n`, etc.)
- Produces: `updateFileTabLabels()`

- [ ] **Step 1: Write `updateFileTabLabels` function in `case.html` script block**
  Add the renaming matching logic:
  ```javascript
  function updateFileTabLabels() {
      const docType = document.getElementById('docTypeSelect').value;
      const assignments = []; // Array of { roleName: "Borrower 1", name: "Kiran Devi", id: "1234..." }

      const getVal = (id) => {
          const el = document.getElementById(id);
          return el ? el.value.trim().toUpperCase() : '';
      };

      if (docType === 'SD') {
          // Sellers
          for (let i = 0; i < 5; i++) {
              const name = getVal(`field_sellers_${i}_n_en`) || getVal(`field_sellers_${i}_n`);
              const id = getVal(`field_sellers_${i}_id`);
              if (name) assignments.push({ role: `Seller ${i + 1}`, name, id });
          }
          // Buyers
          for (let i = 0; i < 5; i++) {
              const name = getVal(`field_buyers_${i}_n_en`) || getVal(`field_buyers_${i}_n`);
              const id = getVal(`field_buyers_${i}_id`);
              if (name) assignments.push({ role: `Buyer ${i + 1}`, name, id });
          }
          // Witnesses
          for (let i = 0; i < 5; i++) {
              const name = getVal(`field_ws_${i}_n_en`) || getVal(`field_ws_${i}_n`);
              const id = getVal(`field_ws_${i}_id`);
              if (name) assignments.push({ role: `Witness ${i + 1}`, name, id });
          }
      } else {
          // Borrowers
          for (let i = 0; i < 5; i++) {
              const name = getVal(`field_bs_${i}_n`);
              const id = getVal(`field_bs_${i}_id`);
              if (name) assignments.push({ role: `Borrower ${i + 1}`, name, id });
          }
          // Witnesses
          for (let i = 0; i < 5; i++) {
              const name = getVal(`field_ws_${i}_n`);
              const id = getVal(`field_ws_${i}_id`);
              if (name) assignments.push({ role: `Witness ${i + 1}`, name, id });
          }
          // Bank Signer
          const signerName = getVal('field_bsign_n');
          const signerId = getVal('field_bsign_id');
          if (signerName) assignments.push({ role: 'Bank Signer', name: signerName, id: signerId });
      }

      // Now iterate through tabs and match filenames to assignments
      ALL_CASE_FILES.forEach(filename => {
          const base = filename.substring(0, filename.lastIndexOf('.')).toLowerCase().replace(/[^a-z0-9]/g, '');
          let matchedRole = "";

          // Try matching by Aadhaar ID (last 4 digits)
          for (const ass of assignments) {
              if (ass.id && ass.id.replace(/\s/g, '').length >= 4) {
                  const idClean = ass.id.replace(/\s/g, '');
                  const last4 = idClean.substring(idClean.length - 4);
                  if (base.includes(last4)) {
                      matchedRole = ass.role;
                      break;
                  }
              }
          }

          // Try fuzzy matching by Name
          if (!matchedRole) {
              for (const ass of assignments) {
                  const assClean = ass.name.toLowerCase().replace(/[^a-z0-9]/g, '');
                  // Check if name contains filename parts or vice-versa
                  if (assClean.length >= 3) {
                      // Check overlap
                      if (base.includes(assClean) || assClean.includes(base) || 
                          assClean.split(' ').every(part => base.includes(part))) {
                          matchedRole = ass.role;
                          break;
                      }
                  }
              }
          }

          // Construct display name
          let displayName = filename;
          if (matchedRole) {
              const ext = filename.split('.').pop();
              const pairInfo = findPairedFile(filename);
              let sideLabel = "";
              if (pairInfo) {
                  sideLabel = pairInfo.side === 'front' ? ' (Front)' : ' (Back)';
              }
              displayName = `${matchedRole}${sideLabel}.${ext}`;
          }

          // Rename file preview tabs
          const safeId = 'file-tab-' + filename.replace(/\./g, '_');
          const tabBtn = document.getElementById(safeId);
          if (tabBtn) {
              tabBtn.innerHTML = `📄 ${displayName}`;
              tabBtn.title = displayName;
          }

          // Rename sidebar list elements
          const sidebarSpan = document.querySelector(`span[onclick="previewFile('${filename}')"]`);
          if (sidebarSpan) {
              sidebarSpan.textContent = displayName;
              sidebarSpan.title = displayName;
          }
      });
  }
  ```

- [ ] **Step 2: Hook `updateFileTabLabels` into loading and Click actions**
  Make sure `updateFileTabLabels` runs:
  1. At the end of `DOMContentLoaded` handler:
     ```javascript
     document.addEventListener('DOMContentLoaded', () => {
         // ... existing loads ...
         setTimeout(updateFileTabLabels, 500);
     });
     ```
  2. At the end of `assignSelectedAadhars()` in `case.html` (right after completing all assignments).
  3. On changing fields (like binding blur/change event listeners to field inputs to update live if manually edited).
     ```javascript
     document.querySelectorAll('input[id^="field_"]').forEach(inp => {
         inp.addEventListener('blur', updateFileTabLabels);
         inp.addEventListener('change', updateFileTabLabels);
     });
     ```

- [ ] **Step 3: Add data-filename attribute to preview buttons in HTML template**
  Ensure we can find the buttons by class even if IDs are re-rendered. Add `data-filename="{{ filename }}"` to button in lines 889-896.

- [ ] **Step 4: Commit Task 3**
  ```bash
  git add web_templates/case.html
  git commit -m "feat: integrate dynamic tab renaming on assignments change and page load"
  ```
