# Spec: Title Chain Phase 1 Improvements - Manual Override & Boundary Sync

- **Date**: 2026-07-03
- **Status**: Approved
- **Author**: Antigravity

---

## 1. Goal Description

This specification addresses the Phase 1 improvements of the Title Chain timeline feature to resolve the immediate development and deployment bottlenecks.

### 1.1 Problems Solved
1. **Manual Override Discard Bug**: In Sale Deed (SD) mode, the user can edit the combined Devanagari narrative block directly in the UI text area when "Manual Mode" is active. However, when generating the final `.docx` document, the backend recompile loop overwrites this edited text area content with card-generated text.
2. **Out-of-Sync Property Details**: When a user changes property boundaries (East, West, North, South) or areas under the Property tab, these changes are not reactively pushed to the active Title Chain timeline cards' previews. The user must manually edit the cards or reload the page to refresh the compiled paragraphs.

---

## 2. Proposed Changes

### 2.1 Backend Schema Configuration
#### [MODIFY] [modules/sd/schema.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/schema.py)
* Add `"chain_is_manual"` to the list `sd_keys` whitelisted under `prune_sd_data(...)` to prevent the session pruning from deleting the flag during serialization.

---

### 2.2 Flask Controller
#### [MODIFY] [app.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/app.py)
* In route `save_case(...)` (approx. line 720), read `chain_is_manual` from request JSON and store it under `session["data"]["chain_is_manual"]`.
* In route `generate_rm(...)` (approx. line 1467):
  * Check if `context.get("chain_is_manual")` evaluates to `"true"` or `True`.
  * If true, **do not** call `generate_chain_narrative` to re-compile `context["chain_text"]`. Instead, split the existing `context["chain_text"]` by double newlines (`\n\n`) directly to populate the list `context["chain_paragraphs"]`.
  * If false or not set, proceed with the default templated re-compilation.

---

### 2.3 Frontend Layout & Javascript
#### [MODIFY] [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)
* **Collect Override Flag**: In `collectFieldData()`, add `chain_is_manual` to the collected `data` payload:
  ```javascript
  chain_is_manual: document.getElementById('field_chain_is_manual')?.checked ? 'true' : 'false'
  ```
* **Page Load Init**: In `initializeGlobalChainMode()`, read the saved `chain_is_manual` flag from server data:
  ```javascript
  const isManualSaved = "{{ data.get('chain_is_manual', 'false') }}" === "true";
  toggle.checked = isManualSaved;
  if (isManualSaved) {
      globalTextarea.removeAttribute('readonly');
  } else {
      globalTextarea.setAttribute('readonly', 'true');
  }
  ```
* **Reactive Property Sync**:
  * In the document load/initialization function in `case.html`, add event listeners to property input elements:
    * `#field_ps_0_e`
    * `#field_ps_0_w`
    * `#field_ps_0_n`
    * `#field_ps_0_s`
    * `#field_ps_0_area`
    * `#field_ps_0_area_unit`
  * Bind `input` and `change` events on these selectors to a callback:
    * If `#field_chain_is_manual` is unchecked:
      * Find all elements with the class `.chain-card` in the DOM to determine the loop count.
      * Execute `compileCardPreview(idx)` for each card sequentially.

---

## 3. Verification Plan

### 3.1 Automated Tests
* We can run the existing test suite using `pytest` (if any tests are configured) to verify we haven't broken any general case loading/saving.

### 3.2 Manual Verification
1. **Manual Override**:
   * Open a Sale Deed case.
   * Go to the Title Chain tab, check "Edit narrative directly".
   * Add a custom word (e.g. "SPECIAL TEST WORD") to the main text area.
   * Save the case, reload the page, and ensure the checkbox remains checked and the text is persisted.
   * Generate the final Word document and verify the custom text appears in the generated file.
2. **Boundary Sync**:
   * Open the case, ensure Manual mode is unchecked.
   * Go to the Property Details tab and change the North Boundary to "50 Feet Wide Highway".
   * Go to the Title Chain tab (without reloading) and verify the compiled paragraphs on the right side now reflect the new boundary value.
