# e-Panjiyan Automation Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automate the Document Details form filling and Stamp Duty Calculation pages in the e-Panjiyan Chrome extension by targeting precise element IDs and implementing state-based redirect loop prevention.

**Architecture:** Update the content script (`content.js`) functions `setSelectValueByText`, `autofillDetails`, and `autofillCalculateDuty` to use precise selector queries and value matching. Use `chrome.storage.local` to persist the stamp duty calculation state so that we can transition from Calculate Duty to Party Details on page reload.

**Tech Stack:** Chrome Extension manifest v3, Vanilla JavaScript, DOM APIs, jQuery/Select2 page context triggers.

## Global Constraints
* Maintain strict compatibility with manifest v3 and Chrome Extension APIs.
* Do not modify or alter the KYC, Aadhaar/PAN extraction, or relation splitting logic in the backend python files (`app.py`, `utils/helpers.py`, etc.).
* All selectors must fail gracefully if elements are not found, and log appropriate messages to the console and user status toast.

---

### Task 1: Update Dropdown Option Selection matching in `content.js`

**Files:**
* Modify: `extensions/epanjiyan_autofill/content.js`

**Interfaces:**
* Consumes: Nothing
* Produces: Updated helper function `setSelectValueByText` supporting bilingual fallbacks.

- [ ] **Step 1: Locate and rewrite `setSelectValueByText` function**

Modify the option matching loop in `setSelectValueByText` in `extensions/epanjiyan_autofill/content.js` starting at line 504 to support bilingual English/Hindi matches:

```javascript
async function setSelectValueByText(selectEl, text) {
    if (!selectEl) return false;
    
    if (selectEl.tagName.toUpperCase() === 'NG-SELECT') {
        return await selectNgSelectOption(selectEl, text);
    }
    
    const options = Array.from(selectEl.options);
    const isExactJaipur = text.toUpperCase() === 'JAIPUR';
    const matchedOption = options.find(opt => {
        const optText = opt.text.toUpperCase();
        if (isExactJaipur) {
            return optText.includes('JAIPUR') || optText.includes('जयपुर');
        }
        
        const query = text.toUpperCase();
        let isMatch = optText.includes(query) || optText.replace(/\s+/g, '').includes(query.replace(/\s+/g, ''));
        
        // Bilingual fallbacks mapping if direct string match fails
        if (!isMatch) {
            if (query.includes("MORTGAGE/ CHARGE") || query.includes("MORTGAGE")) {
                isMatch = optText.includes("बंधक/भार") || optText.includes("MORTGAGE");
            } else if (query.includes("WITHOUT POSSESSION")) {
                isMatch = optText.includes("बिना कब्जे") || optText.includes("WITHOUT POSSESSION");
            } else if (query.includes("GENERAL")) {
                isMatch = optText.includes("सामान्य") || optText.includes("GENERAL");
            }
        }
        return isMatch;
    });
    
    if (matchedOption) {
        selectEl.value = matchedOption.value;
        selectEl.dispatchEvent(new Event('change', { bubbles: true }));
        selectEl.dispatchEvent(new Event('input', { bubbles: true }));
        
        // Ensure element has ID and trigger page-context jQuery update
        if (!selectEl.id) {
            selectEl.id = 'select_' + Math.random().toString(36).substring(2, 9);
        }
        triggerJQuerySelect(selectEl.id, matchedOption.value);
        return true;
    }
    return false;
}
```

- [ ] **Step 2: Syntax check the script**

Run syntax check using node CLI:
`node -c extensions/epanjiyan_autofill/content.js`
Expected: Program completes successfully with no syntax output.

- [ ] **Step 3: Commit changes**

```bash
git add extensions/epanjiyan_autofill/content.js
git commit -m "feat: update setSelectValueByText with bilingual fallbacks"
```

---

### Task 2: Implement Precise Element Selection in `autofillDetails`

**Files:**
* Modify: `extensions/epanjiyan_autofill/content.js`

**Interfaces:**
* Consumes: Updated `setSelectValueByText` function from Task 1.
* Produces: Updated `autofillDetails` function.

- [ ] **Step 1: Rewrite `autofillDetails` in `content.js`**

Replace `autofillDetails` function in `extensions/epanjiyan_autofill/content.js` (lines 822-969) with direct ID selectors and value-based radio checks:

```javascript
async function autofillDetails(data, sendResponse, autoSave = false) {
    try {
        showStatusToast("Selecting Location: Urban...");
        // Select Urban
        clickRadioByValueOrLabel("Urban (शहरी)");
        
        // Select Self (target input#radioself directly)
        setTimeout(async () => {
            showStatusToast("Selecting Transfer Status: Self...");
            const selfRadio = document.getElementById('radioself') || document.querySelector('input#radioself');
            if (selfRadio) {
                selfRadio.checked = true;
                selfRadio.click();
                selfRadio.dispatchEvent(new Event('change', { bubbles: true }));
            } else {
                clickRadioByValueOrLabel("Self (स्वयं)");
            }
            
            // Wait for Self Modal
            showStatusToast("Waiting for Gender Profile Modal...");
            let modalBody = null;
            for (let i = 0; i < 15; i++) {
                const modals = Array.from(document.querySelectorAll('.modal-body, ngb-modal-window, .modal-dialog, .modal-content, .modal'));
                modalBody = modals.find(m => m.offsetWidth > 0 || m.offsetHeight > 0 || m.getBoundingClientRect().width > 0);
                if (modalBody) break;
                await new Promise(r => setTimeout(r, 150));
            }
            
            if (!modalBody) {
                showStatusToast("Error: Modal not found", false);
                sendResponse({ success: false, error: 'Could not find the category modal window.' });
                return;
            }
            
            // Find correct gender card and click it using value-based selectors
            showStatusToast(`Selecting Gender Card: ${data.gender_card}...`);
            let radioValue = "1"; // Default General Male
            if (data.gender_card === 'JOINT') {
                radioValue = "6"; // Male/Female Joint
            } else if (data.gender_card === 'FEMALE_GEN') {
                radioValue = "3"; // Female General
            }
            
            const radioBtn = modalBody.querySelector(`input[name="individualdata"][value="${radioValue}"]`);
            if (radioBtn) {
                radioBtn.checked = true;
                radioBtn.click();
                radioBtn.dispatchEvent(new Event('change', { bubbles: true }));
                
                await new Promise(r => setTimeout(r, 400));
                
                // Click Continue button in modal footer
                const continueBtn = modalBody.querySelector('button[onclick*="setdatass"]') || 
                                    modalBody.querySelector('button[onclick*="return setdatass()"]') ||
                                    Array.from(modalBody.querySelectorAll('button, a, input[type="button"]')).find(b => {
                                        const txt = b.textContent.trim().toUpperCase();
                                        return txt.includes('CONTINUE') || txt.includes('SAVE') || txt.includes('आगे बढ़ें') || txt.includes('OK');
                                    });
                                    
                if (continueBtn) {
                    showStatusToast("Saving modal selection...");
                    continueBtn.click();
                }
                
                await new Promise(r => setTimeout(r, 800));
                
                // Fill Document Type using exact select element ID
                showStatusToast("Setting Document Type: Mortgage...");
                const docTypeSelect = document.getElementById('parentarticle_id');
                await setSelectValueByText(docTypeSelect, "Mortgage/ Charge");
                
                await new Promise(r => setTimeout(r, 600));
                
                // Fill SubType using exact select element ID
                showStatusToast("Setting SubType: Mortgage without possession...");
                const subTypeSelect = document.getElementById('ddlDocSubType');
                await setSelectValueByText(subTypeSelect, "(b)Mortgage deed without possession");
                
                await new Promise(r => setTimeout(r, 600));
                
                // Fill Category using exact select element ID
                showStatusToast("Setting Category: General...");
                const catSelect = document.getElementById('ddlCategory');
                await setSelectValueByText(catSelect, "General");
                
                await new Promise(r => setTimeout(r, 600));
                
                // Fill SRO using exact select element ID
                showStatusToast(`Setting SRO to ${data.sro || 'JAIPUR-VII'}...`);
                const sroSelect = document.getElementById('ddlSRO');
                await setSelectValueByText(sroSelect, data.sro || "JAIPUR-VII");
                
                await new Promise(r => setTimeout(r, 600));
                
                // Fill Tehsil using exact select element ID
                showStatusToast(`Setting Tehsil to ${data.tehsil || 'JAIPUR'}...`);
                const tehsilSelect = document.getElementById('ddlTehsil');
                await setSelectValueByText(tehsilSelect, data.tehsil || "JAIPUR");
                
                if (autoSave) {
                    setTimeout(() => {
                        const saveBtn = document.getElementById('savedocument');
                        if (saveBtn) {
                            showStatusToast("Submitting Details (Clicking Save)...");
                            saveBtn.click();
                            
                            // Poll for SweetAlert2 modal to appear
                            const checkInterval = setInterval(() => {
                                showStatusToast("Waiting for Document Saved popup...");
                                const swalOkBtn = document.querySelector('.swal2-confirm') || 
                                                  Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'OK' && (b.offsetWidth > 0 || b.offsetHeight > 0));
                                if (swalOkBtn) {
                                    showStatusToast("Confirming Save (Clicking OK)...");
                                    clearInterval(checkInterval);
                                    swalOkBtn.click();
                                    
                                    setTimeout(() => {
                                        hideStatusToast();
                                    }, 1000);
                                    
                                    sendResponse({ success: true, message: 'Autofilled details, clicked Save, and confirmed modal!' });
                                }
                            }, 250);
                            
                            // Safety timeout (clear interval after 8 seconds)
                            setTimeout(() => {
                                clearInterval(checkInterval);
                            }, 8000);
                        } else {
                            showStatusToast("Save button not found.", false);
                            sendResponse({ success: true, message: 'Autofilled details, but could not find Save button.' });
                        }
                    }, 1000);
                } else {
                    setTimeout(() => {
                        hideStatusToast();
                    }, 1500);
                    sendResponse({ success: true, message: 'Autofilled all details! Review and click Save.' });
                }
            } else {
                showStatusToast("Card selection failed.", false);
                sendResponse({ success: false, error: `Could not find the card matching ${data.gender_card} in the modal.` });
            }
        }, 300);
    } catch (err) {
        showStatusToast("Details autofill encountered error.", false);
        sendResponse({ success: false, error: err.message });
    }
}
```

- [ ] **Step 2: Syntax check the script**

Run:
`node -c extensions/epanjiyan_autofill/content.js`
Expected: PASS with no syntax errors.

- [ ] **Step 3: Commit changes**

```bash
git add extensions/epanjiyan_autofill/content.js
git commit -m "feat: rewrite autofillDetails using exact element selectors"
```

---

### Task 3: Update `autofillCalculateDuty` for State-Based Loop Prevention

**Files:**
* Modify: `extensions/epanjiyan_autofill/content.js`

**Interfaces:**
* Consumes: Chrome Local Storage APIs
* Produces: Updated async `autofillCalculateDuty` function.

- [ ] **Step 1: Rewrite `autofillCalculateDuty` function**

Modify `autofillCalculateDuty` in `extensions/epanjiyan_autofill/content.js` (lines 975-1067) to be an async function that queries `chrome.storage.local` to determine if stamp duty was saved:

```javascript
async function autofillCalculateDuty(data, sendResponse) {
    try {
        const url = window.location.href;
        const urlLower = url.toLowerCase();
        
        if (urlLower.includes('/propertyvaluation/propertydetail')) {
            // Retrieve stampDutyCalculated status from local storage
            const storage = await new Promise(resolve => {
                chrome.storage.local.get(['stampDutyCalculated'], resolve);
            });
            
            if (storage.stampDutyCalculated) {
                showStatusToast("Proceeding to Party details screen...");
                const partyDetailBtn = document.querySelector('button[formaction*="/Party/viewparty"]') || 
                                       triggerButtonByText("Party Detail") || 
                                       triggerButtonByText("पक्षकार विवरण") ||
                                       Array.from(document.querySelectorAll('button, a')).find(b => b.textContent.includes('Party Detail') || b.textContent.includes('पक्षकार विवरण'));
                if (partyDetailBtn) {
                    chrome.storage.local.remove(['stampDutyCalculated']);
                    partyDetailBtn.click();
                    setTimeout(() => hideStatusToast(), 1000);
                    sendResponse({ success: true, message: 'Proceeding to Party Details screen...' });
                } else {
                    showStatusToast("Party Detail button not found.", false);
                    sendResponse({ success: false, error: 'Could not locate Party Detail button.' });
                }
            } else {
                showStatusToast("Navigating to Calculate Stamp Duty...");
                const calcBtn = document.querySelector('button[formaction*="/PropertyValuation/CalculateDuty"]') || 
                                triggerButtonByText("Calculate Duty") || 
                                triggerButtonByText("ड्यूटी की गणना करें");
                if (calcBtn) {
                    calcBtn.click();
                    sendResponse({ success: true, message: 'Clicked Calculate Duty!' });
                } else {
                    showStatusToast("Calculate Duty button not found.", false);
                    sendResponse({ success: false, error: 'Could not find Calculate Duty button.' });
                }
            }
        } else if (urlLower.includes('/propertyvaluation/calculateduty')) {
            const dateInput = document.getElementById('execution_date') || findInputByLabel("Execution Date") || findInputByLabel("निष्पादन तिथि");
            const faceValueInput = document.getElementById('face_value') || findInputByLabel("Face Value") || findInputByLabel("अंकित मूल्य");
            
            if (dateInput && faceValueInput) {
                let execDate = data.execution_date;
                if (!execDate) {
                    const today = new Date();
                    const dd = String(today.getDate()).padStart(2, '0');
                    const mm = String(today.getMonth() + 1).padStart(2, '0');
                    const yyyy = today.getFullYear();
                    execDate = `${dd}-${mm}-${yyyy}`;
                }
                
                showStatusToast(`Setting Execution Date: ${execDate} & Face Value: ${data.face_value}...`);
                setDatePickerValue(dateInput, execDate);
                setInputValue(faceValueInput, data.face_value.toString());
                
                setTimeout(() => {
                    showStatusToast("Submitting Stamp Duty (Clicking Calculate & Save)...");
                    const calcSaveBtn = document.querySelector('input[type="submit"][value="Calculate & Save"]') || 
                                        document.querySelector('button[value="Calculate & Save"]') ||
                                        triggerButtonByText("Calculate & Save") || 
                                        triggerButtonByText("गणना और सहेजें");
                    
                    if (calcSaveBtn) {
                        calcSaveBtn.click();
                        
                        // Poll for SweetAlert2 modal to appear
                        const checkInterval = setInterval(() => {
                            showStatusToast("Waiting for Calculation Saved popup...");
                            const swalOkBtn = document.querySelector('.swal2-confirm') || 
                                              Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'OK' && (b.offsetWidth > 0 || b.offsetHeight > 0));
                            if (swalOkBtn) {
                                showStatusToast("Confirming calculation (Clicking OK)...");
                                clearInterval(checkInterval);
                                
                                // Set the stampDutyCalculated state to true in local storage before clicking OK
                                chrome.storage.local.set({ stampDutyCalculated: true }, () => {
                                    swalOkBtn.click();
                                    setTimeout(() => {
                                        hideStatusToast();
                                    }, 1000);
                                    sendResponse({ success: true, message: 'Autofilled execution date, face value, saved, and confirmed!' });
                                });
                            }
                        }, 250);
                        
                        // Safety timeout (clear interval after 8 seconds)
                        setTimeout(() => {
                            clearInterval(checkInterval);
                        }, 8000);
                    } else {
                        showStatusToast("Calculate & Save button not found.", false);
                        sendResponse({ success: true, message: 'Autofilled execution date and face value!' });
                    }
                }, 800);
            } else {
                showStatusToast("Failed to find inputs.", false);
                sendResponse({ success: false, error: 'Could not locate Execution Date or Face Value inputs.' });
            }
        } else {
            sendResponse({ success: false, error: 'Make sure you are on the Property Detail or Calculate Duty screen.' });
        }
    } catch (err) {
        showStatusToast("Calculate duty encountered error.", false);
        sendResponse({ success: false, error: err.message });
    }
}
```

- [ ] **Step 2: Syntax check the script**

Run:
`node -c extensions/epanjiyan_autofill/content.js`
Expected: PASS with no syntax errors.

- [ ] **Step 3: Commit changes**

```bash
git add extensions/epanjiyan_autofill/content.js
git commit -m "feat: add state tracking to autofillCalculateDuty to prevent redirect loops"
```
