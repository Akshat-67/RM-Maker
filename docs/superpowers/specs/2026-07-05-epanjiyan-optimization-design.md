# Design Spec: e-Panjiyan Autofill Performance Optimization

This design specification outlines the optimizations to make the e-Panjiyan Chrome extension automation lightning-fast by replacing static timeouts with event-driven triggers and parallelizing input fields.

## Proposed Changes

### 1. Event-Driven Page Load Handler (`content.js`)
* **Goal**: Eliminate the static `1500ms` start delay on every page load.
* **Mechanism**: 
  * Check `document.readyState` immediately.
  * If the page is already loaded, start the check instantly.
  * Otherwise, attach to the `DOMContentLoaded` event and start as soon as it fires, with a backup timeout of only `300ms`.

### 2. Parallel Static Field Filling (`content.js`)
* **Goal**: Fill form inputs simultaneously instead of waiting sequentially.
* **Mechanism**:
  * Identify all static text input fields on the `/Party/PartyAdd` form (e.g., Name English, Name Hindi, Mobile, ID Details, House No, Colony, Pincode).
  * Use `Promise.all` to write values and trigger keyboard events in parallel.
  * Example pattern:
    ```javascript
    await Promise.all([
        setInputValue(getField('nameEn'), data.name_en),
        setInputValue(getField('nameHi'), data.name_hi),
        setInputValue(getField('mobile'), data.mobile),
        ...
    ]);
    ```

### 3. Non-Blocking Select2 Dropdown Polling (`content.js`)
* **Goal**: Eliminate the hardcoded `600ms` / `800ms` timeouts between dropdown selections.
* **Mechanism**:
  * Retain the polling loop that checks for options availability.
  * Once the option is available, select it and dispatch events immediately.
  * Begin searching for the next dropdown's options without introducing any artificial `setTimeout` sleep blocks.

### 4. High-Frequency Alert Dismissal (`content.js`)
* **Goal**: Reduce latency when waiting for SweetAlert2 save/calculation confirmation popups.
* **Mechanism**:
  * Reduce the `checkInterval` polling frequency for `.swal2-confirm` from `250ms` to `50ms`.
  * Trigger click and finish automation immediately upon detection.

### 5. Multiple Executants State Machine Sequence (`content.js`)
* **Goal**: Support cases with more than one borrower/executant without skipping any records.
* **Mechanism**:
  * Expand `partyStage` value from a singular `"EXECUTANT"` string to dynamically support index-appended values (`"EXECUTANT_0"`, `"EXECUTANT_1"`, etc.).
  * For any active index `idx`, retrieve the specific executant `data.executants[idx]`.
  * After saving, check if there is a next index (`idx + 1 < data.executants.length`).
    * If yes, transition to `"EXECUTANT_${idx + 1}"`.
    * If no, transition to `"CLAIMANT"`.

## Verification Plan

### Manual Verification
1. Measure the time taken to complete the Document Details form.
2. Measure the time taken to complete the Party Details (Executant, Claimant, Witnesses, Presenter) automation.
3. Verify that the website correctly saves all details and does not drop any events.
4. Verify that cases with multiple executants sequentially add all executants before moving to the Claimant (Bank).
