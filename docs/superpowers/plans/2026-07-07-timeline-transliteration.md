# Timeline Transliteration & Height Expansion Implementation Plan
 
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
 
**Goal:** Expand the height of the timeline narrative preview textarea and add synchronized transliteration / DevLys mode buttons to Step 3.
 
**Architecture:** Increase container min-height, embed a second button set in the tab header styled with Bootstrap, synchronize both button sets via script state, and scope keyboard events to `document` to enable global typing support.
 
**Tech Stack:** HTML5, CSS3, Javascript.
 
## Global Constraints
* Hindi text must use Segoe UI or Mangal fonts.
* Legacy encoding/fonts must not be used on the client text inputs.
* AGENTS.md rules must not be violated.
 
---
 
### Task 1: Expand Textarea Height and Add Timeline Toggle Buttons
 
**Files:**
- Modify: [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)
 
- [ ] **Step 1: Increase container and textarea height**
  Locate the tab-content block (around line 1797) in [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html):
  ```html
  <div class="tab-content flex-grow-1 overflow-hidden d-flex flex-column mb-3" style="min-height: 500px;">
      <!-- Editable Raw Area -->
      <div class="tab-pane fade show active flex-grow-1 d-flex flex-column" id="narrative-edit-pane" role="tabpanel">
          <textarea class="form-control flex-grow-1 hindi-legacy-input font-monospace p-3" id="chainNarrativePreview" style="font-size: 0.88rem; line-height: 1.6; resize: vertical; min-height: 420px; height: 100%;" oninput="syncNarrativeToMainData()">{{ data.get('chain_text', '') }}</textarea>
      </div>
  ```
 
- [ ] **Step 2: Add mini toolbar to PreviewSwitcher tabs**
  Update the narrative tab list switcher layout (around line 1788) in [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html):
  ```html
  <!-- Preview Mode Switcher Tabs -->
  <div class="d-flex justify-content-between align-items-center mb-2 flex-shrink-0">
      <ul class="nav nav-tabs" id="narrativePreviewTabs" role="tablist" style="font-size: 0.78rem; border-bottom: none;">
          <li class="nav-item" role="presentation">
              <button class="nav-link active py-1 px-3 fw-bold" id="narrative-edit-tab" data-bs-toggle="tab" data-bs-target="#narrative-edit-pane" type="button" role="tab" aria-selected="true">✏️ Edit Text</button>
          </li>
          <li class="nav-item" role="presentation">
              <button class="nav-link py-1 px-3 fw-bold" id="narrative-rich-tab" data-bs-toggle="tab" data-bs-target="#narrative-rich-pane" type="button" role="tab" aria-selected="false" onclick="renderRichNarrative()">👁️ Rich View</button>
          </li>
      </ul>
      <div class="d-flex gap-1.5 align-items-center">
          <button id="btnToggleItransTimeline" class="btn btn-xs btn-outline-warning text-dark fw-bold py-1 px-2.5" style="font-size: 0.68rem;" onclick="toggleItransMode()">A→अ ITRANS (Off)</button>
          <button id="btnToggleDevLysTimeline" class="btn btn-xs btn-outline-info text-dark fw-bold py-1 px-2.5" style="font-size: 0.68rem;" onclick="toggleDevLysMode()">⌨️ DevLys (Off)</button>
      </div>
  </div>
  ```
 
- [ ] **Step 3: Commit changes**
  ```bash
  git add web_templates/case.html
  git commit -m "feat: expand narrative preview textarea height and add toggle buttons to timeline"
  ```
 
---
 
### Task 2: Synchronize Typing Modes and Scope Event Listeners Globally
 
**Files:**
- Modify: [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)
 
- [ ] **Step 1: Update state toggling function**
  Modify `toggleItransMode()` and `toggleDevLysMode()` script definitions (around line 2432) in [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html):
  ```javascript
  function toggleItransMode() {
      transliterationEnabled = !transliterationEnabled;
      if (transliterationEnabled) {
          devlysEnabled = false;
          // Sync DevLys buttons
          const devlysBtns = [document.getElementById('btnToggleDevLys'), document.getElementById('btnToggleDevLysTimeline')];
          devlysBtns.forEach(btn => {
              if (btn) {
                  btn.classList.replace('btn-info', 'btn-outline-info');
                  btn.innerHTML = '⌨️ DevLys (Off)';
              }
          });
          document.getElementById('devlysBadge').style.display = 'none';
      }
      
      const itransBtns = [document.getElementById('btnToggleItrans'), document.getElementById('btnToggleItransTimeline')];
      itransBtns.forEach(btn => {
          if (btn) {
              if (transliterationEnabled) {
                  btn.classList.replace('btn-outline-warning', 'btn-warning');
                  btn.innerHTML = 'A→अ ITRANS (ON)';
              } else {
                  btn.classList.replace('btn-warning', 'btn-outline-warning');
                  btn.innerHTML = 'A→अ ITRANS (Off)';
              }
          }
      });
      document.getElementById('transliterationBadge').style.display = transliterationEnabled ? 'inline-block' : 'none';
      updateActiveModeIndicator();
  }
 
  function toggleDevLysMode() {
      devlysEnabled = !devlysEnabled;
      if (devlysEnabled) {
          transliterationEnabled = false;
          // Sync Itrans buttons
          const itransBtns = [document.getElementById('btnToggleItrans'), document.getElementById('btnToggleItransTimeline')];
          itransBtns.forEach(btn => {
              if (btn) {
                  btn.classList.replace('btn-warning', 'btn-outline-warning');
                  btn.innerHTML = 'A→अ ITRANS (Off)';
              }
          });
          document.getElementById('transliterationBadge').style.display = 'none';
      }
      
      const devlysBtns = [document.getElementById('btnToggleDevLys'), document.getElementById('btnToggleDevLysTimeline')];
      devlysBtns.forEach(btn => {
          if (btn) {
              if (devlysEnabled) {
                  btn.classList.replace('btn-outline-info', 'btn-info');
                  btn.innerHTML = '⌨️ DevLys (ON)';
              } else {
                  btn.classList.replace('btn-info', 'btn-outline-info');
                  btn.innerHTML = '⌨️ DevLys (Off)';
              }
          }
      });
      document.getElementById('devlysBadge').style.display = devlysEnabled ? 'inline-block' : 'none';
      updateActiveModeIndicator();
  }
  ```
 
- [ ] **Step 2: Update field checks selector**
  Update `shouldTransliterate(el)` helper function (around line 2487) in [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html):
  ```javascript
   function shouldTransliterate(el) {
      if (!el || !el.id) return false;
      const id = el.id.toLowerCase();
      if (id.endsWith('_en')) return false;
      if (id.includes('_id') || id.includes('_pan') || id.includes('_reg_no')) return false;
      if (id === 'chainnarrativepreview') return true;
      if (id === 'node_sellers' || id === 'node_buyers') return true;
      
      const label = el.closest('.col-md-6, .col-12, .col-md-9, .col-md-4, .col-8, .col-4')?.querySelector('label')?.textContent || "";
      const isHindiField = label.includes('(Hindi)') || label.includes('Address') || label.includes('Owner') || label.includes('Deed Type') || label.includes('Words') || label.includes('Relation') || label.includes('Name') || label.includes('Title');
      return isHindiField;
  }
  ```
 
- [ ] **Step 3: Update keydown and blur event listener scoping**
  Change the binding target variable `workspace` in [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html) (around line 2668):
  ```javascript
  // Change const workspace = document.getElementById('verificationContent'); to:
  const workspace = document.body;
  ```
 
- [ ] **Step 4: Commit changes**
  ```bash
  git add web_templates/case.html
  git commit -m "feat: synchronize timeline buttons state and expand keyboard listeners globally to document.body"
  ```
