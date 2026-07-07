// Content script to run on e-Panjiyan portal pages
console.log("[RM-Maker Autofill] Content script loaded on:", window.location.href);

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log("[RM-Maker Autofill] Message received:", request.action);
    
    try {
        switch (request.action) {
            case 'one_click_autofill':
                oneClickAutofill(request.data, sendResponse);
                break;
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
// HELPER FUNCTIONS
// =====================================================================

let toastElement = null;

function showStatusToast(message, isSpinner = true) {
    try {
        if (!toastElement) {
            toastElement = document.createElement('div');
            toastElement.id = 'rm-maker-toast';
            toastElement.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 999999;
                background: rgba(15, 23, 42, 0.95);
                color: #ffffff;
                padding: 12px 20px;
                border-radius: 8px;
                font-family: 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
                font-weight: 600;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.05), 0 0 10px rgba(99, 102, 241, 0.2);
                border: 1px solid rgba(99, 102, 241, 0.4);
                display: flex;
                align-items: center;
                gap: 12px;
                transition: all 0.3s ease;
                transform: translateY(-20px);
                opacity: 0;
            `;
            document.body.appendChild(toastElement);
            
            // Force reflow
            toastElement.offsetHeight;
            toastElement.style.transform = 'translateY(0)';
            toastElement.style.opacity = '1';
        }
        
        const icon = isSpinner ? 
            `<svg style="animation: spin 1s linear infinite; width: 18px; height: 18px;" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="rgba(255, 255, 255, 0.2)" stroke-width="3"/>
                <path d="M12 2C6.47715 2 2 6.47715 2 12C2 13.5997 2.37562 15.1116 3.04348 16.4522" stroke="#6366f1" stroke-width="3" stroke-linecap="round"/>
             </svg>` : 
            `<span style="color: #10b981; font-size: 18px; font-weight: bold;">⚡</span>`;
            
        toastElement.innerHTML = `
            ${icon}
            <span style="letter-spacing: 0.2px;">${message}</span>
        `;
        
        // Add keyframe animation for spinner if not present
        if (!document.getElementById('rm-maker-toast-style')) {
            const style = document.createElement('style');
            style.id = 'rm-maker-toast-style';
            style.textContent = `
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }
    } catch (e) {
        console.error("[RM-Maker] Error showing status toast:", e);
    }
}

function hideStatusToast() {
    try {
        if (toastElement) {
            toastElement.style.transform = 'translateY(-20px)';
            toastElement.style.opacity = '0';
            setTimeout(() => {
                if (toastElement && toastElement.parentNode) {
                    toastElement.parentNode.removeChild(toastElement);
                    toastElement = null;
                }
            }, 300);
        }
    } catch (e) {
        console.error("[RM-Maker] Error hiding status toast:", e);
    }
}


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
        pan: ['#txtPanCardNo', '#txtpancardno', '#txtpan', '#pan', 'input[name*="pan" i]', 'input[id*="pan" i]'],
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
    let cleaned = name.replace(/^(MR|MRS|MS|SHRI|SMT|SH|DR|LATE)\b\.?\s*/i, '').trim();
    // Strip special characters like dots, commas, dashes, keeping only alphanumeric and spaces
    cleaned = cleaned.replace(/[^A-Za-z0-9\s]/g, ' ');
    // Collapse multiple spaces into one space
    cleaned = cleaned.replace(/\s+/g, ' ').trim();
    return cleaned;
}

function checkRequiredFields() {
    const nameInput = document.getElementById('txtpartynameen') || document.querySelector('input[name="partynameen"]') || document.querySelector('input[id*="partyname" i]');
    if (nameInput && !nameInput.value.trim()) {
        return "Party Name (English)";
    }
    
    const fatherInput = document.getElementById('txtfathernameen') || document.querySelector('input[name="fathernameen"]') || document.querySelector('input[id*="fathername" i]') || document.querySelector('input[id*="relationname" i]');
    if (fatherInput && !fatherInput.value.trim()) {
        return "Father/Husband Name (English)";
    }
    
    const ageInput = document.getElementById('txtage') || document.querySelector('input[name="age"]') || document.querySelector('input[id*="age" i]');
    if (ageInput && !ageInput.value.trim()) {
        return "Age";
    }
    
    const pinInput = document.getElementById('txtpincode') || document.querySelector('input[name="pincode"]') || document.querySelector('input[id*="pincode" i]') || document.querySelector('input[id*="pin" i]');
    if (pinInput && !pinInput.value.trim()) {
        return "Pincode";
    }
    
    return null;
}

async function fillPartyFormFields(partyData, isPresenter, isPurchaser, isWitness = false) {
    console.log("[RM-Maker] Starting fillPartyFormFields for:", partyData.name_en, "isWitness:", isWitness);
    
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
    await new Promise(r => setTimeout(r, 200));
    
    // 2. Gender Selection
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
    await new Promise(r => setTimeout(r, 200));
    
    // 3. Dropdowns - Filled sequentially to avoid ng-select race conditions
    const catSelect = getField('category');
    if (catSelect) await setSelectValueByText(catSelect, "General");
    
    const occSelect = getField('occupation');
    if (occSelect) await setSelectValueByText(occSelect, "Other");
    
    const idSelect = getField('idProof');
    if (idSelect) await setSelectValueByText(idSelect, "Other than above");
    
    await new Promise(r => setTimeout(r, 250));
    
    // 4. Fill basic details
    const partyNameEn = getField('partyNameEn');
    if (partyNameEn) setInputValue(partyNameEn, cleanSalutation(partyData.name_en));
    
    const relNameEn = getField('relNameEn');
    if (relNameEn) setInputValue(relNameEn, cleanSalutation(partyData.relation_name_en));
    
    const dobInput = document.getElementById('txtdob') || getField('dob');
    const ageInput = getField('age');
    if (dobInput) {
        let dobValue = "";
        if (partyData.dob) {
            dobValue = partyData.dob.replace(/[-\.]/g, '/');
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
        setDatePickerValue(dobInput, dobValue);
    } else if (ageInput) {
        setInputValue(ageInput, partyData.age || "40");
    }
    
    const casteEn = getField('casteEn');
    if (casteEn) setInputValue(casteEn, "HINDU");
    
    const casteHi = document.getElementById('txtcastehindi') || document.querySelector('input[name*="casteHindi" i]') || document.querySelector('input[id*="castehindi" i]');
    if (casteHi) setInputValue(casteHi, "हिन्दू");
    
    const idDetails = getField('idDetails');
    const sampleAadhaar = "123456789012";
    if (idDetails) setInputValue(idDetails, partyData.id || partyData.aadhaar || sampleAadhaar);
    
    if (partyData.pan) {
        const panInput = getField('pan');
        if (panInput) setInputValue(panInput, partyData.pan);
    }
    
    // Address Details
    if (partyData.address) {
        const houseInput = getField('houseNo');
        const colonyInput = getField('colony');
        const areaInput = getField('area');
        const cityInput = getField('city');
        const pinInput = getField('pincode');
        
        if (houseInput) setInputValue(houseInput, partyData.address.house_no || "00");
        if (colonyInput) setInputValue(colonyInput, partyData.address.colony || "");
        if (areaInput) setInputValue(areaInput, partyData.address.area || "");
        if (cityInput) setInputValue(cityInput, partyData.address.city || "JAIPUR");
        if (pinInput) setInputValue(pinInput, partyData.address.pincode || "");
    }
    
    await new Promise(r => setTimeout(r, 400));
    
    // 5. Contact Details (Mobile Number OTP verification)
    if (isWitness) {
        console.log("[RM-Maker] Skipping mobile verification for witness.");
        console.log("[RM-Maker] Completed fillPartyFormFields for:", partyData.name_en);
        return;
    }
    
    // Check if OTP needs to be bypassed based on Property/Loan Valuation (< 25 lakhs)
    let valuationAmount = 0;
    try {
        const valSelectors = [
            'input[id*="valuation" i]', 'input[name*="valuation" i]',
            'input[id*="marketval" i]', 'input[name*="marketval" i]',
            'input[id*="consideration" i]', 'input[name*="consideration" i]',
            'input[id*="dlc" i]', 'input[name*="dlc" i]',
            'span[id*="valuation" i]', 'span[id*="marketval" i]', 'span[id*="consideration" i]',
            'td[id*="valuation" i]', 'td[id*="marketval" i]'
        ];
        for (const sel of valSelectors) {
            const el = document.querySelector(sel);
            if (el) {
                const valStr = el.value || el.textContent || "";
                const parsed = parseFloat(valStr.replace(/[^0-9.]/g, ''));
                if (parsed > valuationAmount) valuationAmount = parsed;
            }
        }
        
        const bodyText = document.body.innerText;
        const regex = /(?:valuation|market\s*value|dlc|consideration|loan|amount|मूल्यांकन|ऋण|बाजार\s*मूल्य|प्रतिफल)\s*[:\-]?\s*(?:rs\.?|inr)?\s*([0-9,.]+)/i;
        const matches = bodyText.match(new RegExp(regex.source, 'gi'));
        if (matches) {
            for (const m of matches) {
                const cleanNum = m.match(/[0-9,.]+/);
                if (cleanNum) {
                    const parsed = parseFloat(cleanNum[0].replace(/,/g, ''));
                    if (parsed > valuationAmount) valuationAmount = parsed;
                }
            }
        }
    } catch (err) {
        console.error("[RM-Maker] Error reading valuation from page:", err);
    }
    
    console.log("[RM-Maker] Resolved property/loan valuation:", valuationAmount);
    
    // Only trigger mobile OTP sequence if valuation/loan >= 30 lakhs (3,000,000)
    // If valuation is 0, we default to doing it (safer default)
    if (valuationAmount > 0 && valuationAmount < 3000000) {
        console.log(`[RM-Maker] Loan valuation (${valuationAmount}) is less than 30 Lakhs. Skipping OTP mobile sequence.`);
        console.log("[RM-Maker] Completed fillPartyFormFields for:", partyData.name_en);
        return;
    }
    
    let mobileVal = "";
    if (chrome && chrome.storage && chrome.storage.local) {
        const res = await new Promise(r => chrome.storage.local.get(['oneClickData', 'defaultMobile'], r));
        mobileVal = (res.oneClickData && res.oneClickData.mobile) || res.defaultMobile || "";
    }
    if (!mobileVal) {
        mobileVal = "8233658093";
    }
    
    const chkMobile = document.getElementById('chkMobile') || document.querySelector('input[name="chkEnterMobile"]');
    if (chkMobile) {
        if (!chkMobile.checked) {
            console.log("[RM-Maker] Checking Enter Mobile checkbox...");
            chkMobile.click();
        }
        
        await new Promise(r => setTimeout(r, 450));
        
        const contactInput = document.getElementById('txtcontact') || document.querySelector('input[name="contactno"]');
        if (contactInput) {
            console.log("[RM-Maker] Found contact input. Filling with:", mobileVal);
            setInputValue(contactInput, mobileVal);
            
            await new Promise(r => setTimeout(r, 450));
            
            const verifyBtn = document.getElementById('btnotpforvaluation') || 
                              Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim().toUpperCase() === 'VERIFY');
            if (verifyBtn) {
                console.log("[RM-Maker] Clicking Verify button to trigger OTP...");
                verifyBtn.click();
                
                // 1. Wait for and click OK on the "OTP Sent Successfully" SweetAlert modal
                showStatusToast("Waiting for OTP sent confirmation...");
                let clickedSentOk = false;
                for (let i = 0; i < 40; i++) {
                    const okBtn = document.querySelector('.swal2-confirm, .swal-button--confirm') || 
                                  Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim().includes('Ok') || b.textContent.trim().includes('ठीक है'));
                    if (okBtn && (okBtn.offsetWidth > 0 || okBtn.offsetHeight > 0)) {
                        await new Promise(r => setTimeout(r, 450));
                        okBtn.click();
                        okBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                        clickedSentOk = true;
                        break;
                    }
                    await new Promise(r => setTimeout(r, 150));
                }
                
                if (clickedSentOk) {
                    // 2. Poll for OTP from MacroDroid endpoint
                    showStatusToast("Polling for forwarded OTP from MacroDroid...");
                    let otpVal = "";
                    for (let i = 0; i < 60; i++) { // Poll for up to 90 seconds
                        try {
                            const response = await fetch('http://localhost:5000/api/case/otp/recent');
                            const resData = await response.json();
                            if (resData && resData.otp) {
                                otpVal = resData.otp;
                                break;
                            }
                        } catch (err) {
                            console.error("Error polling OTP:", err);
                        }
                        await new Promise(r => setTimeout(r, 1500));
                    }
                    
                    if (otpVal) {
                        showStatusToast(`OTP Received: ${otpVal}. Filling...`);
                        const otpInput = document.getElementById('txtotp') || document.querySelector('input[name="txtvaltionotp"]');
                        if (otpInput) {
                            setInputValue(otpInput, otpVal);
                            await new Promise(r => setTimeout(r, 450));
                            
                            // 3. Click Verify Mobile button
                            const verifyMobileBtn = document.getElementById('btnVerifyMobile');
                            if (verifyMobileBtn) {
                                console.log("[RM-Maker] Clicking Verify Mobile button...");
                                verifyMobileBtn.click();
                                
                                // 4. Wait for and click OK on the "OTP verified successfully" SweetAlert modal
                                showStatusToast("Waiting for OTP verified confirmation...");
                                for (let i = 0; i < 40; i++) {
                                    const okBtn = document.querySelector('.swal2-confirm, .swal-button--confirm') || 
                                                  Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim().includes('Ok') || b.textContent.trim().includes('ठीक है'));
                                    if (okBtn && (okBtn.offsetWidth > 0 || okBtn.offsetHeight > 0)) {
                                        await new Promise(r => setTimeout(r, 450));
                                        okBtn.click();
                                        okBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                                        break;
                                    }
                                    await new Promise(r => setTimeout(r, 150));
                                }
                            }
                        }
                    } else {
                        showStatusToast("OTP polling timed out. Please enter OTP manually.", false);
                    }
                }
            }
        }
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
    
    for (let i = 0; i < 15; i++) {
        await new Promise(r => setTimeout(r, 100));
        const options = Array.from(document.querySelectorAll('.ng-option, [role="option"]'));
        const matchedOption = options.find(opt => {
            const optText = opt.textContent.toUpperCase();
            return optText.includes(text.toUpperCase()) || (text.toUpperCase() === 'JAIPUR' && optText.includes('जयपुर'));
        });
        
        if (matchedOption) {
            console.log("[content.js] Found matching ng-select option:", matchedOption.textContent);
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
            if (query === "MORTGAGE/ CHARGE") {
                isMatch = optText.includes("बंधक/भार");
            } else if (query.includes("WITHOUT POSSESSION")) {
                isMatch = optText.includes("बिना कब्जे");
            } else if (query === "GENERAL") {
                isMatch = optText.includes("सामान्य");
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

function setInputValue(inputEl, value) {
    if (!inputEl) return false;
    inputEl.value = value;
    inputEl.dispatchEvent(new Event('input', { bubbles: true }));
    inputEl.dispatchEvent(new Event('change', { bubbles: true }));
    inputEl.dispatchEvent(new Event('blur', { bubbles: true }));
    return true;
}

function clickRadioByValueOrLabel(labelText) {
    const labels = Array.from(document.querySelectorAll('label, span, div'));
    const matchedLabel = labels.find(l => l.textContent.trim().toUpperCase() === labelText.toUpperCase());
    if (matchedLabel) {
        matchedLabel.click();
        const parent = matchedLabel.parentElement;
        if (parent) {
            const radio = parent.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                radio.click();
                radio.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }
        }
    }
    
    const radios = Array.from(document.querySelectorAll('input[type="radio"]'));
    const valueMatch = radios.find(r => r.value && r.value.toUpperCase() === labelText.toUpperCase());
    if (valueMatch) {
        valueMatch.checked = true;
        valueMatch.click();
        valueMatch.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
    }
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

async function bypassVerificationModal(verifyType, sendResponse, successMsg) {
    console.log(`[RM-Maker] Starting bypassVerificationModal for type: ${verifyType}`);
    
    try {
        // Step 1: Poll for the verification dropdown
        let verificationTypeSelect = null;
        for (let i = 0; i < 40; i++) {
            const allSelects = Array.from(document.querySelectorAll('select'));
            verificationTypeSelect = allSelects.find(s => {
                const opts = Array.from(s.options).map(o => o.text.toUpperCase());
                return opts.some(t => t.includes('PUBLIC') || t.includes('BANK') || t.includes('सार्वजनिक'));
            });
            if (verificationTypeSelect) break;
            await new Promise(r => setTimeout(r, 50));
        }
        
        if (!verificationTypeSelect) {
            console.error("[RM-Maker] Verification dropdown not found after polling.");
            sendResponse({ success: false, error: 'Verification modal dropdown not found.' });
            return;
        }
        
        // Select Public or Bank
        await setSelectValueByText(verificationTypeSelect, verifyType);
        
        // Step 2: Poll for the radio buttons to render
        let withoutOtpRadio = null;
        for (let i = 0; i < 30; i++) {
            const allRadios = Array.from(document.querySelectorAll('input[type="radio"]'));
            withoutOtpRadio = allRadios.find(r => {
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
            if (withoutOtpRadio) break;
            await new Promise(r => setTimeout(r, 50));
        }
        
        if (!withoutOtpRadio) {
            console.error("[RM-Maker] 'Without OTP' radio button not found after polling.");
            sendResponse({ success: false, error: 'Without OTP option not found.' });
            return;
        }
        
        // Click the Without OTP radio
        withoutOtpRadio.checked = true;
        withoutOtpRadio.click();
        withoutOtpRadio.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Step 3: Poll for the Submit button to render and become clickable
        let submitBtn = null;
        for (let i = 0; i < 30; i++) {
            submitBtn = document.getElementById('btnsubmit') || 
                        Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"], a')).find(b => {
                            const txt = b.textContent.trim().toUpperCase();
                            return txt === 'SUBMIT' || txt.includes('प्रस्तुत करें');
                        });
            if (submitBtn && (submitBtn.offsetWidth > 0 || submitBtn.offsetHeight > 0)) {
                break;
            }
            submitBtn = null;
            await new Promise(r => setTimeout(r, 50));
        }
        
        if (submitBtn) {
            console.log("[RM-Maker] Clicking verification Submit button.");
            submitBtn.click();
            sendResponse({ success: true, message: successMsg });
        } else {
            console.error("[RM-Maker] Submit button not found in modal after polling.");
            sendResponse({ success: false, error: 'Submit button not found.' });
        }
    } catch (e) {
        console.error("[RM-Maker] Error in bypassVerificationModal:", e);
        sendResponse({ success: false, error: e.message });
    }
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
                
                await new Promise(r => setTimeout(r, 600)); // Minimal wait for modal submit action
                
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
                                    }, 100);
                                    
                                    sendResponse({ success: true, message: 'Autofilled details, clicked Save, and confirmed modal!' });
                                }
                            }, 50);
                            
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

// =====================================================================
// 2b. Calculate Duty (Step 5-6 in notes)
// =====================================================================

async function autofillCalculateDuty(data, sendResponse) {
    try {
        const url = window.location.href;
        const urlLower = url.toLowerCase();
        
        if (urlLower.includes('/propertyvaluation/propertydetail')) {
            showStatusToast("Checking Stamp Duty Calculation...");
            
            // Retrieve stampDutyCalculated status from local storage
            const storage = await new Promise(resolve => {
                chrome.storage.local.get(['stampDutyCalculated'], resolve);
            });
            
            if (storage.stampDutyCalculated) {
                showStatusToast("Proceeding to Party details screen...");
                const partyDetailBtn = document.querySelector('button[formaction*="/Party/Viewparty" i]') || 
                                       document.querySelector('button[formaction*="viewparty" i]') ||
                                       Array.from(document.querySelectorAll('button, a')).find(b => {
                                           const txt = b.textContent.toUpperCase();
                                           return txt.includes('PARTY DETAIL') || txt.includes('पक्षकार विवरण');
                                       });
                                       
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
                const calcBtn = document.querySelector('button[formaction*="/PropertyValuation/CalculateDuty" i]') || 
                                document.querySelector('button[formaction*="calculateduty" i]') ||
                                Array.from(document.querySelectorAll('button, a')).find(b => {
                                    const txt = b.textContent.toUpperCase();
                                    return txt.includes('CALCULATE DUTY') || txt.includes('ड्यूटी की गणना करें');
                                });
                                
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
                        // Set the stampDutyCalculated state to true in local storage immediately before clicking submit
                        chrome.storage.local.set({ stampDutyCalculated: true }, () => {
                            calcSaveBtn.click();
                            
                            // Poll for SweetAlert2 modal to appear
                            const checkInterval = setInterval(() => {
                                showStatusToast("Waiting for Calculation Saved popup...");
                                const swalOkBtn = document.querySelector('.swal2-confirm') || 
                                                  Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'OK' && (b.offsetWidth > 0 || b.offsetHeight > 0));
                                if (swalOkBtn) {
                                    showStatusToast("Confirming calculation (Clicking OK)...");
                                    clearInterval(checkInterval);
                                    swalOkBtn.click();
                                    setTimeout(() => {
                                        hideStatusToast();
                                    }, 100);
                                    sendResponse({ success: true, message: 'Autofilled execution date, face value, saved, and confirmed!' });
                                }
                            }, 50);
                            
                            // Safety timeout (clear interval after 8 seconds)
                            setTimeout(() => {
                                clearInterval(checkInterval);
                                // If no popup appeared after 8s (e.g. redirected already), send response
                                sendResponse({ success: true, message: 'Submitted stamp duty calculation.' });
                            }, 8000);
                        });
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

// =====================================================================
// 3. Autofill Executant (Steps 8-10 in notes)
// =====================================================================

function autofillExecutants(data, sendResponse, stage = "EXECUTANT") {
    if (!data.executants || data.executants.length === 0) {
        sendResponse({ success: false, error: 'No executants data available.' });
        return;
    }
    
    const idx = (stage === "EXECUTANT") ? 0 : parseInt(stage.split("_")[1]);
    if (idx >= data.executants.length) {
        sendResponse({ success: false, error: `Executant index ${idx} out of range.` });
        return;
    }
    
    const exec = data.executants[idx];
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
        const isFirst = (idx === 0);
        fillPartyFormFields(exec, isFirst, isFirst)
            .then(() => {
                sendResponse({ success: true, message: `Autofilled Executant ${idx + 1} details! Review and click Save.` });
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
                               return txt.includes('WITNESS') || txt.includes('गवाह') || txt.includes('साक्षी') || (el.src && el.src.includes('witness'));
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
        fillPartyFormFields(wit, false, false, true)
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
// 7. One-Click Page Autofill
// =====================================================================

async function oneClickAutofill(data, sendResponse) {
    try {
        // Ensure gender_card is computed if not present
        if (!data.gender_card && data.executants) {
            data.gender_card = computeGenderCard(data.executants);
        }
        
        const url = window.location.href;
        const urlLower = url.toLowerCase();

        // Helper function to handle district selection on the dashboard
        async function selectDistrictAndSubmit(distSelect) {
            showStatusToast("Selecting District 'JAIPUR'...");
            const success = await setSelectValueByText(distSelect, "JAIPUR");
            if (success) {
                showStatusToast("District selected! Waiting to submit modal...");
                setTimeout(() => {
                    const modalEl = distSelect.closest('.modal-content, .modal, .modal-dialog');
                    const submitBtn = modalEl?.querySelector('button[type="submit"], button.btn-primary, .btn-primary, #btnsubmit') || 
                                      document.querySelector('.login-arrow') || 
                                      document.querySelector('.fa-arrow-right, .fa-arrow-circle-right');
                    if (submitBtn) {
                        showStatusToast("Submitting District Selection...");
                        submitBtn.click();
                        sendResponse({ success: true, message: 'Selected district JAIPUR and submitted modal!' });
                    } else {
                        // Fallback change trigger
                        distSelect.dispatchEvent(new Event('change', { bubbles: true }));
                        sendResponse({ success: true, message: 'Selected district JAIPUR!' });
                    }
                }, 1500);
            } else {
                showStatusToast("Failed to select JAIPUR in dropdown.", false);
                sendResponse({ success: false, error: 'Could not select JAIPUR in district dropdown.' });
            }
        }

        // 1. Citizen Dashboard
        if (urlLower.includes('/citizen/dashboard')) {
            const distSelect = document.getElementById('ddlDistrict');
            // Verify if the district dropdown is actually visible (modal is open)
            const isModalOpen = distSelect && (distSelect.offsetWidth > 0 || distSelect.offsetHeight > 0 || distSelect.getBoundingClientRect().width > 0);
            
            if (isModalOpen) {
                // District modal is already open, select and submit
                selectDistrictAndSubmit(distSelect);
            } else {
                showStatusToast("Opening Valuation Modal...");
                // Click Add New Valuation button to open modal - ID is specific
                let addValuationBtn = document.getElementById('addnewproperty');
                const isBtnVisible = addValuationBtn && (addValuationBtn.offsetWidth > 0 || addValuationBtn.offsetHeight > 0 || addValuationBtn.getBoundingClientRect().width > 0);
                
                if (!isBtnVisible) {
                    // Fallback to text matching
                    addValuationBtn = Array.from(document.querySelectorAll('button, input, a')).find(el => {
                        const isVisible = el.offsetWidth > 0 || el.offsetHeight > 0 || el.getBoundingClientRect().width > 0;
                        if (!isVisible) return false;
                        
                        const txt = el.textContent.trim().toUpperCase();
                        return txt.includes('ADD NEW VALUATION') || txt.includes('मूल्यांकन जोड़ें');
                    });
                }
                                        
                if (addValuationBtn) {
                    addValuationBtn.click();
                    
                    // Wait 1.5 seconds for modal to appear and become visible
                    setTimeout(() => {
                        const newDistSelect = document.getElementById('ddlDistrict');
                        if (newDistSelect) {
                            selectDistrictAndSubmit(newDistSelect);
                        } else {
                            showStatusToast("Failed to open district selection modal.", false);
                            sendResponse({ success: false, error: 'District dropdown did not appear in modal.' });
                        }
                    }, 1500);
                } else {
                    showStatusToast("Valuation button not found.", false);
                    sendResponse({ success: false, error: 'Could not find visible "+ Add New Valuation" button.' });
                }
            }
            return;
        }

        // 2. Property Valuation (Details vs Property Detail vs Calculate Duty Page)
        if (urlLower.includes('/propertyvaluation')) {
            if (urlLower.includes('/propertyvaluation/propertydetail')) {
                autofillCalculateDuty(data, sendResponse);
                return;
            }
            if (urlLower.includes('/propertyvaluation/calculateduty')) {
                autofillCalculateDuty(data, sendResponse);
                return;
            }
            
            // Otherwise, we are on the main Document Details page
            showStatusToast("Starting Document Details Autofill...");
            autofillDetails(data, sendResponse, true);
            return;
        }

        // 3. Fallbacks: Route to specific step function based on active URL
        if (urlLower.includes('/login')) {
            autofillLogin(data, sendResponse);
        } else if (urlLower.includes('/party/viewparty') || urlLower.includes('/party/partyadd')) {
            // Read partyStage from local storage (default to EXECUTANT if not set)
            const storage = await new Promise(resolve => {
                chrome.storage.local.get(['partyStage'], resolve);
            });
            const stage = storage.partyStage || "EXECUTANT";
            
            if (stage === "DONE") {
                if (chrome && chrome.storage && chrome.storage.local) {
                    chrome.storage.local.set({ oneClickRunning: false });
                }
                sendResponse({ success: true, message: 'All parties (Borrower, Bank, Witnesses) have been successfully added!' });
                return;
            }
            
            if (urlLower.includes('/party/partyadd')) {
                showStatusToast(`Filling ${stage} Details...`);
                
                let fillPromise = null;
                let nextStage = "CLAIMANT";
                
                if (stage.startsWith("EXECUTANT")) {
                    const idx = (stage === "EXECUTANT") ? 0 : parseInt(stage.split("_")[1]);
                    const exec = data.executants[idx];
                    const isFirst = (idx === 0);
                    fillPromise = fillPartyFormFields(exec, isFirst, isFirst, false);
                    
                    if (idx + 1 < data.executants.length) {
                        nextStage = `EXECUTANT_${idx + 1}`;
                    } else {
                        nextStage = "CLAIMANT";
                    }
                } else if (stage === "CLAIMANT") {
                    const cl = data.claimant;
                    fillPromise = fillPartyFormFields(cl, false, false, false);
                    nextStage = "WITNESS_1";
                } else if (stage === "WITNESS_1") {
                    const wit = data.witnesses[0];
                    fillPromise = fillPartyFormFields(wit, false, false, true);
                    nextStage = "WITNESS_2";
                } else if (stage === "WITNESS_2") {
                    const wit = data.witnesses[1];
                    fillPromise = fillPartyFormFields(wit, false, false, true);
                    nextStage = "PRESENTER";
                }
                
                if (fillPromise) {
                    try {
                        await fillPromise;
                        
                        // Check missing fields before saving
                        const missingField = checkRequiredFields();
                        if (missingField) {
                            showStatusToast(`⚠️ Missing required field: ${missingField}. Please fill it and click Save manually.`, false);
                            sendResponse({ success: false, error: `${missingField} is required but empty.` });
                            return;
                        }
                        
                        // Wait 800ms before clicking Save
                        await new Promise(r => setTimeout(r, 800));
                        
                        const saved = triggerButtonByText("Save");
                        if (saved) {
                            showStatusToast("Waiting for success confirmation...");
                            let clickedOk = false;
                            for (let i = 0; i < 40; i++) {
                                const swalContainer = document.querySelector('.swal2-container');
                                if (swalContainer) {
                                    const isError = swalContainer.querySelector('.swal2-error, .swal2-warning') || 
                                                    swalContainer.innerText.toLowerCase().includes('error') || 
                                                    swalContainer.innerText.toLowerCase().includes('select') || 
                                                    swalContainer.innerText.toLowerCase().includes('required') || 
                                                    swalContainer.innerText.includes('चुनें') || 
                                                    swalContainer.innerText.includes('अनिवार्य');
                                    if (isError) {
                                        showStatusToast(`⚠️ Save Failed: "${swalContainer.innerText.split('\n')[0]}". Correct it and click Save manually.`, false);
                                        sendResponse({ success: false, error: 'SweetAlert error modal detected.' });
                                        return;
                                    }
                                }
                                
                                const okBtn = document.querySelector('.swal2-confirm, .swal-button--confirm') || 
                                              Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim().toUpperCase() === 'OK' || b.textContent.trim().includes('ठीक है'));
                                if (okBtn && (okBtn.offsetWidth > 0 || okBtn.offsetHeight > 0)) {
                                    await new Promise(r => setTimeout(r, 450));
                                    okBtn.click();
                                    okBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                                    
                                    await new Promise(r => setTimeout(r, 300));
                                    const stillExists = document.querySelector('.swal2-confirm, .swal-button--confirm');
                                    if (stillExists) {
                                        stillExists.click();
                                        stillExists.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                                    }
                                    
                                    // Update stage in local storage
                                    const updates = { partyStage: nextStage };
                                    if (nextStage === "DONE") {
                                        updates.oneClickRunning = false;
                                    }
                                    chrome.storage.local.set(updates, () => {
                                        setTimeout(() => hideStatusToast(), 100);
                                        sendResponse({ success: true, message: `Successfully saved ${stage} and updated stage to ${nextStage}` });
                                    });
                                    clickedOk = true;
                                    break;
                                }
                                await new Promise(r => setTimeout(r, 150));
                            }
                            if (!clickedOk) {
                                showStatusToast("Saved (confirmation popup timed out).", false);
                                sendResponse({ success: true, message: "Saved, but popup confirmation timed out." });
                            }
                        } else {
                            showStatusToast("Save button not found. Please click Save manually.", false);
                            sendResponse({ success: false, error: 'Could not find the Save button on the Party form.' });
                        }
                    } catch (err) {
                        showStatusToast(`Error filling ${stage} form: ${err.message}`, false);
                        sendResponse({ success: false, error: err.message });
                    }
                } else {
                    sendResponse({ success: false, error: `Invalid partyStage: ${stage}` });
                }
            } else {
                // We are on Viewparty
                showStatusToast(`Routing party step: ${stage}...`);
                if (stage.startsWith("EXECUTANT")) {
                    autofillExecutants(data, sendResponse, stage);
                } else if (stage === "CLAIMANT") {
                    autofillClaimant(data, sendResponse);
                } else if (stage === "WITNESS_1") {
                    autofillWitnessN(data, 0, sendResponse);
                } else if (stage === "WITNESS_2") {
                    autofillWitnessN(data, 1, sendResponse);
                } else if (stage === "PRESENTER") {
                    showStatusToast("Opening Presenter Details...");
                    const presenterBtn = document.querySelector('button[onclick*="PresenterDetailClick"]') ||
                                         Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Presenter Details'));
                    if (presenterBtn) {
                        presenterBtn.click();
                        
                        // Wait 1.5 seconds for the modal to open
                        setTimeout(() => {
                            showStatusToast("Selecting Presenter Option: Self...");
                            const selfRadio = document.getElementById('rblpoa_0') || 
                                              document.querySelector('input[name="rblpoa"][value="0"]');
                            if (selfRadio) {
                                selfRadio.click();
                                selfRadio.dispatchEvent(new Event('change', { bubbles: true }));
                                
                                // Wait 800ms before saving
                                setTimeout(() => {
                                    showStatusToast("Saving Presenter Details...");
                                    const saveBtn = document.getElementById('poadetailssave') || 
                                                    document.querySelector('button[id*="poadetails" i]');
                                    if (saveBtn) {
                                        saveBtn.click();
                                        
                                        // Poll for SweetAlert2 OK button
                                        const checkInterval = setInterval(() => {
                                            showStatusToast("Waiting for Presenter Saved popup...");
                                            const swalOkBtn = document.querySelector('.swal2-confirm') || 
                                                              Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'OK' && (b.offsetWidth > 0 || b.offsetHeight > 0));
                                            if (swalOkBtn) {
                                                showStatusToast("Presenter details saved successfully!");
                                                clearInterval(checkInterval);
                                                
                                                // Set stage to DONE and stop automation
                                                chrome.storage.local.set({ partyStage: "DONE", oneClickRunning: false }, () => {
                                                    swalOkBtn.click();
                                                    setTimeout(() => hideStatusToast(), 100);
                                                    sendResponse({ success: true, message: 'Presenter Details saved! One-Click Autofill Complete.' });
                                                });
                                            }
                                        }, 50);
                                        
                                        // Safety timeout (clear interval after 8 seconds)
                                        setTimeout(() => clearInterval(checkInterval), 8000);
                                    } else {
                                        showStatusToast("Save button not found in Presenter modal.", false);
                                        sendResponse({ success: false, error: 'Could not find Presenter modal Save button.' });
                                    }
                                }, 800);
                            } else {
                                showStatusToast("Self radio option not found in Presenter modal.", false);
                                sendResponse({ success: false, error: 'Could not locate Self radio button in Presenter modal.' });
                            }
                        }, 1500);
                    } else {
                        showStatusToast("Presenter Details button not found.", false);
                        sendResponse({ success: false, error: 'Could not find Presenter Details button.' });
                    }
                } else {
                    sendResponse({ success: false, error: `Unknown partyStage: ${stage}` });
                }
            }
        } else {
            sendResponse({ success: false, error: 'No automation matches this URL. Navigate to Dashboard, Login, or Details page first.' });
        }
    } catch (e) {
        console.error("[RM-Maker Autofill] Error in oneClickAutofill:", e);
        sendResponse({ success: false, error: e.message });
    }
}

// Helper: compute gender_card from executants array (same logic as popup.js getGenderCardType)
function computeGenderCard(executants) {
    if (!executants || executants.length === 0) return 'MALE_GEN';
    const genders = executants.map(e => e.gender);
    const hasMale = genders.includes('MALE');
    const hasFemale = genders.includes('FEMALE');
    if (hasMale && hasFemale) return 'JOINT';
    if (hasFemale) return 'FEMALE_GEN';
    return 'MALE_GEN';
}

// Auto-run on page load if one-click automation is active
try {
    if (chrome && chrome.storage && chrome.storage.local) {
        chrome.storage.local.get(['oneClickRunning', 'oneClickData', 'activeCaseData'], (res) => {
            if (res.oneClickRunning && (res.oneClickData || res.activeCaseData)) {
                const urlLower = window.location.href.toLowerCase();
                // DO NOT auto-run on Dashboard to prevent accidental loops on fresh visits
                if (urlLower.includes('/citizen/dashboard')) {
                    console.log("[RM-Maker] Dashboard page detected. Resetting oneClickRunning flag to prevent auto-loops.");
                    chrome.storage.local.set({ oneClickRunning: false });
                    return;
                }
                
                // Build the complete data payload, computing gender_card if missing
                const caseData = res.oneClickData || res.activeCaseData;
                if (!caseData.gender_card) {
                    caseData.gender_card = computeGenderCard(caseData.executants);
                }
                
                const runAutofill = () => {
                    console.log("[RM-Maker] Starting auto-execution immediately...");
                    oneClickAutofill(caseData, (response) => {
                        console.log("[RM-Maker] Auto-execution step response:", response);
                        if (response && !response.success) {
                            console.error("[RM-Maker] Step auto-execution failed:", response.error);
                        }
                    });
                };

                // Check readiness immediately or bind to DOMContentLoaded/load with 250ms fallback
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
                    setTimeout(triggerOnce, 250);
                }
            }
        });
    }
} catch (e) {
    console.error("[RM-Maker] Error in page-load auto-execution check:", e);
}
