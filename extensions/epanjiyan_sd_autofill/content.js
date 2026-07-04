// Content script for Rajasthan e-Panjiyan Sale Deed (SD) Autofill
console.log("[SD Autofill] Content script loaded on:", window.location.href);

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log("[SD Autofill] Message received:", request.action);
    
    try {
        switch (request.action) {
            case 'one_click_autofill':
                oneClickAutofill(request.data, sendResponse);
                break;
            case 'autofill_district':
                autofillDistrict(request.data, sendResponse);
                break;
            case 'autofill_details':
                autofillDetails(request.data, sendResponse);
                break;
            case 'autofill_address':
                autofillAddress(request.data, sendResponse);
                break;
            case 'autofill_calculate_duty':
                autofillCalculateDuty(request.data, sendResponse);
                break;
            default:
                sendResponse({ success: false, error: 'Unknown action' });
        }
    } catch (e) {
        console.error("[SD Autofill] Exception in script:", e);
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
            toastElement.id = 'sd-autofill-toast';
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
        
        if (!document.getElementById('sd-toast-style')) {
            const style = document.createElement('style');
            style.id = 'sd-toast-style';
            style.textContent = `
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }
    } catch (e) {
        console.error("[SD Autofill] Error showing status toast:", e);
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
        console.error("[SD Autofill] Error hiding status toast:", e);
    }
}

// Select2 element filling helper
async function setSelectValueByText(selectEl, text, cleanString = true) {
    if (!selectEl) return false;
    
    const searchVal = cleanString ? text.trim().toUpperCase() : text;
    let matchedOption = Array.from(selectEl.options).find(opt => {
        const optText = cleanString ? opt.text.trim().toUpperCase() : opt.text;
        return optText === searchVal || optText.includes(searchVal);
    });
    
    if (!matchedOption) return false;
    
    selectEl.value = matchedOption.value;
    selectEl.dispatchEvent(new Event('change', { bubbles: true }));
    
    // Trigger Select2 custom change triggers
    const select2Container = selectEl.nextElementSibling;
    if (select2Container && select2Container.classList.contains('select2-container')) {
        const renderSpan = select2Container.querySelector('.select2-selection__rendered');
        if (renderSpan) {
            renderSpan.textContent = matchedOption.text;
            renderSpan.title = matchedOption.text;
        }
    }
    return true;
}

// Select2 value-based selection helper
async function setSelectValueByValue(selectEl, value) {
    if (!selectEl) return false;
    selectEl.value = value;
    selectEl.dispatchEvent(new Event('change', { bubbles: true }));
    
    const select2Container = selectEl.nextElementSibling;
    if (select2Container && select2Container.classList.contains('select2-container')) {
        const renderSpan = select2Container.querySelector('.select2-selection__rendered');
        const matchedOption = selectEl.querySelector(`option[value="${value}"]`);
        if (renderSpan && matchedOption) {
            renderSpan.textContent = matchedOption.text;
            renderSpan.title = matchedOption.text;
        }
    }
    return true;
}

function clickRadioByValueOrLabel(labelText) {
    const cleanLabel = labelText.toLowerCase().replace(/\s+/g, '').trim();
    const radios = Array.from(document.querySelectorAll('input[type="radio"]'));
    const matched = radios.find(r => {
        const val = r.value.toLowerCase().replace(/\s+/g, '').trim();
        const id = r.id.toLowerCase().replace(/\s+/g, '').trim();
        if (val.includes(cleanLabel) || id.includes(cleanLabel)) return true;
        
        // Check labels
        const parent = r.parentElement;
        if (parent && parent.textContent.toLowerCase().replace(/\s+/g, '').includes(cleanLabel)) return true;
        return false;
    });
    
    if (matched) {
        matched.checked = true;
        matched.click();
        matched.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
    }
    return false;
}

// Levenshtein fuzzy string match helpers
function levenshteinDistance(s1, s2) {
    s1 = s1.toLowerCase().replace(/[^a-z0-9]/g, '');
    s2 = s2.toLowerCase().replace(/[^a-z0-9]/g, '');
    
    const track = Array(s2.length + 1).fill(null).map(() =>
        Array(s1.length + 1).fill(null));
    for (let i = 0; i <= s1.length; i += 1) {
        track[0][i] = i;
    }
    for (let j = 0; j <= s2.length; j += 1) {
        track[j][0] = j;
    }
    for (let j = 1; j <= s2.length; j += 1) {
        for (let i = 1; i <= s1.length; i += 1) {
            const indicator = s1[i - 1] === s2[j - 1] ? 0 : 1;
            track[j][i] = Math.min(
                track[j - 1][i] + 1, // deletion
                track[j][i - 1] + 1, // insertion
                track[j - 1][i - 1] + indicator // substitution
            );
        }
    }
    return track[s2.length][s1.length];
}

function stringSimilarity(s1, s2) {
    const longer = s1.length > s2.length ? s1 : s2;
    const shorter = s1.length > s2.length ? s2 : s1;
    if (longer.length === 0) return 1.0;
    const dist = levenshteinDistance(longer, shorter);
    return (longer.length - dist) / longer.length;
}

function cleanStringForColony(s) {
    if (!s) return "";
    return s.toLowerCase()
        .replace(/[^a-z0-9\s]/g, '')
        .replace(/\b(colony|nagar|road|gali|scheme|sec|sector|block)\b/g, '')
        .replace(/\s+/g, '')
        .trim();
}

// =====================================================================
// 3. One-Click Page Autofill
// =====================================================================

async function oneClickAutofill(data, sendResponse) {
    try {
        const url = window.location.href.toLowerCase();
        
        if (url.includes('/citizen/dashboard')) {
            autofillDistrict(data, sendResponse);
            return;
        }
        
        if (url.includes('/propertyvaluation')) {
            if (url.includes('/propertyvaluation/propertydetail')) {
                autofillCalculateDuty(data, sendResponse);
                return;
            }
            if (url.includes('/propertyvaluation/calculateduty')) {
                autofillCalculateDuty(data, sendResponse);
                return;
            }
            if (url.includes('/propertyvaluation/addpropertyaddress')) {
                autofillAddress(data, sendResponse);
                return;
            }
            // Main Document details page
            autofillDetails(data, sendResponse);
            return;
        }
        
        sendResponse({ success: false, error: 'Not on e-Panjiyan dashboard or valuation page.' });
    } catch (e) {
        console.error("[SD Autofill] Error in oneClickAutofill:", e);
        sendResponse({ success: false, error: e.message });
    }
}

// 0. District Selection & Dashboard Modal Navigation
async function autofillDistrict(data, sendResponse) {
    try {
        const distSelect = document.getElementById('ddlDistrict');
        const isModalOpen = distSelect && (distSelect.offsetWidth > 0 || distSelect.offsetHeight > 0);
        
        async function submitJaipur(selectEl) {
            showStatusToast("Selecting District 'JAIPUR'...");
            const success = await setSelectValueByText(selectEl, "JAIPUR");
            if (success) {
                showStatusToast("District selected! Submitting...");
                setTimeout(() => {
                    const modalEl = selectEl.closest('.modal-content, .modal, .modal-dialog');
                    const submitBtn = modalEl?.querySelector('button[type="submit"], button.btn-primary, #btnsubmit') ||
                                      document.querySelector('.login-arrow') ||
                                      document.querySelector('.fa-arrow-right');
                    if (submitBtn) {
                        submitBtn.click();
                        sendResponse({ success: true, message: 'District selected and submitted.' });
                    } else {
                        selectEl.dispatchEvent(new Event('change', { bubbles: true }));
                        sendResponse({ success: true, message: 'District selected.' });
                    }
                }, 1000);
            } else {
                sendResponse({ success: false, error: 'Could not select JAIPUR.' });
            }
        }
        
        if (isModalOpen) {
            await submitJaipur(distSelect);
        } else {
            showStatusToast("Opening Valuation Modal...");
            const addValuationBtn = document.getElementById('addnewproperty') ||
                                    Array.from(document.querySelectorAll('button, a')).find(el => el.textContent.trim().includes('Add New Valuation') || el.textContent.trim().includes('मूल्यांकन जोड़ें'));
            if (addValuationBtn) {
                addValuationBtn.click();
                setTimeout(async () => {
                    const newDistSelect = document.getElementById('ddlDistrict');
                    if (newDistSelect) {
                        await submitJaipur(newDistSelect);
                    } else {
                        sendResponse({ success: false, error: 'District selector not found.' });
                    }
                }, 1000);
            } else {
                sendResponse({ success: false, error: 'Add Valuation button not found.' });
            }
        }
    } catch (e) {
        sendResponse({ success: false, error: e.message });
    }
}

// Helper to determine the SD Category
function determineSDCategory(caseData) {
    const gender = (caseData.gender || 'male').toLowerCase();
    const caste = (caseData.caste || 'General').toUpperCase();
    const isFemale = gender === 'female';
    const isSCSTBPL = caste === 'SC' || caste === 'ST' || !!caseData.isBPL;
    
    if (isFemale && isSCSTBPL) return '4'; // Female SC/ST/BPL card
    if (isFemale) return '3'; // Female other than SC/ST/BPL card
    if (caseData.isJoint) return '6'; // Male/Female Joint card
    return '1'; // Male (GEN) card
}

// 1. Document Details Form Page (/PropertyValuation)
async function autofillDetails(data, sendResponse) {
    try {
        showStatusToast("Setting Location Type: Urban...");
        clickRadioByValueOrLabel("Urban (शहरी)");
        
        await new Promise(r => setTimeout(r, 400));
        
        showStatusToast("Selecting Transfer Status: Self...");
        const selfRadio = document.getElementById('radioself') || document.querySelector('input#radioself');
        if (selfRadio) {
            selfRadio.checked = true;
            selfRadio.click();
            selfRadio.dispatchEvent(new Event('change', { bubbles: true }));
        } else {
            clickRadioByValueOrLabel("Self (स्वयं)");
        }
        
        // Wait for Self Category Modal
        showStatusToast("Waiting for Gender/Category Modal...");
        let modalBody = null;
        for (let i = 0; i < 20; i++) {
            const modals = Array.from(document.querySelectorAll('.modal-body, .modal-dialog, .modal-content, .modal'));
            modalBody = modals.find(m => m.offsetWidth > 0 || m.offsetHeight > 0);
            if (modalBody) break;
            await new Promise(r => setTimeout(r, 150));
        }
        
        if (!modalBody) {
            sendResponse({ success: false, error: 'Gender/Category modal did not load.' });
            return;
        }
        
        const radioValue = determineSDCategory(data);
        showStatusToast(`Selecting Category Card option: ${radioValue}...`);
        const radioBtn = modalBody.querySelector(`input[name="individualdata"][value="${radioValue}"]`);
        if (radioBtn) {
            radioBtn.checked = true;
            radioBtn.click();
            radioBtn.dispatchEvent(new Event('change', { bubbles: true }));
            
            await new Promise(r => setTimeout(r, 300));
            
            const continueBtn = modalBody.querySelector('button[onclick*="setdatass"]') || 
                                modalBody.querySelector('button[onclick*="return setdatass()"]') ||
                                Array.from(modalBody.querySelectorAll('button')).find(b => b.textContent.trim().includes('Continue') || b.textContent.trim().includes('आगे बढ़ें'));
            if (continueBtn) {
                continueBtn.click();
            }
        }
        
        await new Promise(r => setTimeout(r, 600));
        
        // Document Type: Sale Deed (Conveyance)
        showStatusToast("Selecting Document Type: Sale Deed...");
        const docTypeSelect = document.getElementById('parentarticle_id');
        await setSelectValueByText(docTypeSelect, "Sale Deed (Conveyance)");
        
        await new Promise(r => setTimeout(r, 400));
        
        // SubType: Sale Deed
        showStatusToast("Selecting SubType: Sale Deed...");
        const subTypeSelect = document.getElementById('ddlDocSubType');
        await setSelectValueByText(subTypeSelect, "Sale Deed");
        
        await new Promise(r => setTimeout(r, 400));
        
        // Category dropdown
        showStatusToast("Selecting Category Dropdown...");
        const catSelect = document.getElementById('ddlCategory');
        let categoryVal = "General";
        if (radioValue === '4') {
            categoryVal = "Female SC/ST/BPL";
        } else if (radioValue === '3') {
            categoryVal = "Female other than SC/ST/BPL";
        }
        await setSelectValueByText(catSelect, categoryVal);
        
        // SRO & Tehsil
        showStatusToast("Selecting SRO & Tehsil...");
        const sroSelect = document.getElementById('ddlSRO');
        const tehsilSelect = document.getElementById('ddlTehsil');
        if (data.sro) await setSelectValueByText(sroSelect, data.sro);
        if (data.tehsil) await setSelectValueByText(tehsilSelect, data.tehsil);
        
        // Seva Pradata Name & Mobile
        showStatusToast("Filling Service Provider info...");
        const providerName = document.getElementById('sevaPradataName');
        const providerMobile = document.getElementById('sevaPradataMobile');
        if (providerName) {
            providerName.value = "SANKALP LAW ASSOCIATES";
            providerName.dispatchEvent(new Event('input', { bubbles: true }));
        }
        if (providerMobile) {
            providerMobile.value = "9799967384";
            providerMobile.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        await new Promise(r => setTimeout(r, 500));
        
        // Click Save
        showStatusToast("Saving document details...");
        const saveBtn = document.getElementById('savedocument');
        if (saveBtn) {
            saveBtn.click();
            sendResponse({ success: true, message: 'Document details successfully saved!' });
        } else {
            sendResponse({ success: false, error: 'Could not find the Save button.' });
        }
    } catch (e) {
        sendResponse({ success: false, error: e.message });
    }
}

