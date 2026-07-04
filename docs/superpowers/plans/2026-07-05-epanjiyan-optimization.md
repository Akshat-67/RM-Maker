# e-Panjiyan Autofill Performance Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Optimize the e-Panjiyan Chrome extension to perform autofill and page transitions with minimal latency by removing static delays and parallelizing field entry.

**Architecture:** Use event-driven document ready state checking, parallelize static text inputs using JavaScript asynchronous promises (`Promise.all`), and increase polling frequency for dynamic dropdowns and popups to ensure instant responses.

**Tech Stack:** JavaScript (ES6+), Chrome Extensions API (Manifest V3)

## Global Constraints
* Do not introduce any new dependencies.
* Maintain all existing validation and bilingual Select2 fallback match logic.

---

### Task 1: Optimize Page Load Startup Hook

**Files:**
- Modify: `extensions/epanjiyan_autofill/content.js:1440-1478`

**Interfaces:**
- Consumes: Page load events.
- Produces: Instant initialization of `oneClickAutofill`.

- [ ] **Step 1: Modify page load auto-execution check to use instant document readiness check**

Change the self-executing code at the end of the file in `extensions/epanjiyan_autofill/content.js`:
```javascript
// Old logic:
try {
    if (chrome && chrome.storage && chrome.storage.local) {
        chrome.storage.local.get(['oneClickRunning', 'activeCaseData'], (res) => {
            if (res.oneClickRunning && res.activeCaseData) {
                const caseData = res.activeCaseData;
                console.log("[RM-Maker] Detected active One-Click Autofill. Starting auto-execution in 1.5s...");
                setTimeout(() => {
                    oneClickAutofill(caseData, (response) => {
                        if (response && !response.success) {
                            console.error("[RM-Maker] Step auto-execution failed:", response.error);
                        }
                    });
                }, 1500);
            }
        });
    }
} catch (e) {
    console.error("[RM-Maker] Error in page-load auto-execution check:", e);
}
```
Replace with:
```javascript
try {
    if (chrome && chrome.storage && chrome.storage.local) {
        chrome.storage.local.get(['oneClickRunning', 'activeCaseData'], (res) => {
            if (res.oneClickRunning && res.activeCaseData) {
                const caseData = res.activeCaseData;
                
                const runAutofill = () => {
                    console.log("[RM-Maker] Starting auto-execution immediately...");
                    oneClickAutofill(caseData, (response) => {
                        if (response && !response.success) {
                            console.error("[RM-Maker] Step auto-execution failed:", response.error);
                        }
                    });
                };

                // Check readiness immediately or bind to DOMContentLoaded with 200ms fallback
                if (document.readyState === "complete" || document.readyState === "interactive") {
                    runAutofill();
                } else {
                    let triggered = false;
                    const triggerOnce = () => {
                        if (triggered) return;
                        triggered = true;
                        runAutofill();
                    };
                    document.addEventListener("DOMContentLoaded", triggerOnce);
                    window.addEventListener("load", triggerOnce);
                    // Minimal fallback
                    setTimeout(triggerOnce, 250);
                }
            }
        });
    }
} catch (e) {
    console.error("[RM-Maker] Error in page-load auto-execution check:", e);
}
```

- [ ] **Step 2: Check Syntax using Node**

Run: `node -c extensions/epanjiyan_autofill/content.js`
Expected: Success

- [ ] **Step 3: Commit**
```bash
git add extensions/epanjiyan_autofill/content.js
git commit -m "perf: optimize page load auto-execution hook to trigger instantly"
```

---

### Task 2: Parallelize Static Field Filling on PartyAdd Form

**Files:**
- Modify: `extensions/epanjiyan_autofill/content.js:350-415` (within `fillPartyFormFields` function)

**Interfaces:**
- Consumes: `partyData` block containing personal details.
- Produces: Simultaneous field value updates on the active DOM form.

- [ ] **Step 1: Group independent static text inputs and fill in parallel**

Modify the synchronous text-filling section of `fillPartyFormFields` to use `Promise.all` instead of individual sequential calls:
```javascript
    // Group static inputs and execute them simultaneously
    await Promise.all([
        (async () => {
            const nameEnInput = getField('nameEn');
            if (nameEnInput) setInputValue(nameEnInput, partyData.name_en);
        })(),
        (async () => {
            const nameHiInput = getField('nameHi');
            if (nameHiInput) setInputValue(nameHiInput, partyData.name_hi);
        })(),
        (async () => {
            const ageInput = getField('age');
            if (ageInput) setInputValue(ageInput, partyData.age.toString());
        })(),
        (async () => {
            const contactInput = getField('contactNo');
            if (contactInput) setInputValue(contactInput, partyData.mobile || FAKE_MOBILE);
        })(),
        (async () => {
            const idDetailsInput = getField('idDetails');
            if (idDetailsInput) setInputValue(idDetailsInput, partyData.aadhaar);
        })(),
        (async () => {
            if (partyData.address) {
                const houseInput = getField('houseNo');
                const colonyInput = getField('colony');
                const areaInput = getField('area');
                const cityInput = getField('city');
                const pinInput = getField('pincode');
                
                setInputValue(houseInput, partyData.address.house_no || "00");
                setInputValue(colonyInput, partyData.address.colony || "");
                setInputValue(areaInput, partyData.address.area || "");
                setInputValue(cityInput, partyData.address.city || "JAIPUR");
                setInputValue(pinInput, partyData.address.pincode || "");
            }
        })()
    ]);
```

- [ ] **Step 2: Check Syntax using Node**

Run: `node -c extensions/epanjiyan_autofill/content.js`
Expected: Success

- [ ] **Step 3: Commit**
```bash
git add extensions/epanjiyan_autofill/content.js
git commit -m "perf: parallelize static text input filling in fillPartyFormFields using Promise.all"
```

---

### Task 3: Eliminate Artificial Dropdown Sleep Timeouts

**Files:**
- Modify: `extensions/epanjiyan_autofill/content.js:890-945` (within `autofillDetails` function)

**Interfaces:**
- Consumes: Dropdown selection calls.
- Produces: Instant progression through document classification selectors.

- [ ] **Step 1: Remove hardcoded timeouts from autofillDetails dropdown flow**

In `autofillDetails`, update the dropdown section to execute sequentially without waiting for `setTimeout` between selections:
```javascript
                // Fill Document Type using exact select element ID
                showStatusToast("Setting Document Type: Mortgage...");
                const docTypeSelect = document.getElementById('parentarticle_id');
                let docTypeSet = false;
                for (let i = 0; i < 10; i++) {
                    docTypeSet = await setSelectValueByText(docTypeSelect, "Mortgage/ Charge");
                    if (docTypeSet) break;
                    await new Promise(r => setTimeout(r, 200));
                }
                
                // Fill SubType using exact select element ID
                showStatusToast("Setting SubType: Mortgage without possession...");
                const subTypeSelect = document.getElementById('ddlDocSubType');
                let subTypeSet = false;
                for (let i = 0; i < 15; i++) {
                    subTypeSet = await setSelectValueByText(subTypeSelect, "(b)Mortgage deed without possession");
                    if (subTypeSet) break;
                    await new Promise(r => setTimeout(r, 200));
                }
                
                // Fill Category using exact select element ID
                showStatusToast("Setting Category: General...");
                const catSelect = document.getElementById('ddlCategory');
                let catSet = false;
                for (let i = 0; i < 10; i++) {
                    catSet = await setSelectValueByText(catSelect, "General");
                    if (catSet) break;
                    await new Promise(r => setTimeout(r, 200));
                }
                
                // Fill SRO using exact select element ID
                showStatusToast(`Setting SRO to ${data.sro || 'JAIPUR-VII'}...`);
                const sroSelect = document.getElementById('ddlSRO');
                let sroSet = false;
                for (let i = 0; i < 15; i++) {
                    sroSet = await setSelectValueByText(sroSelect, data.sro || "JAIPUR-VII");
                    if (sroSet) break;
                    await new Promise(r => setTimeout(r, 200));
                }
                
                // Fill Tehsil using exact select element ID
                showStatusToast(`Setting Tehsil to ${data.tehsil || 'JAIPUR'}...`);
                const tehsilSelect = document.getElementById('ddlTehsil');
                let tehsilSet = false;
                for (let i = 0; i < 15; i++) {
                    tehsilSet = await setSelectValueByText(tehsilSelect, data.tehsil || "JAIPUR");
                    if (tehsilSet) break;
                    await new Promise(r => setTimeout(r, 200));
                }
```

- [ ] **Step 2: Check Syntax using Node**

Run: `node -c extensions/epanjiyan_autofill/content.js`
Expected: Success

- [ ] **Step 3: Commit**
```bash
git add extensions/epanjiyan_autofill/content.js
git commit -m "perf: remove hardcoded setTimeout delays between dropdown selections"
```

---

### Task 4: High-Frequency Alert Confirmation Polling

**Files:**
- Modify: `extensions/epanjiyan_autofill/content.js:1450-1545` (within SweetAlert polling intervals)

**Interfaces:**
- Consumes: SweetAlert visual indicators.
- Produces: Instant clicks to confirmation buttons.

- [ ] **Step 1: Update polling rates for Save and Calculation popups**

In `content.js` at all locations checking for the `.swal2-confirm` confirmation popups (such as inside `autofillDetails`, `autofillCalculateDuty`, and the new state-machine handlers):
* Reduce the `checkInterval` timer period from `250ms` to `50ms`.
* Reduce the timeout before hiding the status toast from `1000ms` / `1500ms` to `100ms` / `200ms` where safe.

Example:
```javascript
                            // Poll for SweetAlert2 modal to appear
                            const checkInterval = setInterval(() => {
                                showStatusToast("Waiting for Party Saved popup...");
                                const swalOkBtn = document.querySelector('.swal2-confirm') || 
                                                  Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'OK' && (b.offsetWidth > 0 || b.offsetHeight > 0));
                                if (swalOkBtn) {
                                    showStatusToast("Confirming Save (Clicking OK)...");
                                    clearInterval(checkInterval);
                                    
                                    const updates = { partyStage: nextStage };
                                    if (nextStage === "DONE") {
                                        updates.oneClickRunning = false;
                                    }
                                    chrome.storage.local.set(updates, () => {
                                        swalOkBtn.click();
                                        setTimeout(() => hideStatusToast(), 100);
                                        sendResponse({ success: true, message: `Successfully saved ${stage}` });
                                    });
                                }
                            }, 50); // Set to 50ms instead of 250ms
```

- [ ] **Step 2: Check Syntax using Node**

Run: `node -c extensions/epanjiyan_autofill/content.js`
Expected: Success

- [ ] **Step 3: Run full pytest suite**

Run: `$env:PYTHONPATH="." ; pytest tests/`
Expected: 12 passed

- [ ] **Step 4: Commit**
```bash
git add extensions/epanjiyan_autofill/content.js
git commit -m "perf: reduce SweetAlert popup polling interval to 50ms for instant confirmation"
```
