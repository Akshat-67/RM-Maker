// Content script to run on e-Panjiyan portal pages
console.log("[RM-Maker Autofill] Content script loaded on:", window.location.href);

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log("[RM-Maker Autofill] Message received:", request.action);
    
    try {
        switch (request.action) {
            case 'autofill_district':
                autofillDistrict(request.data, sendResponse);
                break;
            case 'autofill_login':
                autofillLogin(request.data, sendResponse);
                break;
            case 'autofill_details':
                autofillDetails(request.data, sendResponse);
                break;
            case 'autofill_calculate_duty':
                autofillCalculateDuty(request.data, sendResponse);
                break;
            case 'autofill_executants':
                autofillExecutants(request.data, sendResponse);
                break;
            case 'autofill_claimant':
                autofillClaimant(request.data, sendResponse);
                break;
            case 'autofill_witness1':
                autofillWitnessN(request.data, 0, sendResponse);
                break;
            case 'autofill_witness2':
                autofillWitnessN(request.data, 1, sendResponse);
                break;
            case 'set_presenter':
                setPresenter(request.data, sendResponse);
                break;
            case 'auto_run_flow':
                startAutoRunFlow(request.data, sendResponse);
                break;
            default:
                sendResponse({ success: false, error: 'Unknown action' });
        }
    } catch (e) {
        console.error("[RM-Maker Autofill] Exception in script:", e);
        sendResponse({ success: false, error: e.message });
    }
    return true; // Keep message channel open for async response
});

// =====================================================================
// AUTO-RUN: Resume automation on page load if a flow is active
// =====================================================================
let isRunningStep = false; // Prevent multiple overlapping triggers

function checkAndResumeFlow() {
    if (!chrome?.storage?.local) return;
    
    chrome.storage.local.get(['autoRunState', 'activeCaseData'], (result) => {
        let state = result.autoRunState;
        const caseData = result.activeCaseData;
        
        if (!state || !caseData) {
            // Remove badge if no active flow
            const badge = document.getElementById('rm-maker-autorun-badge');
            if (badge) badge.remove();
            return;
        }
        
        const url = window.location.href;
        const lowerUrl = url.toLowerCase();
        
        // --- SMART RECOVERY & TRANSITION AUTO-ADVANCE ---
        // If state is stuck in 'awaiting_district_modal' but we are on PropertyValuation, auto-advance state!
        if (state === 'awaiting_district_modal' && lowerUrl.includes('propertyvaluation') && !lowerUrl.includes('calculateduty')) {
            console.log('[RM-Maker AutoRun] Smart Recovery: Upgrading state to awaiting_property_valuation');
            state = 'awaiting_property_valuation';
            chrome.storage.local.set({ autoRunState: state });
        }
        
        // If state is stuck in 'awaiting_property_valuation' but we are on CalculateDuty page, auto-advance state!
        if (state === 'awaiting_property_valuation' && lowerUrl.includes('calculateduty')) {
            console.log('[RM-Maker AutoRun] Smart Recovery: Upgrading state to awaiting_calculate_duty');
            state = 'awaiting_calculate_duty';
            chrome.storage.local.set({ autoRunState: state });
        }
        
        // If state is stuck in 'duty_completed' but we are on PropertyDetail page, auto-advance state!
        if (state === 'duty_completed' && lowerUrl.includes('propertydetail')) {
            console.log('[RM-Maker AutoRun] Smart Recovery: Upgrading state to awaiting_party_detail_navigation');
            state = 'awaiting_party_detail_navigation';
            chrome.storage.local.set({ autoRunState: state });
        }
        
        // If state is stuck in 'awaiting_party_detail_navigation' but we are on Viewparty/PartyAdd page, auto-advance state!
        if (state === 'awaiting_party_detail_navigation' && (lowerUrl.includes('party/viewparty') || lowerUrl.includes('party/partyadd'))) {
            console.log('[RM-Maker AutoRun] Smart Recovery: Upgrading state to awaiting_executant_autofill');
            state = 'awaiting_executant_autofill';
            chrome.storage.local.set({ autoRunState: state });
        }
        
        updateFloatingStatus(state);
        
        // Prevent running multiple times on the same page state
        if (isRunningStep) return;
        
        console.log(`[RM-Maker AutoRun] Checking state. State: ${state}, URL: ${url}`);
        
        // Switch on state and call handlers
        switch (state) {
            case 'awaiting_property_valuation':
                if (lowerUrl.includes('propertyvaluation') && !lowerUrl.includes('calculateduty')) {
                    isRunningStep = true;
                    console.log('[RM-Maker AutoRun] Executing Document Details step...');
                    handleDocumentDetailsStep(caseData);
                    setTimeout(() => { isRunningStep = false; }, 2000);
                }
                break;
                
            case 'awaiting_calculate_duty':
                if (lowerUrl.includes('propertydetail') || lowerUrl.includes('calculateduty')) {
                    isRunningStep = true;
                    console.log('[RM-Maker AutoRun] Executing Calculate Duty step...');
                    handleCalculateDutyStep(caseData);
                    setTimeout(() => { isRunningStep = false; }, 2000);
                }
                break;
                
            case 'awaiting_party_detail_navigation':
                if (lowerUrl.includes('propertydetail')) {
                    isRunningStep = true;
                    console.log('[RM-Maker AutoRun] Executing Party Detail Navigation step...');
                    handlePartyDetailNavigationStep();
                    setTimeout(() => { isRunningStep = false; }, 2000);
                }
                break;
                
            case 'awaiting_executant_autofill':
            case 'awaiting_claimant_autofill':
            case 'awaiting_witness1_autofill':
            case 'awaiting_witness2_autofill':
                if (lowerUrl.includes('party/viewparty') || lowerUrl.includes('party/partyadd')) {
                    isRunningStep = true;
                    console.log(`[RM-Maker AutoRun] Executing step: ${state}`);
                    handlePartyAutofillSequence(state, caseData);
                    setTimeout(() => { isRunningStep = false; }, 2000);
                }
                break;
                
            default:
                break;
        }
    });
}

(function observeUrlChanges() {
    let lastUrl = window.location.href;
    
    // Check URL changes every 500ms
    setInterval(() => {
        const currentUrl = window.location.href;
        if (currentUrl !== lastUrl) {
            console.log(`[RM-Maker AutoRun] URL changed from ${lastUrl} to ${currentUrl}`);
            lastUrl = currentUrl;
            isRunningStep = false; // Reset lock on navigation
            
            // Wait 1.5s for page elements to load after route transition
            setTimeout(() => {
                checkAndResumeFlow();
            }, 1500);
        }
    }, 500);
    
    // Also run immediately on startup
    setTimeout(() => {
        checkAndResumeFlow();
    }, 1500);
})();

// =====================================================================
// HELPER FUNCTIONS
// =====================================================================

function findInputByLabel(text) {
    const cleanText = text.replace(/\s+/g, ' ').trim().toUpperCase();
    const labels = Array.from(document.querySelectorAll('label'));
    const matchedLabel = labels.find(l => {
        const cleanLabelText = l.textContent.replace(/\s+/g, ' ').trim().toUpperCase();
        return cleanLabelText.includes(cleanText);
    });
    
    if (matchedLabel) {
        if (matchedLabel.htmlFor) {
            const input = document.getElementById(matchedLabel.htmlFor);
            if (input) return input;
        }
        const childInput = matchedLabel.querySelector('input, select, textarea');
        if (childInput) return childInput;
        
        const nextEl = matchedLabel.nextElementSibling;
        if (nextEl) {
            const input = nextEl.querySelector('input, select, textarea') || (nextEl.tagName === 'INPUT' || nextEl.tagName === 'SELECT' || nextEl.tagName === 'TEXTAREA' ? nextEl : null);
            if (input) return input;
        }
        
        const parent = matchedLabel.parentElement;
        if (parent) {
            const input = parent.querySelector('input, select, textarea');
            if (input) return input;
        }
    }
    
    // Fallback: search inputs directly by placeholder, name, or id (case-insensitive substring match)
    const inputs = Array.from(document.querySelectorAll('input, textarea'));
    const cleanQuery = text.toLowerCase();
    
    const match = inputs.find(i => {
        const ph = (i.placeholder || "").toLowerCase();
        const name = (i.name || "").toLowerCase();
        const id = (i.id || "").toLowerCase();
        return ph.includes(cleanQuery) || name.includes(cleanQuery) || id.includes(cleanQuery);
    });
    
    return match || null;
}

function findSelectByLabel(text) {
    const cleanText = text.replace(/\s+/g, ' ').trim().toUpperCase();
    const labels = Array.from(document.querySelectorAll('label'));
    const matchedLabel = labels.find(l => {
        const cleanLabelText = l.textContent.replace(/\s+/g, ' ').trim().toUpperCase();
        return cleanLabelText.includes(cleanText);
    });
    
    if (matchedLabel) {
        if (matchedLabel.htmlFor) {
            const select = document.getElementById(matchedLabel.htmlFor);
            if (select && (select.tagName === 'SELECT' || select.tagName === 'NG-SELECT')) return select;
        }
        const sibling = matchedLabel.nextElementSibling;
        if (sibling) {
            const select = sibling.querySelector('select, ng-select') || (sibling.tagName === 'SELECT' || sibling.tagName === 'NG-SELECT' ? sibling : null);
            if (select) return select;
        }
        const parent = matchedLabel.parentElement;
        if (parent) {
            const select = parent.querySelector('select, ng-select');
            if (select) return select;
        }
    }
    
    // Fallback: search selects directly
    const selects = Array.from(document.querySelectorAll('select, ng-select'));
    const cleanQuery = text.toLowerCase();
    
    const match = selects.find(s => {
        const name = (s.name || "").toLowerCase();
        const id = (s.id || "").toLowerCase();
        return name.includes(cleanQuery) || id.includes(cleanQuery);
    });
    
    return match || null;
}

function findIdDetailsInput() {
    return findInputByLabel("id Details") || 
           findInputByLabel("आईडी विवरण") || 
           findInputByLabel("ID Number") ||
           document.querySelector('input[id*="idno" i], input[name*="idno" i], input[id*="idProof" i], input[name*="idProof" i], input[id*="uid" i], input[name*="uid" i], input[id*="aadhar" i], input[name*="aadhar" i]') ||
           Array.from(document.querySelectorAll('input')).find(i => {
               const id = (i.id || "").toLowerCase();
               const name = (i.name || "").toLowerCase();
               const ph = (i.placeholder || "").toLowerCase();
               return id.includes('proof') || name.includes('proof') || id.includes('idno') || name.includes('idno') || ph.includes('aadhar') || ph.includes('id');
           });
}

function getField(fieldName) {
    const selectorMap = {
        presenter: ['#is_presentor', '#is_presenter', 'input[name*="present" i]', 'input[id*="present" i]'],
        stamppurchaser: ['#chkstampPurchaser', '#chkstamp_purchaser', 'input[name*="stamp" i]', 'input[id*="stamp" i]'],
        partyNameEn: ['#txtpartyname', 'input[name="partyname" i]', 'input[id*="partyname" i]', 'input[name*="partyname" i]'],
        relNameEn: ['#txtfathername', '#txtrelationname', '#txtfhname', '#txtfh_name', 'input[name*="father" i]', 'input[id*="father" i]', 'input[name*="relation" i]', 'input[id*="relation" i]', 'input[id*="fh" i]', 'input[name*="fh" i]'],
        dob: ['#txtdob', 'input[name="dob" i]', 'input[id*="dob" i]', 'input[name*="dob" i]'],
        age: ['#txtAge', '#txtage', 'input[name="age" i]', 'input[id*="age" i]', 'input[name*="age" i]'],
        category: ['#ddlcategory', '#category', 'select[name*="category" i]', 'select[id*="category" i]'],
        casteEn: ['#txtcaste', 'input[name="caste" i]', 'input[id*="caste" i]', 'input[name*="caste" i]'],
        occupation: ['#ddloccupation', '#occupation', 'select[name*="occupation" i]', 'select[id*="occupation" i]'],
        idProof: ['#ddlidproof', '#ddlIdproof', '#ddlIdProof', 'select[name*="idproof" i]', 'select[id*="idproof" i]', 'select[name*="id_proof" i]'],
        idDetails: ['#txtiddetails', '#txtidproofno', '#txtidno', '#txtidproofdetails', '#iddetails', 'input[name*="iddetails" i]', 'input[id*="iddetails" i]', 'input[name*="idno" i]', 'input[id*="idno" i]', 'input[name*="idproof" i]', 'input[id*="idproof" i]'],
        pan: ['#txtpancardno', '#txtpan', '#pan', 'input[name*="pan" i]', 'input[id*="pan" i]'],
        houseNo: ['#txthouseno', '#txthouse_no', '#houseno', 'input[name*="house" i]', 'input[id*="house" i]'],
        colony: ['#txtpartycolony', '#txtcolony', '#colony', 'input[name*="colony" i]', 'input[id*="colony" i]'],
        area: ['#txtpartyarea', '#txtarea', '#area', '#txtlocation', 'input[name*="area" i]', 'input[id*="area" i]', 'input[name*="location" i]'],
        city: ['#txtCity', '#txtcity', '#city', 'input[name*="city" i]', 'input[id*="city" i]'],
        pincode: ['#txtpincode', '#pincode', 'input[name*="pin" i]', 'input[id*="pin" i]']
    };
    
    const selectors = selectorMap[fieldName];
    if (!selectors) return null;
    
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el) return el;
    }
    
    // If still not found, try finding by label as fallback
    if (fieldName === 'partyNameEn') return findInputByLabel("Party Name") || findInputByLabel("पक्षकार का नाम");
    if (fieldName === 'relNameEn') return findInputByLabel("Father/Husband Name") || findInputByLabel("Father/Husband") || findInputByLabel("पिता/पति का नाम");
    if (fieldName === 'dob') return findInputByLabel("DOB") || findInputByLabel("जन्मतिथि");
    if (fieldName === 'age') return findInputByLabel("Age") || findInputByLabel("आयु");
    if (fieldName === 'category') return findSelectByLabel("Category") || findSelectByLabel("श्रेणी");
    if (fieldName === 'casteEn') return findInputByLabel("Caste") || findInputByLabel("जाति");
    if (fieldName === 'occupation') return findSelectByLabel("Occupation") || findSelectByLabel("व्यवसाय");
    if (fieldName === 'idProof') return findSelectByLabel("Photo id Proof") || findSelectByLabel("फोटो आईडी प्रूफ");
    if (fieldName === 'idDetails') return findIdDetailsInput();
    if (fieldName === 'pan') return findInputByLabel("PAN Card No") || findInputByLabel("पैन कार्ड नं");
    if (fieldName === 'houseNo') return findInputByLabel("House No") || findInputByLabel("मकान नं");
    if (fieldName === 'colony') return findInputByLabel("Colony") || findInputByLabel("कालोनी");
    if (fieldName === 'area') return findInputByLabel("Area / Location") || findInputByLabel("क्षेत्र / स्थान");
    if (fieldName === 'city') return findInputByLabel("City") || findInputByLabel("शहर");
    if (fieldName === 'pincode') return findInputByLabel("Pin Code") || findInputByLabel("पिन कोड");
    
    return null;
}

function cleanSalutation(name) {
    if (!name) return "";
    return name.replace(/^(MR|MRS|MS|SHRI|SMT|SH|DR|LATE)\b\.?\s*/i, '').trim();
}

async function fillPartyFormFields(partyData, isPresenter, isPurchaser) {
    console.log("[RM-Maker] Starting fillPartyFormFields for:", partyData.name_en);
    
    // 1. Checkboxes
    const presenterBox = getField('presenter');
    const purchaserBox = getField('stamppurchaser');
    
    if (presenterBox) {
        presenterBox.checked = isPresenter;
        presenterBox.dispatchEvent(new Event('change', { bubbles: true }));
        presenterBox.dispatchEvent(new Event('click', { bubbles: true }));
    }
    if (purchaserBox) {
        purchaserBox.checked = isPurchaser;
        purchaserBox.dispatchEvent(new Event('change', { bubbles: true }));
        purchaserBox.dispatchEvent(new Event('click', { bubbles: true }));
    }
    
    // 2. Names (English only, stripped of salutations like MR/MRS)
    const partyNameEn = getField('partyNameEn');
    const relNameEn = getField('relNameEn');
    setInputValue(partyNameEn, cleanSalutation(partyData.name_en));
    setInputValue(relNameEn, cleanSalutation(partyData.relation_name_en));
    
    // 3. Gender
    if (partyData.gender === 'FEMALE') {
        const femaleRadio = document.getElementById('rbtfemale') || document.querySelector('input[type="radio"][value="F"]') || document.querySelector('input[type="radio"][id*="female" i]');
        if (femaleRadio) {
            femaleRadio.checked = true;
            femaleRadio.click();
            femaleRadio.dispatchEvent(new Event('change', { bubbles: true }));
        }
    } else if (partyData.gender === 'TRANSGENDER' || partyData.gender === 'TRANS') {
        const transRadio = document.getElementById('rbttransgender') || document.querySelector('input[type="radio"][value="T"]') || document.querySelector('input[type="radio"][id*="trans" i]');
        if (transRadio) {
            transRadio.checked = true;
            transRadio.click();
            transRadio.dispatchEvent(new Event('change', { bubbles: true }));
        }
    } else {
        const maleRadio = document.getElementById('rbtmale') || document.querySelector('input[type="radio"][value="M"]') || document.querySelector('input[type="radio"][id*="male" i]');
        if (maleRadio) {
            maleRadio.checked = true;
            maleRadio.click();
            maleRadio.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
    
    // 4. DOB / Age
    const dobInput = document.getElementById('txtdob') || getField('dob');
    const ageInput = getField('age');
    if (dobInput) {
        let dobValue = "";
        if (partyData.dob) {
            // Normalize separators to slashes
            dobValue = partyData.dob.replace(/[-\.]/g, '/');
            // If it's just a 4-digit year, pad to 01/01/YYYY
            if (dobValue.length === 4 && /^\d+$/.test(dobValue)) {
                dobValue = `01/01/${dobValue}`;
            }
        } else if (partyData.age) {
            const currentYear = new Date().getFullYear();
            const birthYear = currentYear - parseInt(partyData.age);
            dobValue = `01/01/${birthYear}`;
        } else {
            dobValue = "01/01/1985";
        }
        
        console.log("[RM-Maker] Writing DOB using page-context datepicker:", dobValue);
        setDatePickerValue(dobInput, dobValue);
    } else if (ageInput) {
        setInputValue(ageInput, partyData.age || "40");
    }
    
    // 5. Category (Select)
    const catSelect = getField('category');
    if (catSelect) {
        await setSelectValueByText(catSelect, "General");
    }
    
    // 6. Caste (English field only!) & जाति (Hindi field - hardcoded always to हिन्दू)
    const casteEn = getField('casteEn');
    if (casteEn) {
        setInputValue(casteEn, "HINDU");
    }
    const casteHi = document.getElementById('txtcastehindi') || document.querySelector('input[name*="casteHindi" i]') || document.querySelector('input[id*="castehindi" i]');
    if (casteHi) {
        setInputValue(casteHi, "हिन्दू");
    }
    
    // 7. Occupation (Select)
    const occSelect = getField('occupation');
    if (occSelect) {
        await setSelectValueByText(occSelect, "Other");
    }
    
    // 8. Photo ID Proof (Select)
    const idSelect = getField('idProof');
    if (idSelect) {
        await setSelectValueByText(idSelect, "Other than above");
    }
    
    // 9. ID Details (Aadhaar Number) & PAN Card
    const idDetails = getField('idDetails');
    const sampleAadhaar = "123456789012"; // Safety sample
    if (idDetails) {
        setInputValue(idDetails, partyData.id || partyData.aadhaar || sampleAadhaar);
    }
    
    if (partyData.pan) {
        const panInput = getField('pan');
        if (panInput) {
            setInputValue(panInput, partyData.pan);
        }
    }
    
    // 10. Address
    if (partyData.address) {
        const houseInput = getField('houseNo');
        const colonyInput = getField('colony');
        const areaInput = getField('area');
        const cityInput = getField('city');
        const pinInput = getField('pincode');
        
        setInputValue(houseInput, partyData.address.house_no || "");
        setInputValue(colonyInput, partyData.address.colony || "");
        setInputValue(areaInput, partyData.address.area || "");
        setInputValue(cityInput, partyData.address.city || "JAIPUR");
        setInputValue(pinInput, partyData.address.pincode || "");
    }
    
    console.log("[RM-Maker] Completed fillPartyFormFields for:", partyData.name_en);
}


function triggerJQuerySelect(elementId, value) {
    try {
        const script = document.createElement('script');
        script.textContent = `
            (function() {
                const el = document.getElementById("${elementId}");
                const $ = window.jQuery || window.$;
                if (el && $) {
                    $(el).val("${value}").trigger('change');
                }
            })();
        `;
        (document.head || document.documentElement).appendChild(script);
        script.remove();
    } catch (e) {
        console.error("[RM-Maker] Select injection failed:", e);
    }
}

function setDatePickerValue(inputEl, value) {
    if (!inputEl) return;
    
    // Ensure the input element has an ID
    if (!inputEl.id) {
        inputEl.id = 'date_' + Math.random().toString(36).substring(2, 9);
    }
    
    // 1. Update in extension context
    inputEl.removeAttribute('readonly');
    setInputValue(inputEl, value);
    inputEl.setAttribute('readonly', 'readonly');
    
    // 2. Update in page context (to trigger jQuery datepicker widget)
    try {
        const script = document.createElement('script');
        script.textContent = `
            (function() {
                const el = document.getElementById("${inputEl.id}");
                const $ = window.jQuery || window.$;
                if (el && $) {
                    $(el).removeAttr('readonly');
                    $(el).val("${value}").trigger('change').trigger('input');
                    if (typeof $(el).datepicker === 'function') {
                        try {
                            $(el).datepicker('setDate', "${value}");
                        } catch(e) { console.error("datepicker setDate failed:", e); }
                    }
                    $(el).attr('readonly', 'readonly');
                }
            })();
        `;
        (document.head || document.documentElement).appendChild(script);
        script.remove();
    } catch (e) {
        console.error("[RM-Maker] Error injecting datepicker script:", e);
    }
}

async function selectNgSelectOption(ngSelectEl, text) {
    if (!ngSelectEl) return false;
    
    console.log("[content.js] Clicking ng-select to open options...");
    const container = ngSelectEl.querySelector('.ng-select-container') || ngSelectEl.querySelector('.ng-arrow-wrapper') || ngSelectEl;
    container.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    container.click();
    
    for (let i = 0; i < 20; i++) {
        await new Promise(r => setTimeout(r, 100));
        const options = Array.from(document.querySelectorAll('.ng-option, [role="option"]'));
        const matchedOption = options.find(opt => {
            const optText = opt.textContent.toUpperCase();
            return optText.includes(text.toUpperCase()) || (text.toUpperCase() === 'JAIPUR' && optText.includes('जयपुर'));
        });
        
        if (matchedOption) {
            console.log("[content.js] Found matching ng-select option:", matchedOption.textContent);
            matchedOption.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
            matchedOption.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
            matchedOption.click();
            matchedOption.dispatchEvent(new Event('change', { bubbles: true }));
            return true;
        }
    }
    console.error("[content.js] Failed to find ng-select option for text:", text);
    return false;
}

async function setSelectValueByText(selectEl, text) {
    if (!selectEl) return false;
    
    if (selectEl.tagName.toUpperCase() === 'NG-SELECT') {
        return await selectNgSelectOption(selectEl, text);
    }
    
    console.log(`[RM-Maker] Selecting option "${text}" in dropdown...`);
    
    // Wait up to 3 seconds for options to load and the matched option to be present
    for (let i = 0; i < 30; i++) {
        const options = Array.from(selectEl.options);
        const isExactJaipur = text.toUpperCase() === 'JAIPUR';
        const matchedOption = options.find(opt => {
            const optText = opt.text.toUpperCase();
            if (isExactJaipur) {
                return optText.includes('JAIPUR') || optText.includes('जयपुर');
            }
            return optText.includes(text.toUpperCase()) || optText.replace(/\s+/g, '').includes(text.toUpperCase().replace(/\s+/g, ''));
        });
        
        if (matchedOption) {
            console.log(`[RM-Maker] Found option matching "${text}":`, matchedOption.text);
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
        await new Promise(r => setTimeout(r, 100)); // Wait 100ms
    }
    
    console.error(`[RM-Maker] Failed to locate option matching "${text}" in dropdown.`);
    return false;
}

function setInputValue(inputEl, value) {
    if (!inputEl) return false;
    inputEl.value = value;
    inputEl.dispatchEvent(new Event('input', { bubbles: true }));
    inputEl.dispatchEvent(new Event('change', { bubbles: true }));
    inputEl.dispatchEvent(new Event('blur', { bubbles: true }));
    return true;
}

function clickRadioByValueOrLabel(labelText) {
    console.log(`[RM-Maker] Attempting to click radio: "${labelText}"`);
    
    // Normalize target text
    const cleanTarget = labelText.replace(/\s+/g, ' ').trim().toUpperCase();
    
    // 1. Search actual <label> elements first (most standard way)
    const labels = Array.from(document.querySelectorAll('label'));
    let matchedLabel = labels.find(l => {
        const txt = l.textContent.replace(/\s+/g, ' ').trim().toUpperCase();
        return txt === cleanTarget || txt.includes(cleanTarget);
    });
    
    // 2. Fallback to spans, divs, or inputs
    if (!matchedLabel) {
        const otherEls = Array.from(document.querySelectorAll('span, div, input[type="radio"]'));
        matchedLabel = otherEls.find(el => {
            if (el.tagName.toUpperCase() === 'INPUT') {
                return el.value && el.value.toUpperCase() === cleanTarget;
            }
            const txt = el.textContent.replace(/\s+/g, ' ').trim().toUpperCase();
            // Restrict size to avoid matching large container divs
            return txt.length < 80 && (txt === cleanTarget || txt.includes(cleanTarget));
        });
    }
    
    if (matchedLabel) {
        console.log(`[RM-Maker] Matched element for radio "${labelText}":`, matchedLabel);
        
        // Try clicking the matched element directly
        matchedLabel.click();
        
        // Now locate the actual radio input element
        let radio = null;
        if (matchedLabel.tagName.toUpperCase() === 'INPUT' && matchedLabel.type === 'radio') {
            radio = matchedLabel;
        } else {
            // Check if it contains a radio input
            radio = matchedLabel.querySelector('input[type="radio"]');
            
            // Check siblings and parent container
            if (!radio) {
                const parent = matchedLabel.parentElement;
                if (parent) {
                    radio = parent.querySelector('input[type="radio"]');
                }
            }
            // Check closest container
            if (!radio) {
                const container = matchedLabel.closest('.radio, .radio-inline, div, td, li');
                if (container) {
                    radio = container.querySelector('input[type="radio"]');
                }
            }
        }
        
        if (radio) {
            console.log('[RM-Maker] Clicking associated radio input:', radio);
            radio.checked = true;
            radio.click();
            radio.dispatchEvent(new Event('change', { bubbles: true }));
            radio.dispatchEvent(new Event('click', { bubbles: true }));
            return true;
        }
    }
    
    // 3. Last resort fallback: Match radio button value directly using common mappings
    const radios = Array.from(document.querySelectorAll('input[type="radio"]'));
    let valueMatch = radios.find(r => r.value && r.value.toUpperCase() === cleanTarget);
    
    // Contextual value mapping (e.g. "Self (स्वयं)" -> "S", "Urban (शहरी)" -> "U", "Rural (ग्रामीण)" -> "R")
    if (!valueMatch) {
        let mappedVal = "";
        if (cleanTarget.includes("SELF") || cleanTarget.includes("स्वयं")) mappedVal = "S";
        else if (cleanTarget.includes("URBAN") || cleanTarget.includes("शहरी")) mappedVal = "U";
        else if (cleanTarget.includes("RURAL") || cleanTarget.includes("ग्रामीण")) mappedVal = "R";
        
        if (mappedVal) {
            valueMatch = radios.find(r => r.value && r.value.toUpperCase() === mappedVal);
        }
    }
    
    if (valueMatch) {
        console.log('[RM-Maker] Found direct radio value match:', valueMatch);
        valueMatch.checked = true;
        valueMatch.click();
        valueMatch.dispatchEvent(new Event('change', { bubbles: true }));
        valueMatch.dispatchEvent(new Event('click', { bubbles: true }));
        return true;
    }
    
    console.error(`[RM-Maker] Failed to locate radio button for: "${labelText}"`);
    return false;
}

function triggerButtonByText(text) {
    const buttons = Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"], a.btn'));
    const matchedBtn = buttons.find(b => b.textContent.trim().toUpperCase().includes(text.toUpperCase()) || (b.value && b.value.toUpperCase().includes(text.toUpperCase())));
    if (matchedBtn) {
        matchedBtn.click();
        return true;
    }
    return false;
}

// =====================================================================
// SHARED: Bypass the Party Verification Modal
// Modal flow (from screenshots):
//   1. Select "Public" (or "Bank" for claimant) from dropdown
//   2. Radio buttons appear: "Jan Aadhar With OTP", "Aadhar Card With OTP", "Without OTP Verification"
//   3. Click "Without OTP Verification" radio
//   4. Submit button appears → click it
//   5. Navigates to /Party/PartyAdd form
// IMPORTANT: No alert() calls — they block Angular rendering!
// =====================================================================

function bypassVerificationModal(verifyType, sendResponse, successMsg) {
    const debugLog = []; // Collect all debug info for one final alert
    
    // Step 1: Wait for modal to fully render (2s)
    setTimeout(() => {
        const allSelects = Array.from(document.querySelectorAll('select'));
        debugLog.push(`Step 1: Found ${allSelects.length} <select> elements`);
        allSelects.forEach((s, i) => {
            const opts = Array.from(s.options).map(o => o.text).join(', ');
            debugLog.push(`  select[${i}]: id="${s.id}" name="${s.name}" opts=[${opts}]`);
        });
        
        const verificationTypeSelect = allSelects.find(s => {
            const opts = Array.from(s.options).map(o => o.text.toUpperCase());
            return opts.some(t => t.includes('PUBLIC') || t.includes('BANK') || t.includes('सार्वजनिक'));
        });
        
        if (!verificationTypeSelect) {
            debugLog.push("Step 1: FAILED — No dropdown with Public/Bank found");
            alert("[RM-Maker DEBUG]\n" + debugLog.join("\n"));
            sendResponse({ success: false, error: 'Verification modal dropdown not found.' });
            return;
        }
        debugLog.push(`Step 1: SUCCESS — Found verification dropdown`);
        
        // Step 2: Select Public or Bank
        setSelectValueByText(verificationTypeSelect, verifyType);
        const selectedText = verificationTypeSelect.options[verificationTypeSelect.selectedIndex]?.text || "(none)";
        debugLog.push(`Step 2: Set dropdown to "${selectedText}"`);
        console.log("[RM-Maker]", debugLog.join(" | "));
        
        // Step 3: Wait 1.5s for Angular to render the radio buttons after dropdown change
        setTimeout(() => {
            const allRadios = Array.from(document.querySelectorAll('input[type="radio"]'));
            debugLog.push(`Step 3: Found ${allRadios.length} radio buttons`);
            allRadios.forEach((r, i) => {
                const lbl = r.labels?.[0]?.textContent?.trim() ||
                            r.nextSibling?.textContent?.trim() ||
                            r.parentElement?.textContent?.trim().substring(0, 80) ||
                            "(no label)";
                debugLog.push(`  radio[${i}]: id="${r.id}" name="${r.name}" val="${r.value}" lbl="${lbl.substring(0, 60)}"`);
            });
            
            const withoutOtpRadio = allRadios.find(r => {
                const combined = [
                    r.labels?.[0]?.textContent || "",
                    r.nextSibling?.textContent || "",
                    r.parentElement?.textContent || "",
                    r.value || "",
                    r.id || ""
                ].join(" ").toLowerCase();
                return combined.includes("without otp") || 
                       combined.includes("without_otp") ||
                       combined.includes("ओटीपी के बिना") || 
                       combined.includes("ओटीपी सत्यापन के बिना");
            });
            
            if (!withoutOtpRadio) {
                debugLog.push("Step 3: FAILED — 'Without OTP Verification' radio NOT found. ABORTING.");
                alert("[RM-Maker DEBUG]\n" + debugLog.join("\n"));
                sendResponse({ success: false, error: 'Without OTP option not found. See console for debug info.' });
                return;
            }
            debugLog.push(`Step 3: SUCCESS — Found Without OTP radio (id="${withoutOtpRadio.id}")`);
            
            // Step 4: Click the Without OTP radio
            withoutOtpRadio.checked = true;
            withoutOtpRadio.click();
            withoutOtpRadio.dispatchEvent(new Event('change', { bubbles: true }));
            debugLog.push(`Step 4: Clicked Without OTP radio. checked=${withoutOtpRadio.checked}`);
            console.log("[RM-Maker]", debugLog.join(" | "));
            
            // Step 5: Wait 1.5s for Submit button to appear after radio selection
            setTimeout(() => {
                // Target the Submit button directly by its known ID
                const submitBtn = document.getElementById('btnsubmit');
                debugLog.push(`Step 5: btnsubmit element = ${submitBtn ? 'FOUND' : 'NOT FOUND'}`);
                
                if (submitBtn) {
                    console.log("[RM-Maker] Clicking #btnsubmit...");
                    submitBtn.click();
                    debugLog.push("Step 5: SUCCESS — Clicked #btnsubmit!");
                    console.log("[RM-Maker] MODAL BYPASS COMPLETE:", debugLog.join(" | "));
                    sendResponse({ success: true, message: successMsg });
                } else {
                    // Fallback: try by text
                    const clicked = triggerButtonByText("Submit") || triggerButtonByText("प्रस्तुत करें");
                    if (clicked) {
                        debugLog.push("Step 5: SUCCESS — Clicked Submit by text fallback");
                        console.log("[RM-Maker] MODAL BYPASS COMPLETE:", debugLog.join(" | "));
                        sendResponse({ success: true, message: successMsg });
                    } else {
                        debugLog.push("Step 5: FAILED — Submit button not found by ID or text");
                        alert("[RM-Maker DEBUG]\n" + debugLog.join("\n"));
                        sendResponse({ success: false, error: 'Submit button not found.' });
                    }
                }
            }, 1500); // Wait for Submit button to render
        }, 1500); // Wait for radio buttons to render
    }, 2000); // Wait for modal to render
}

// =====================================================================
// 0. Autofill District & Navigate
// =====================================================================

async function autofillDistrict(data, sendResponse) {
    try {
        console.log("[content.js] Running autofillDistrict...");
        
        let distSelect = document.querySelector('ng-select, select[id*="district" i], select[name*="district" i], select[class*="district" i], select[id*="dist" i], select[name*="dist" i]');
        
        if (!distSelect) {
            const selects = Array.from(document.querySelectorAll('select, ng-select'));
            if (selects.length === 1) {
                distSelect = selects[0];
            } else {
                distSelect = selects.find(s => {
                    if (s.options) {
                        return Array.from(s.options).some(o => {
                            const txt = o.text.toUpperCase();
                            return txt.includes('JAIPUR') || txt.includes('जयपुर');
                        });
                    }
                    const placeholder = s.querySelector('.ng-placeholder')?.textContent || "";
                    return placeholder.toUpperCase().includes('DISTRICT') || placeholder.includes('जिला');
                });
            }
        }
        
        if (!distSelect) {
            sendResponse({ success: false, error: 'District select dropdown not found on this page.' });
            return;
        }
        
        let optionsLoaded = false;
        if (distSelect.tagName.toUpperCase() === 'NG-SELECT') {
            optionsLoaded = true;
        } else {
            for (let i = 0; i < 15; i++) {
                if (distSelect.options.length > 1) {
                    optionsLoaded = true;
                    break;
                }
                await new Promise(r => setTimeout(r, 200));
            }
        }
        
        if (!optionsLoaded) {
            sendResponse({ success: false, error: 'Select dropdown options failed to load.' });
            return;
        }
        
        if (await setSelectValueByText(distSelect, "JAIPUR")) {
            setTimeout(() => {
                const siblingCol = distSelect.parentElement.nextElementSibling || distSelect.closest('.row')?.querySelector('.col-3');
                const arrowBtn = document.querySelector('.login-arrow') || 
                                 siblingCol?.querySelector('.login-arrow, span, a, button, input') || 
                                 document.querySelector('.fa-arrow-right, .fa-arrow-circle-right, button[class*="arrow"], a[class*="arrow"]');
                if (arrowBtn) {
                    arrowBtn.click();
                    sendResponse({ success: true, message: 'Selected JAIPUR and clicked navigation arrow!' });
                } else {
                    const allBtns = Array.from(document.querySelectorAll('button, a, input[type="button"]'));
                    if (allBtns.length > 0) {
                        allBtns[0].click();
                        sendResponse({ success: true, message: 'Selected JAIPUR and clicked first button!' });
                    } else {
                        sendResponse({ success: true, message: 'Selected JAIPUR but could not find the arrow button.' });
                    }
                }
            }, 500);
        } else {
            sendResponse({ success: false, error: 'Could not set dropdown value to JAIPUR.' });
        }
    } catch (err) {
        sendResponse({ success: false, error: err.message });
    }
}

// =====================================================================
// 1. Autofill Login
// =====================================================================

function autofillLogin(data, sendResponse) {
    let mobileInput = document.querySelector('input[id*="mobile" i], input[id*="mob" i], input[name*="mobile" i], input[placeholder*="Mobile" i], input[placeholder*="Enter Mobile" i], input[placeholder*="मोबाइल" i]');
    
    if (!mobileInput) {
        const inputs = Array.from(document.querySelectorAll('input'));
        mobileInput = inputs.find(i => {
            const id = (i.id || "").toLowerCase();
            const name = (i.name || "").toLowerCase();
            const placeholder = (i.placeholder || "").toLowerCase();
            return id.includes('mob') || name.includes('mob') || placeholder.includes('mob') || placeholder.includes('mobile') || placeholder.includes('मोबाइल');
        });
    }
    
    if (!mobileInput) {
        const visibleInputs = Array.from(document.querySelectorAll('input')).filter(i => {
            const type = i.type || "text";
            return ["text", "number", "tel"].includes(type) && i.offsetWidth > 0 && i.offsetHeight > 0;
        });
        if (visibleInputs.length > 0) {
            mobileInput = visibleInputs[0];
        }
    }
    
    if (!mobileInput) {
        sendResponse({ success: false, error: 'Mobile number input field not found.' });
        return;
    }
    
    setInputValue(mobileInput, data.mobile);
    
    setTimeout(() => {
        const otpTriggered = triggerButtonByText("Get OTP");
        if (otpTriggered) {
            sendResponse({ success: true, message: 'Autofilled mobile number and clicked Get OTP!' });
        } else {
            sendResponse({ success: true, message: 'Autofilled mobile but could not auto-click Get OTP.' });
        }
    }, 100);
}

// =====================================================================
// 2. Autofill Document Details (Step 4 in notes)
// =====================================================================

async function autofillDetails(data, sendResponse) {
    try {
        console.log('[RM-Maker] Starting autofillDetails...');
        // Select Urban
        clickRadioByValueOrLabel("Urban (शहरी)");
        
        // Select Self
        setTimeout(async () => {
            try {
                const clickedSelf = clickRadioByValueOrLabel("Self (स्वयं)");
                if (!clickedSelf) {
                    sendResponse({ success: false, error: 'Could not click Transfer status: Self (स्वयं) radio button.' });
                    return;
                }
                
                // Wait for Self Modal
                console.log('[RM-Maker] Waiting for category modal...');
                let modalBody = null;
                for (let i = 0; i < 25; i++) {
                    const modals = Array.from(document.querySelectorAll('.modal-body, ngb-modal-window, .modal-dialog, .modal-content, .modal'));
                    modalBody = modals.find(m => m.offsetWidth > 0 || m.offsetHeight > 0 || m.getBoundingClientRect().width > 0);
                    if (modalBody) break;
                    await new Promise(r => setTimeout(r, 150));
                }
                
                if (!modalBody) {
                    sendResponse({ success: false, error: 'Could not find the category modal window after clicking Self.' });
                    return;
                }
                console.log('[RM-Maker] Category modal found. Matching gender card:', data.gender_card);
                
                // Find the correct gender card
                let targetCard = null;
                for (let i = 0; i < 15; i++) {
                    const elements = Array.from(modalBody.querySelectorAll('*'));
                    const cardCandidates = elements.filter(el => {
                        const cleanTxt = el.textContent.replace(/\s+/g, '').toUpperCase();
                        if (data.gender_card === 'JOINT') {
                            return cleanTxt.includes('संयुक्त') || cleanTxt.includes('JOINT');
                        } else if (data.gender_card === 'FEMALE_GEN') {
                            return (cleanTxt.includes('महिला') && cleanTxt.includes('GEN')) || cleanTxt.includes('FEMALE');
                        } else {
                            return (cleanTxt.includes('पुरूष') && cleanTxt.includes('GEN')) || (cleanTxt.includes('पुरुष') && cleanTxt.includes('GEN')) || cleanTxt.includes('MALE');
                        }
                    });
                    
                    if (cardCandidates.length > 0) {
                        cardCandidates.sort((a, b) => a.textContent.length - b.textContent.length);
                        targetCard = cardCandidates[0];
                        break;
                    }
                    await new Promise(r => setTimeout(r, 150));
                }
                
                if (targetCard) {
                    console.log('[RM-Maker] Found matching gender card, clicking...', targetCard.textContent);
                    targetCard.click();
                    const parentLabel = targetCard.closest('label, span.radio-btn');
                    if (parentLabel) parentLabel.click();
                    
                    await new Promise(r => setTimeout(r, 400));
                    const modalButtons = Array.from(modalBody.querySelectorAll('button, a, input[type="button"]'));
                    const continueBtn = modalButtons.find(b => {
                        const txt = b.textContent.trim().toUpperCase();
                        return txt.includes('CONTINUE') || txt.includes('SAVE') || txt.includes('सहेजें') || txt.includes('आगे बढ़ें') || txt.includes('OK');
                    });
                    if (continueBtn) {
                        console.log('[RM-Maker] Clicking modal continue button...');
                        continueBtn.click();
                    }
                    
                    await new Promise(r => setTimeout(r, 800));
                    
                    // Fill Document Type
                    console.log('[RM-Maker] Selecting Document Type...');
                    const docTypeSelect = findSelectByLabel("Document Type") || findSelectByLabel("दस्तावेज़ का प्रकार") || document.querySelector('ng-select');
                    await setSelectValueByText(docTypeSelect, "Mortgage/ Charge");
                    
                    await new Promise(r => setTimeout(r, 600));
                    console.log('[RM-Maker] Selecting SubType...');
                    const subTypeSelect = findSelectByLabel("SubType") || findSelectByLabel("उप-प्रकार");
                    await setSelectValueByText(subTypeSelect, "(b)Mortgage deed without possession");
                    
                    await new Promise(r => setTimeout(r, 600));
                    console.log('[RM-Maker] Selecting Category...');
                    const catSelect = findSelectByLabel("Category") || findSelectByLabel("श्रेणी");
                    await setSelectValueByText(catSelect, "General");
                    
                    await new Promise(r => setTimeout(r, 600));
                    console.log('[RM-Maker] Selecting SRO...');
                    const sroSelect = findSelectByLabel("SRO") || findSelectByLabel("उप पंजीयक");
                    await setSelectValueByText(sroSelect, data.sro || "JAIPUR-VII");
                    
                    await new Promise(r => setTimeout(r, 600));
                    console.log('[RM-Maker] Selecting Tehsil...');
                    const tehsilSelect = findSelectByLabel("Tehsil") || findSelectByLabel("तहसील");
                    await setSelectValueByText(tehsilSelect, data.tehsil || "JAIPUR");
                    
                    sendResponse({ success: true, message: 'Autofilled all details! Review and click Save.' });
                    
                } else {
                    sendResponse({ success: false, error: `Could not find the card matching ${data.gender_card} in the modal.` });
                }
            } catch (innerErr) {
                console.error('[RM-Maker] Error in async autofillDetails steps:', innerErr);
                sendResponse({ success: false, error: innerErr.message });
            }
        }, 300);
    } catch (err) {
        console.error('[RM-Maker] Error in autofillDetails wrapper:', err);
        sendResponse({ success: false, error: err.message });
    }
}

// =====================================================================
// 2b. Calculate Duty (Step 5-6 in notes)
// =====================================================================

function autofillCalculateDuty(data, sendResponse) {
    try {
        const url = window.location.href;
        
        if (url.includes('/PropertyValuation/PropertyDetail')) {
            const calcBtn = triggerButtonByText("Calculate Duty") || triggerButtonByText("ड्यूटी की गणना करें");
            if (calcBtn) {
                sendResponse({ success: true, message: 'Clicked Calculate Duty!' });
            } else {
                const preValBtn = triggerButtonByText("Pre Valuation Report") || triggerButtonByText("पूर्व मूल्यांकन रिपोर्ट");
                if (preValBtn) {
                    sendResponse({ success: true, message: 'Opened Pre Valuation Report!' });
                } else {
                    const partyDetailBtn = triggerButtonByText("Party Detail") || triggerButtonByText("पक्षकार विवरण") || Array.from(document.querySelectorAll('button, a')).find(b => b.textContent.includes('Party Detail') || b.textContent.includes('पक्षकार विवरण'));
                    if (partyDetailBtn) {
                        partyDetailBtn.click();
                        sendResponse({ success: true, message: 'Proceeding to Party Details screen...' });
                    } else {
                        sendResponse({ success: false, error: 'Could not find relevant buttons on this screen.' });
                    }
                }
            }
        } else if (url.includes('/PropertyValuation/CalculateDuty')) {
            const dateInput = findInputByLabel("Execution Date") || findInputByLabel("निष्पादन तिथि") || document.querySelector('input[id*="execution" i], input[name*="execution" i], input[id*="date" i]');
            const faceValueInput = findInputByLabel("Face Value") || findInputByLabel("अंकित मूल्य") || document.querySelector('input[id*="face" i], input[name*="face" i], input[id*="loan" i]');
            
            if (dateInput && faceValueInput) {
                let execDate = data.execution_date;
                if (!execDate) {
                    const today = new Date();
                    const dd = String(today.getDate()).padStart(2, '0');
                    const mm = String(today.getMonth() + 1).padStart(2, '0');
                    const yyyy = today.getFullYear();
                    execDate = `${dd}-${mm}-${yyyy}`;
                }
                
                setInputValue(dateInput, execDate);
                setInputValue(faceValueInput, data.face_value.toString());
                
                setTimeout(() => {
                    triggerButtonByText("Calculate & Save") || triggerButtonByText("गणना और सहेजें") || triggerButtonByText("Calculate");
                    sendResponse({ success: true, message: 'Autofilled execution date and face value!' });
                }, 300);
            } else {
                sendResponse({ success: false, error: 'Could not locate Execution Date or Face Value inputs.' });
            }
        } else {
            sendResponse({ success: false, error: 'Make sure you are on the Property Detail or Calculate Duty screen.' });
        }
    } catch (err) {
        sendResponse({ success: false, error: err.message });
    }
}

// =====================================================================
// 3. Autofill Executant (Steps 8-10 in notes)
// =====================================================================

function autofillExecutants(data, sendResponse) {
    if (!data.executants || data.executants.length === 0) {
        sendResponse({ success: false, error: 'No executants data available.' });
        return;
    }
    
    const exec = data.executants[0];
    const url = window.location.href;
    
    // PHASE A: If on Viewparty page → click Executant button → bypass verification modal
    if (url.includes('/Party/Viewparty')) {
        // Click Executant button
        const executantBtn = document.getElementById('exect') || 
                             document.querySelector('button[id*="exec" i]') || 
                             Array.from(document.querySelectorAll('button, a, div, span, img, .btn')).find(el => {
                                 const txt = el.textContent.trim().toUpperCase();
                                 return txt === 'EXECUTANT' || txt.includes('निष्पादक') || (el.src && el.src.includes('executnt'));
                             });
        if (executantBtn) {
            console.log("[RM-Maker] Found Executant button. Clicking...");
            executantBtn.click();
        } else {
            console.log("[RM-Maker] FAILED: Could not find Executant button.");
            sendResponse({ success: false, error: 'Could not find the Executant button.' });
            return;
        }
        
        // Bypass the verification modal (Public → Without OTP → Submit)
        bypassVerificationModal("Public", sendResponse, "Modal bypassed! Click Autofill Executant again once the form loads.");
        return;
    }
    
    // PHASE B: If on PartyAdd form page → fill the actual executant details
    if (url.includes('/Party/PartyAdd') || url.includes('/Party/partyadd')) {
        fillPartyFormFields(exec, true, true)
            .then(() => {
                sendResponse({ success: true, message: 'Autofilled Executant details! Review and click Save.' });
            })
            .catch(err => {
                sendResponse({ success: false, error: err.message });
            });
        return;
    }
    
    // Fallback: Unknown page
    sendResponse({ success: false, error: 'Not on Viewparty or PartyAdd page. Navigate to the Party Details tab first.' });
}

// =====================================================================
// 4. Autofill Claimant (Steps 11-12 in notes)
// =====================================================================

function autofillClaimant(data, sendResponse) {
    if (!data.claimant) {
        sendResponse({ success: false, error: 'No claimant data available.' });
        return;
    }
    
    const cl = data.claimant;
    const url = window.location.href;
    
    // PHASE A: Viewparty → click Claimant → bypass modal
    if (url.includes('/Party/Viewparty')) {
        const claimantBtn = document.getElementById('clmnt') || 
                             document.getElementById('claim') || 
                             document.getElementById('claimant') || 
                             document.querySelector('button[id*="claim" i]') || 
                             Array.from(document.querySelectorAll('button, a, div, span, img, .btn')).find(el => {
                                 const txt = el.textContent.trim().toUpperCase();
                                 return txt === 'CLAIMANT' || txt.includes('दावेदार') || txt.includes('क्लेमेंट') || (el.src && el.src.includes('claimant'));
                             });
        if (claimantBtn) {
            console.log("[RM-Maker] Found Claimant button. Clicking...");
            claimantBtn.click();
        } else {
            sendResponse({ success: false, error: 'Could not find the Claimant button.' });
            return;
        }
        
        // Modal bypass uses Public type (same as executants/witnesses) per notes
        bypassVerificationModal("Public", sendResponse, "Modal bypassed! Click Autofill Claimant again once the form loads.");
        return;
    }
    
    // PHASE B: PartyAdd form → fill claimant details
    if (url.includes('/Party/PartyAdd') || url.includes('/Party/partyadd')) {
        fillPartyFormFields(cl, false, false)
            .then(() => {
                sendResponse({ success: true, message: 'Autofilled Claimant (Bank) details! Review and click Save.' });
            })
            .catch(err => {
                sendResponse({ success: false, error: err.message });
            });
        return;
    }
    
    sendResponse({ success: false, error: 'Not on Viewparty or PartyAdd page.' });
}

// =====================================================================
// 5. Autofill Witnesses (Step 13 in notes)
// =====================================================================

function autofillWitnessN(data, index, sendResponse) {
    if (!data.witnesses || data.witnesses.length <= index) {
        sendResponse({ success: false, error: `No data available for Witness ${index + 1}.` });
        return;
    }
    
    const url = window.location.href;
    
    // PHASE A: Viewparty → click Witness → bypass modal
    if (url.includes('/Party/Viewparty')) {
        const witnessBtn = document.getElementById('wtns') || 
                           document.getElementById('witness') || 
                           document.getElementById('witnesses') || 
                           document.querySelector('button[id*="wit" i]') || 
                           Array.from(document.querySelectorAll('button, a, div, span, img, .btn')).find(el => {
                               const txt = el.textContent.trim().toUpperCase();
                               return txt === 'WITNESS' || txt.includes('गवाह') || txt.includes('साक्षी') || (el.src && el.src.includes('witness'));
                           });
        if (witnessBtn) {
            console.log("[RM-Maker] Found Witness button. Clicking...");
            witnessBtn.click();
        } else {
            console.log("[RM-Maker] FAILED: Could not find Witness button.");
            sendResponse({ success: false, error: 'Could not find the Witness button.' });
            return;
        }
        
        bypassVerificationModal("Public", sendResponse, `Modal bypassed! Click Autofill Witness ${index + 1} again once the form loads.`);
        return;
    }
    
    // PHASE B: PartyAdd form → fill witness details
    if (url.includes('/Party/PartyAdd') || url.includes('/Party/partyadd')) {
        const wit = data.witnesses[index];
        fillPartyFormFields(wit, false, false)
            .then(() => {
                sendResponse({ success: true, message: `Autofilled Witness ${index + 1} details! Click Save.` });
            })
            .catch(err => {
                sendResponse({ success: false, error: err.message });
            });
        return;
    }
    
    sendResponse({ success: false, error: 'Not on Viewparty or PartyAdd page.' });
}

// =====================================================================
// 6. Set Presenter (Step 14 in notes)
// =====================================================================

function setPresenter(data, sendResponse) {
    try {
        const clicked = clickRadioByValueOrLabel("दस्तावेज प्रस्तुतकर्ता पक्षकार स्वयं है");
        if (clicked) {
            setTimeout(() => {
                const saved = triggerButtonByText("Save");
                if (saved) {
                    sendResponse({ success: true, message: 'Selected Presenter as Self and saved!' });
                } else {
                    sendResponse({ success: true, message: 'Selected Presenter as Self. Please click Save manually.' });
                }
            }, 100);
        } else {
            sendResponse({ success: false, error: 'Could not find the presenter option.' });
        }
    } catch (err) {
        sendResponse({ success: false, error: err.message });
    }
}

// =====================================================================
// AUTO-RUN FLOW: Full automation from Dashboard to Calculate Duty
// =====================================================================

function updateFloatingStatus(statusText) {
    let badge = document.getElementById('rm-maker-autorun-badge');
    if (!badge) {
        badge = document.createElement('div');
        badge.id = 'rm-maker-autorun-badge';
        badge.style.position = 'fixed';
        badge.style.top = '10px';
        badge.style.right = '10px';
        badge.style.backgroundColor = '#1e293b';
        badge.style.color = '#f8fafc';
        badge.style.padding = '8px 12px';
        badge.style.borderRadius = '6px';
        badge.style.fontFamily = 'Segoe UI, -apple-system, sans-serif';
        badge.style.fontSize = '12px';
        badge.style.fontWeight = 'bold';
        badge.style.zIndex = '99999';
        badge.style.border = '1px solid #6366f1';
        badge.style.boxShadow = '0 4px 12px rgba(99, 102, 241, 0.35)';
        badge.style.pointerEvents = 'none';
        document.body.appendChild(badge);
    }
    badge.textContent = `⚡ Auto-Run: ${statusText.replace(/_/g, ' ').toUpperCase()}`;
}

function startAutoRunFlow(data, sendResponse) {
    const url = window.location.href;
    const lowerUrl = url.toLowerCase();
    
    // Auto-detect current page and trigger the appropriate entry point
    if (lowerUrl.includes('/citizen/dashboard')) {
        chrome.storage.local.set({ 
            autoRunState: 'awaiting_district_modal',
            activeCaseData: data
        }, () => {
            console.log('[RM-Maker AutoRun] Flow started from Dashboard. State and Case Data saved.');
            sendResponse({ success: true, message: 'Auto-run started! Clicking Add New Valuation...' });
            handleDashboardStep(data);
        });
    } else if (lowerUrl.includes('propertyvaluation') && !lowerUrl.includes('propertydetail') && !lowerUrl.includes('calculateduty')) {
        chrome.storage.local.set({ 
            autoRunState: 'awaiting_property_valuation',
            activeCaseData: data
        }, () => {
            console.log('[RM-Maker AutoRun] Flow started directly from Property Valuation page.');
            sendResponse({ success: true, message: 'Auto-run started! Filling document details...' });
            handleDocumentDetailsStep(data);
        });
    } else if (lowerUrl.includes('propertydetail') || lowerUrl.includes('calculateduty')) {
        chrome.storage.local.set({ 
            autoRunState: 'awaiting_calculate_duty',
            activeCaseData: data
        }, () => {
            console.log('[RM-Maker AutoRun] Flow started directly from Calculate Duty / Property Detail page.');
            sendResponse({ success: true, message: 'Auto-run started! Calculating duty...' });
            handleCalculateDutyStep(data);
        });
    } else if (lowerUrl.includes('party/viewparty') || lowerUrl.includes('party/partyadd')) {
        chrome.storage.local.set({ 
            autoRunState: 'awaiting_executant_autofill',
            activeCaseData: data
        }, () => {
            console.log('[RM-Maker AutoRun] Flow started directly from Party Details page.');
            sendResponse({ success: true, message: 'Auto-run started! Autofilling party details...' });
            handlePartyAutofillSequence('awaiting_executant_autofill', data);
        });
    } else {
        sendResponse({ success: false, error: 'Please navigate to Dashboard, Valuation, Calculate Duty, or Party Details page first.' });
    }
}

// --- STEP 1: Dashboard → Click "+ Add New Valuation" → Select District ---
function handleDashboardStep(caseData) {
    console.log('[RM-Maker AutoRun] Step 1: Dashboard — clicking Add New Valuation');
    
    const addBtn = document.getElementById('addnewproperty') || 
                   document.querySelector('button.addButton') ||
                   Array.from(document.querySelectorAll('button')).find(b => 
                       b.textContent.trim().includes('Add New Valuation') || b.textContent.trim().includes('नया मूल्यांकन'));
    
    if (!addBtn) {
        console.error('[RM-Maker AutoRun] Could not find Add New Valuation button.');
        chrome.storage.local.remove('autoRunState');
        return;
    }
    
    addBtn.click();
    console.log('[RM-Maker AutoRun] Clicked Add New Valuation. Waiting for district modal...');
    
    // Wait for the district modal to appear (Select2 dropdown)
    waitForElement('#ddlDistrict, select[data-select2-id="ddlDistrict"], .select2-selection', 8000)
        .then(() => {
            console.log('[RM-Maker AutoRun] District modal appeared. Waiting for it to settle...');
            return delay(800);
        })
        .then(() => {
            return selectDistrictJaipur();
        })
        .then((success) => {
            if (!success) {
                console.error('[RM-Maker AutoRun] Failed to select JAIPUR district.');
                chrome.storage.local.remove('autoRunState');
            }
        })
        .catch(err => {
            console.error('[RM-Maker AutoRun] District step error:', err);
            chrome.storage.local.remove('autoRunState');
        });
}

// --- STEP 2: PropertyValuation → Fill Document Details → Save ---
async function handleDocumentDetailsStep(caseData) {
    console.log('[RM-Maker AutoRun] Step 2: PropertyValuation — filling document details');
    
    // Wait a bit more for form elements to load
    await delay(1000);
    
    // Determine gender card type
    const executants = caseData.executants || [];
    let genderCard = 'MALE_GEN';
    if (executants.length > 0) {
        const genders = executants.map(e => e.gender);
        const hasMale = genders.includes('MALE');
        const hasFemale = genders.includes('FEMALE');
        if (hasMale && hasFemale) genderCard = 'JOINT';
        else if (hasFemale) genderCard = 'FEMALE_GEN';
    }
    
    // Reuse the existing autofillDetails logic
    const detailsData = {
        sro: caseData.sro || 'JAIPUR-VII',
        tehsil: caseData.tehsil || 'JAIPUR',
        gender_card: genderCard
    };
    
    // Call autofillDetails and wait for it to complete
    autofillDetails(detailsData, (response) => {
        if (response.success) {
            console.log('[RM-Maker AutoRun] Document details filled. Waiting before clicking Save...');
            updateFloatingStatus('DETAILS FILLED. SAVING IN 3S...');
            // Wait 3s for all ng-select options to settle, then click Save
            setTimeout(() => {
                clickSaveButton();
            }, 3000);
        } else {
            console.error('[RM-Maker AutoRun] Failed to fill document details:', response.error);
            updateFloatingStatus(`ERROR: ${response.error}`);
            // Keep the state on the badge for debugging instead of immediately removing it
        }
    });
}

// --- STEP 3: CalculateDuty → Fill values → Calculate twice ---
async function handleCalculateDutyStep(caseData) {
    const url = window.location.href;
    const lowerUrl = url.toLowerCase();
    
    console.log('[RM-Maker AutoRun] Step 3: CalculateDuty — current URL:', url);
    
    if (lowerUrl.includes('propertydetail')) {
        // We are on the intermediate page. Click the "Calculate Duty" button to navigate.
        console.log('[RM-Maker AutoRun] Intermediate PropertyDetail page. Clicking Calculate Duty button to navigate...');
        updateFloatingStatus('PROPERTY DETAIL PAGE. NAVIGATING TO DUTY...');
        await delay(1200);
        
        const calcBtn = triggerButtonByText("Calculate Duty") || triggerButtonByText("ड्यूटी की गणना करें");
        if (calcBtn) {
            console.log('[RM-Maker AutoRun] Calculate Duty button clicked.');
        } else {
            console.error('[RM-Maker AutoRun] Calculate Duty button not found on PropertyDetail page.');
            updateFloatingStatus('ERROR: Calculate Duty button not found.');
        }
        return;
    }
    
    if (lowerUrl.includes('calculateduty')) {
        // We are on the actual calculate duty page. Fill values and click calculate twice.
        // Set state to 'duty_completed' immediately to prevent any re-triggering during calculations
        chrome.storage.local.set({ autoRunState: 'duty_completed' });
        
        console.log('[RM-Maker AutoRun] CalculateDuty page. Filling values...');
        updateFloatingStatus('CALCULATING STAMP DUTY (PASS 1)...');
        await delay(1200);
        
        const dutyData = {
            execution_date: caseData.execution_date,
            face_value: caseData.face_value
        };
        
        // First pass: fill values and click Calculate & Save
        autofillCalculateDuty(dutyData, (response1) => {
            if (!response1.success) {
                console.error('[RM-Maker AutoRun] First Calculate Duty pass failed:', response1.error);
                updateFloatingStatus(`ERROR: ${response1.error}`);
                // Restore state so user can retry
                chrome.storage.local.set({ autoRunState: 'awaiting_calculate_duty' });
                return;
            }
            
            console.log('[RM-Maker AutoRun] First Calculate Duty pass success:', response1.message);
            updateFloatingStatus('CALCULATED FIRST PASS. WAITING 2.5S...');
            
            // Wait 2.5s, then do the second pass click
            setTimeout(() => {
                console.log('[RM-Maker AutoRun] Second Calculate Duty pass: clicking Calculate & Save again...');
                updateFloatingStatus('CALCULATING STAMP DUTY (PASS 2)...');
                
                const calcSaveBtn = triggerButtonByText("Calculate & Save") || 
                                    triggerButtonByText("गणना और सहेजें") || 
                                    triggerButtonByText("Calculate and Save");
                if (calcSaveBtn) {
                    // Save state BEFORE click to prevent race condition during page redirect/unload
                    chrome.storage.local.set({ autoRunState: 'awaiting_party_detail_navigation' }, () => {
                        console.log('[RM-Maker AutoRun] Transition state saved: awaiting_party_detail_navigation. Clicking second pass...');
                        calcSaveBtn.click();
                        console.log('[RM-Maker AutoRun] Second click completed.');
                    });
                } else {
                    console.error('[RM-Maker AutoRun] Calculate & Save button not found for second pass.');
                    chrome.storage.local.set({ autoRunState: 'awaiting_calculate_duty' });
                }
            }, 2500);
        });
    }
}

async function handlePartyDetailNavigationStep() {
    console.log('[RM-Maker AutoRun] Step 4: Navigating to Party Details...');
    updateFloatingStatus('NAVIGATING TO PARTY DETAILS...');
    await delay(1200);
    
    // Find Party Detail button via class, title, formaction, or text
    const partyBtn = document.querySelector('button[formaction*="Viewparty" i]') ||
                     document.querySelector('button[title*="Party Detail" i]') ||
                     Array.from(document.querySelectorAll('button')).find(b => {
                         const txt = b.textContent.trim().toUpperCase();
                         return txt.includes('PARTY DETAIL') || txt.includes('पक्षकार') || txt.includes('VIEWPARTY');
                     });
                     
    if (partyBtn) {
        // Set state to awaiting_executant_autofill BEFORE click/submit to ensure redirect state is saved
        chrome.storage.local.set({ autoRunState: 'awaiting_executant_autofill' }, () => {
            console.log('[RM-Maker AutoRun] Transition state saved: awaiting_executant_autofill. Clicking Party Detail...');
            
            // Dispatch mousedown and mouseup for safety, then click
            partyBtn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
            partyBtn.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
            partyBtn.click();
            
            // Fallback: Programmatic form submission to button's formaction if navigation didn't happen (common for synthetic clicks in SPA forms)
            setTimeout(() => {
                const form = partyBtn.closest('form');
                if (form) {
                    console.log('[RM-Maker AutoRun] Fallback: submitting form programmatically to button formaction...');
                    
                    // Trigger page-context loader animation if it exists
                    try {
                        const script = document.createElement('script');
                        script.textContent = `
                            if (window.loader && typeof window.loader.show === 'function') {
                                window.loader.show();
                            }
                        `;
                        (document.head || document.documentElement).appendChild(script);
                        script.remove();
                    } catch(e) {}
                    
                    form.action = partyBtn.getAttribute('formaction') || '/Party/Viewparty';
                    form.method = 'POST';
                    form.submit();
                }
            }, 400);
            
            console.log('[RM-Maker AutoRun] Party Details navigation initiated!');
        });
    } else {
        console.error('[RM-Maker AutoRun] Party Detail button not found on the page.');
        updateFloatingStatus('ERROR: Party Detail button not found.');
    }
}

async function handlePartyAutofillSequence(state, caseData) {
    const url = window.location.href;
    const lowerUrl = url.toLowerCase();
    
    console.log(`[RM-Maker AutoRun] handlePartyAutofillSequence state: ${state}, URL: ${url}`);
    
    // Map state to party details and next step transition state
    let partyTypeName = '';
    let partyData = null;
    let nextState = '';
    
    if (state === 'awaiting_executant_autofill') {
        partyTypeName = 'EXECUTANT';
        partyData = { executants: caseData.executants };
        nextState = 'awaiting_claimant_autofill';
    } else if (state === 'awaiting_claimant_autofill') {
        partyTypeName = 'CLAIMANT';
        partyData = { claimant: caseData.claimant };
        nextState = 'awaiting_witness1_autofill';
    } else if (state === 'awaiting_witness1_autofill') {
        partyTypeName = 'WITNESS1';
        partyData = { witnesses: caseData.witnesses };
        nextState = 'awaiting_witness2_autofill';
    } else if (state === 'awaiting_witness2_autofill') {
        partyTypeName = 'WITNESS2';
        partyData = { witnesses: caseData.witnesses };
        nextState = 'flow_completed'; 
    }
    
    if (lowerUrl.includes('party/viewparty')) {
        console.log(`[RM-Maker AutoRun] On Viewparty page. Clicking ${partyTypeName} button...`);
        updateFloatingStatus(`OPENING ${partyTypeName} DIALOG...`);
        await delay(1200);
        
        let buttonAction = null;
        if (state === 'awaiting_executant_autofill') {
            buttonAction = 'autofill_executants';
        } else if (state === 'awaiting_claimant_autofill') {
            buttonAction = 'autofill_claimant';
        } else if (state === 'awaiting_witness1_autofill') {
            buttonAction = 'autofill_witness1';
        } else if (state === 'awaiting_witness2_autofill') {
            buttonAction = 'autofill_witness2';
        }
        
        // Call the specific helper based on action
        if (buttonAction === 'autofill_executants') {
            autofillExecutants(partyData, (response) => handleViewPartyCallback(response, partyTypeName));
        } else if (buttonAction === 'autofill_claimant') {
            autofillClaimant(partyData, (response) => handleViewPartyCallback(response, partyTypeName));
        } else if (buttonAction === 'autofill_witness1') {
            autofillWitnessN(partyData, 0, (response) => handleViewPartyCallback(response, partyTypeName));
        } else if (buttonAction === 'autofill_witness2') {
            autofillWitnessN(partyData, 1, (response) => handleViewPartyCallback(response, partyTypeName));
        }
        return;
    }
    
    if (lowerUrl.includes('party/partyadd')) {
        console.log(`[RM-Maker AutoRun] On PartyAdd page. Autofilling ${partyTypeName} details...`);
        updateFloatingStatus(`FILLING ${partyTypeName} DETAILS...`);
        await delay(1200);
        
        const onAutofillComplete = (response) => {
            if (response.success) {
                console.log(`[RM-Maker AutoRun] ${partyTypeName} details filled. Waiting 1.2s before clicking Save...`);
                updateFloatingStatus(`${partyTypeName} DETAILS FILLED. SAVING...`);
                
                setTimeout(() => {
                    // Save next state to storage BEFORE clicking Save button to prevent race conditions during redirect
                    chrome.storage.local.set({ autoRunState: nextState }, () => {
                        console.log(`[RM-Maker AutoRun] Next state saved: ${nextState}. Clicking Save button...`);
                        
                        // Click the Save button
                        const saveBtn = document.getElementById('saveDetail') || 
                                        document.querySelector('button.btn-success') || 
                                        triggerButtonByText("Save") || 
                                        triggerButtonByText("सहेजें");
                                        
                        if (saveBtn) {
                            saveBtn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                            saveBtn.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                            saveBtn.click();
                            console.log(`[RM-Maker AutoRun] ${partyTypeName} Save button clicked. Watching for SweetAlert2 confirm...`);
                            
                            // Poll for SweetAlert2 OK button to dismiss alert and trigger redirect
                            let checkCount = 0;
                            const swalInterval = setInterval(() => {
                                checkCount++;
                                const okBtn = document.querySelector('button.swal2-confirm') || 
                                              Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'OK' || b.textContent.trim() === 'ठीक है');
                                if (okBtn) {
                                    console.log('[RM-Maker AutoRun] SweetAlert2 OK button found. Clicking to trigger redirect...');
                                    okBtn.click();
                                    clearInterval(swalInterval);
                                    
                                    // If this was the last step in the party sequence, clear the autoRunState completely after redirect
                                    if (nextState === 'flow_completed') {
                                        setTimeout(() => {
                                            chrome.storage.local.remove('autoRunState');
                                            console.log('[RM-Maker AutoRun] ✅ Party details filling workflow finished!');
                                            updateFloatingStatus('PARTY DETAILS FILL COMPLETE!');
                                            setTimeout(() => {
                                                const badge = document.getElementById('rm-maker-autorun-badge');
                                                if (badge) badge.remove();
                                            }, 4000);
                                        }, 1500);
                                    }
                                }
                                if (checkCount > 40) { // Timeout after 8 seconds (40 * 200ms)
                                    console.warn('[RM-Maker AutoRun] SweetAlert2 OK button did not appear within timeout.');
                                    clearInterval(swalInterval);
                                }
                            }, 200);
                        } else {
                            console.error('[RM-Maker AutoRun] Save button not found!');
                            updateFloatingStatus('ERROR: Save button not found!');
                        }
                    });
                }, 1200);
            } else {
                console.error(`[RM-Maker AutoRun] ${partyTypeName} details fill failed:`, response.error);
                updateFloatingStatus(`ERROR: ${response.error}`);
            }
        };
        
        // Execute the correct form autofill helper
        if (state === 'awaiting_executant_autofill') {
            autofillExecutants(partyData, onAutofillComplete);
        } else if (state === 'awaiting_claimant_autofill') {
            autofillClaimant(partyData, onAutofillComplete);
        } else if (state === 'awaiting_witness1_autofill') {
            autofillWitnessN(partyData, 0, onAutofillComplete);
        } else if (state === 'awaiting_witness2_autofill') {
            autofillWitnessN(partyData, 1, onAutofillComplete);
        }
    }
}

function handleViewPartyCallback(response, partyTypeName) {
    if (response.success) {
        console.log(`[RM-Maker AutoRun] ${partyTypeName} modal bypass complete.`);
        updateFloatingStatus(`${partyTypeName} BYPASSED. LOADING FORM...`);
    } else {
        console.error(`[RM-Maker AutoRun] ${partyTypeName} modal bypass failed:`, response.error);
        updateFloatingStatus(`ERROR: ${response.error}`);
    }
}

// =====================================================================
// AUTO-RUN HELPERS
// =====================================================================

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function waitForElement(selector, timeout = 5000) {
    return new Promise((resolve, reject) => {
        const existing = document.querySelector(selector);
        if (existing) {
            resolve(existing);
            return;
        }
        
        const observer = new MutationObserver((mutations, obs) => {
            const el = document.querySelector(selector);
            if (el) {
                obs.disconnect();
                resolve(el);
            }
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
        
        setTimeout(() => {
            observer.disconnect();
            // One last check
            const el = document.querySelector(selector);
            if (el) resolve(el);
            else reject(new Error(`Timeout waiting for element: ${selector}`));
        }, timeout);
    });
}

async function selectDistrictJaipur() {
    // The district modal uses Select2. We need to:
    // 1. Find and open the Select2 dropdown
    // 2. Search for JAIPUR
    // 3. Click it
    
    // Try clicking the Select2 container to open the dropdown
    const select2Container = document.querySelector('#select2-ddlDistrict-container') ||
                              document.querySelector('.select2-selection') ||
                              document.querySelector('[aria-labelledby="select2-ddlDistrict-container"]');
    
    if (select2Container) {
        console.log('[RM-Maker AutoRun] Found Select2 container, clicking to open...');
        select2Container.click();
        // Also try dispatching mousedown which Select2 listens to
        select2Container.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        
        await delay(600);
        
        // Type "JAIPUR" into the Select2 search box
        const searchInput = document.querySelector('.select2-search__field') ||
                           document.querySelector('input.select2-search__field');
        if (searchInput) {
            searchInput.value = 'JAIPUR';
            searchInput.dispatchEvent(new Event('input', { bubbles: true }));
            searchInput.dispatchEvent(new Event('keyup', { bubbles: true }));
            await delay(800);
        }
        
        // Find and click the JAIPUR option in the dropdown results
        const options = Array.from(document.querySelectorAll('.select2-results__option'));
        const jaipurOpt = options.find(opt => {
            const txt = opt.textContent.toUpperCase();
            return txt.includes('JAIPUR') || txt.includes('जयपुर');
        });
        
        if (jaipurOpt) {
            console.log('[RM-Maker AutoRun] Found JAIPUR option, clicking via mouse events...');
            
            // Dispatch mousedown, mouseup, and click to ensure Select2 registers the selection
            jaipurOpt.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
            jaipurOpt.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
            jaipurOpt.click();
            
            // Also sync the underlying select element directly as a fail-safe
            const rawSelect = document.getElementById('ddlDistrict');
            if (rawSelect) {
                const fallbackOptions = Array.from(rawSelect.options);
                const matchOpt = fallbackOptions.find(o => o.text.toUpperCase().includes('JAIPUR') || o.text.includes('जयपुर'));
                if (matchOpt) {
                    rawSelect.value = matchOpt.value;
                    rawSelect.dispatchEvent(new Event('change', { bubbles: true }));
                    triggerJQuerySelect('ddlDistrict', matchOpt.value);
                }
            }
            
            await delay(500);
            
            // Set the state in storage BEFORE triggering navigation to prevent race conditions on unload
            return new Promise((resolve) => {
                chrome.storage.local.set({ autoRunState: 'awaiting_property_valuation' }, () => {
                    console.log('[RM-Maker AutoRun] Property valuation state saved to storage. Clicking navigation arrow...');
                    
                    // Now look for the navigation arrow or submit button
                    const arrowBtn = document.querySelector('.login-arrow') ||
                                    document.querySelector('a[class*="arrow"]') ||
                                    document.querySelector('span[class*="arrow"]');
                    if (arrowBtn) {
                        arrowBtn.click();
                        resolve(true);
                    } else {
                        // Fallback: look for any submit-like button in the modal
                        const modalBtns = Array.from(document.querySelectorAll('.modal button, .modal a, .modal input[type="button"]'));
                        const goBtn = modalBtns.find(b => b.offsetWidth > 0 && b.offsetHeight > 0);
                        if (goBtn) {
                            goBtn.click();
                            resolve(true);
                        } else {
                            resolve(false);
                        }
                    }
                });
            });
        }
    }
    
    // Fallback: try using the underlying <select> element directly via jQuery
    const rawSelect = document.getElementById('ddlDistrict');
    if (rawSelect) {
        console.log('[RM-Maker AutoRun] Trying jQuery fallback for district select...');
        const fallbackOptions = Array.from(rawSelect.options);
        const jaipurOpt = fallbackOptions.find(o => o.text.toUpperCase().includes('JAIPUR') || o.text.includes('जयपुर'));
        if (jaipurOpt) {
            rawSelect.value = jaipurOpt.value;
            rawSelect.dispatchEvent(new Event('change', { bubbles: true }));
            
            // Also trigger via page-context jQuery for Select2 binding
            triggerJQuerySelect('ddlDistrict', jaipurOpt.value);
            
            await delay(500);
            
            return new Promise((resolve) => {
                chrome.storage.local.set({ autoRunState: 'awaiting_property_valuation' }, () => {
                    console.log('[RM-Maker AutoRun] Property valuation state saved via fallback. Clicking arrow...');
                    const arrowBtn = document.querySelector('.login-arrow') ||
                                    document.querySelector('a[class*="arrow"]');
                    if (arrowBtn) {
                        arrowBtn.click();
                        resolve(true);
                    } else {
                        resolve(false);
                    }
                });
            });
        }
    }
    
    return false;
}
 
function clickSaveButton() {
    console.log('[RM-Maker AutoRun] Clicking Save button...');
    
    const saveBtn = document.getElementById('savedocument') ||
                    document.querySelector('button.submit-btn') ||
                    Array.from(document.querySelectorAll('button')).find(b => {
                        const txt = b.textContent.trim();
                        return txt === 'Save' || txt === 'सहेजें';
                    });
    
    if (saveBtn) {
        console.log('[RM-Maker AutoRun] Save button found. Clicking Save...');
        saveBtn.click();
        
        // Wait for SweetAlert2 confirmation modal button (.swal2-confirm)
        console.log('[RM-Maker AutoRun] Waiting for SweetAlert confirmation dialog...');
        waitForElement('.swal2-confirm, button.swal2-confirm, .swal2-actions button', 10000)
            .then((okBtn) => {
                console.log('[RM-Maker AutoRun] SweetAlert OK button appeared. Clicking...');
                // Set state for the CalculateDuty page that will load after OK is clicked
                chrome.storage.local.set({ autoRunState: 'awaiting_calculate_duty' }, () => {
                    okBtn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                    okBtn.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                    okBtn.click();
                });
            })
            .catch(err => {
                console.error('[RM-Maker AutoRun] SweetAlert OK button did not appear:', err);
                // Fallback: still set the state in case it auto-navigated or did something else
                chrome.storage.local.set({ autoRunState: 'awaiting_calculate_duty' });
            });
    } else {
        console.error('[RM-Maker AutoRun] Save button not found.');
        chrome.storage.local.remove('autoRunState');
    }
}
