# Specification: Timeline Transliteration & Textarea Height Expansion
 
This document defines the spec for expanding the height of the Title Chain Timeline narrative textarea and integrating transliteration / DevLys mode controls.
 
## Goal
1. Increase the vertical height of the Hindi Narrative Preview textarea in the Title Chain Timeline tab to allow easier editing.
2. Add toggle buttons for Transliteration and DevLys typing directly to the Title Chain Timeline preview section.
3. Ensure transliteration and DevLys keyboard inputs function correctly in the narrative preview textarea and timeline inputs.
 
---
 
## Proposed Changes
 
### 1. Preview Layout & Buttons
#### [case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)
* **Textarea Height**: Change the enclosing tab-content height to `min-height: 500px;` and set the height of `#chainNarrativePreview` to `100%` with `min-height: 420px; resize: vertical;`.
* **Toolbar Toggle buttons**: Update the preview switcher header to place the toggle buttons adjacent to the "Edit Text / Rich View" tabs:
  ```html
  <div class="d-flex justify-content-between align-items-center mb-2 flex-shrink-0">
      <ul class="nav nav-tabs" id="narrativePreviewTabs" role="tablist" style="font-size: 0.78rem; border-bottom: none;">
          ...
      </ul>
      <div class="d-flex gap-1.5 align-items-center">
          <button id="btnToggleItransTimeline" class="btn btn-xs btn-outline-warning text-dark fw-bold py-1 px-2.5" style="font-size: 0.68rem;" onclick="toggleItransMode()">A→अ ITRANS (Off)</button>
          <button id="btnToggleDevLysTimeline" class="btn btn-xs btn-outline-info text-dark fw-bold py-1 px-2.5" style="font-size: 0.68rem;" onclick="toggleDevLysMode()">⌨️ DevLys (Off)</button>
      </div>
  </div>
  ```
 
### 2. Synchronization and Transliteration Event Interception
#### [case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)
* **State Mirroring**: Modify `toggleItransMode()` and `toggleDevLysMode()` to look up both the primary and timeline toggle buttons by ID and class, syncing their classes (e.g. `btn-warning` vs `btn-outline-warning`) and inner text.
* **Fields Selector**: Modify `shouldTransliterate(el)` to return `true` if `el.id` is `'chainNarrativePreview'`, `'node_sellers'`, or `'node_buyers'`.
* **Global Listeners**: Move the `keydown` and `blur` transliteration listeners from `#verificationContent` to `document` so they apply to all inputs/textareas with the `hindi-legacy-input` class across the whole page.
 
---
 
## Verification Plan
* Verify that the template renders correctly and the textarea height is expanded.
* Type inside the narrative preview textarea with ITRANS mode active and verify space bar transliterates words to Hindi.
