// Content script for Rajasthan e-Panjiyan Sale Deed (SD) Autofill
console.log("[SD Autofill] Content script loaded on:", window.location.href);

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log("[SD Autofill] Message received:", request.action);
    
    try {
        switch (request.action) {
            case 'ping':
                sendResponse({ success: true, message: 'pong' });
                break;
            case 'public_dlc_lookup_start':
                checkAutomatedStateOnLoad();
                sendResponse({ success: true, message: 'Automation loop triggered!' });
                break;
            case 'public_dlc_lookup':
                runPublicDlcLookup(request.data, sendResponse);
                break;
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

async function waitForPageBlockToDisappear(maxWaitMs = 10000) {
    const startTime = Date.now();
    while (Date.now() - startTime < maxWaitMs) {
        const blocks = document.querySelectorAll('.blockUI, .blockOverlay, .blockPage, .loading, .ajax-loader, .spinner');
        let isBlocked = false;
        for (const block of blocks) {
            if (block.offsetWidth > 0 || block.offsetHeight > 0) {
                isBlocked = true;
                break;
            }
        }
        const overlays = Array.from(document.querySelectorAll('div'));
        for (const div of overlays) {
            const txt = div.textContent.trim();
            if ((txt.includes("Saving document details") || txt.includes("Please Wait") || txt.includes("loading")) && (div.offsetWidth > 0 || div.offsetHeight > 0)) {
                const style = window.getComputedStyle(div);
                if (style.position === 'fixed' || style.position === 'absolute' || style.zIndex > 100) {
                    isBlocked = true;
                    break;
                }
            }
        }
        if (!isBlocked) {
            await new Promise(r => setTimeout(r, 200));
            return;
        }
        await new Promise(r => setTimeout(r, 200));
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
        await waitForPageBlockToDisappear(6000);
        
        // SubType: Sale Deed
        showStatusToast("Selecting SubType: Sale Deed...");
        const subTypeSelect = document.getElementById('ddlDocSubType');
        await setSelectValueByText(subTypeSelect, "Sale Deed");
        await waitForPageBlockToDisappear(6000);
        
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
        await waitForPageBlockToDisappear(6000);
        
        // SRO & Tehsil
        showStatusToast("Selecting SRO & Tehsil...");
        const sroSelect = document.getElementById('ddlSRO');
        const tehsilSelect = document.getElementById('ddlTehsil');
        if (data.sro) await setSelectValueByText(sroSelect, data.sro);
        if (data.tehsil) await setSelectValueByText(tehsilSelect, data.tehsil);
        await waitForPageBlockToDisappear(8000);
        
        // Seva Pradata Name & Mobile
        showStatusToast("Filling Service Provider info...");
        const providerName = document.getElementById('sevaPradataName');
        const providerMobile = document.getElementById('sevaPradataMobile');
        if (providerName) {
            providerName.value = "SANKALP LAW ASSOCIATES";
            providerName.dispatchEvent(new Event('input', { bubbles: true }));
            providerName.dispatchEvent(new Event('change', { bubbles: true }));
        }
        if (providerMobile) {
            providerMobile.value = "9799967384";
            providerMobile.dispatchEvent(new Event('input', { bubbles: true }));
            providerMobile.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        await new Promise(r => setTimeout(r, 600));
        
        // Click Save
        showStatusToast("Saving document details...");
        const saveBtn = document.getElementById('savedocument');
        if (saveBtn) {
            saveBtn.click();
            
            // Wait for and click SweetAlert2 success modal confirmation button
            showStatusToast("Waiting for success confirmation...");
            let clickedOk = false;
            for (let i = 0; i < 40; i++) {
                const okBtn = document.querySelector('.swal2-confirm, .swal-button--confirm') || 
                              Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim().includes('OK') || b.textContent.trim().includes('ठीक है'));
                if (okBtn && (okBtn.offsetWidth > 0 || okBtn.offsetHeight > 0)) {
                    okBtn.click();
                    clickedOk = true;
                    break;
                }
                await new Promise(r => setTimeout(r, 150));
            }
            
            if (clickedOk) {
                sendResponse({ success: true, message: 'Document details successfully saved and confirmed!' });
            } else {
                sendResponse({ success: true, message: 'Document details saved (modal confirmation timed out).' });
            }
        } else {
            sendResponse({ success: false, error: 'Could not find the Save button.' });
        }
    } catch (e) {
        sendResponse({ success: false, error: e.message });
    }
}

// Helper to determine Property Type (Plot/FLAT/HOUSE)
function determinePropertyType(propertyData) {
    const address = (propertyData.address || "").toLowerCase();
    const plotArea = parseFloat(propertyData.area || propertyData.plot_area || 0);
    const constArea = parseFloat(propertyData.constructed_area || 0);
    const isFlatKey = address.includes("flat") || address.includes("apartment") || address.includes("tower") || address.includes("unit") || address.includes("block");
    
    if (plotArea > 0 && constArea === 0 && !isFlatKey) {
        return "Plot";
    }
    if (isFlatKey || (constArea > 0 && plotArea === 0)) {
        return "FLAT";
    }
    if (plotArea > 0 && constArea > 0) {
        return "HOUSE";
    }
    return "Plot"; // Default fallback
}

// Helper to split plot number into three input boxes
function splitPlotNumber(plotStr) {
    let plot1 = "";
    let plot2 = "";
    let plot3 = "";
    
    const cleanPlot = (plotStr || "").trim();
    
    // Match block/sector prefix like "F-", "A-", "Sec-3 "
    const blockMatch = cleanPlot.match(/^([A-Z0-9]+)\s*[-/]\s*(.*)$/i);
    if (blockMatch) {
        plot1 = blockMatch[1];
        const rest = blockMatch[2].trim();
        
        const slashIndex = rest.indexOf('/');
        if (slashIndex !== -1) {
            plot2 = rest.substring(0, slashIndex + 1).trim(); // includes the slash
            plot3 = rest.substring(slashIndex + 1).trim();
        } else {
            plot2 = rest;
        }
    } else {
        const slashIndex = cleanPlot.indexOf('/');
        if (slashIndex !== -1) {
            plot2 = cleanPlot.substring(0, slashIndex + 1).trim();
            plot3 = cleanPlot.substring(slashIndex + 1).trim();
        } else {
            plot2 = cleanPlot;
        }
    }
    return { plot1, plot2, plot3 };
}

// 2. Add Property Address Page (/PropertyValuation/AddPropertyAddress)
async function autofillAddress(data, sendResponse) {
    try {
        const prop = data.property || {};
        
        // 2.1 Set Property Type
        showStatusToast("Selecting Property Type...");
        const propTypeSelect = document.getElementById('ddlpropertytype');
        const detectedType = determinePropertyType(prop);
        await setSelectValueByText(propTypeSelect, detectedType);
        
        await new Promise(r => setTimeout(r, 400));

        // Pre-select Category Type and Location (Interior/Exterior) if they are populated (optional helper)
        const ddlCatType = document.getElementById('ddlCategoryType');
        if (ddlCatType && ddlCatType.options.length > 1) {
            showStatusToast("Pre-selecting Category Type (Residential)...");
            await setSelectValueByText(ddlCatType, "Residential");
            await new Promise(r => setTimeout(r, 200));
        }
        
        const roadWidth = parseFloat(prop.road_width || 30);
        const locValue = roadWidth <= 30 ? "0" : "1"; // 0 is Interior, 1 is Exterior
        const locRadio = document.querySelector(`input[name="Location"][value="${locValue}"]`);
        if (locRadio) {
            showStatusToast(`Pre-setting Location (Road Width: ${roadWidth} ft)...`);
            locRadio.checked = true;
            locRadio.click();
            locRadio.dispatchEvent(new Event('change', { bubbles: true }));
            await new Promise(r => setTimeout(r, 200));
        }
        await new Promise(r => setTimeout(r, 200));
        
        // 2.2 Select Colony (Fuzzy Match & Highest DLC comparison)
        showStatusToast("Analyzing Colony DLC rates...");
        const ddlColony = document.getElementById('ddlColony');
        let bestOption = null;
        let maxDLC = 0;
        
        if (ddlColony) {
            const cleanTarget = cleanStringForColony(prop.colony);
            let candidates = [];
            
            // Search fuzzy matches
            for (let opt of ddlColony.options) {
                if (!opt.value) continue;
                const cleanOpt = cleanStringForColony(opt.text);
                const score = stringSimilarity(cleanTarget, cleanOpt);
                if (score >= 0.85) {
                    candidates.push({ option: opt, score: score });
                }
            }
            
            // Search JDA fallback if no fuzzy match
            if (candidates.length === 0) {
                for (let opt of ddlColony.options) {
                    const txt = opt.text.toLowerCase();
                    if (txt.includes("jda") || txt.includes("जे.डी.ए")) {
                        candidates.push({ option: opt, score: 0.5 });
                    }
                }
            }
            
            // Sequentially check and choose highest DLC
            const dlcInput = document.getElementById('txtDLC') || document.querySelector('input[id*="dlc" i]') || document.querySelector('input[id*="Dlc" i]');
            const checkedRatesLog = [];
            
            console.log("[SD Autofill] Starting Colony DLC rate verification checks...");
            for (let cand of candidates) {
                showStatusToast(`Checking: Selecting Colony ${cand.option.text}...`);
                
                // 1. Select the colony
                ddlColony.value = cand.option.value;
                ddlColony.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Select2 UI rendering update
                const select2Container = ddlColony.nextElementSibling;
                if (select2Container && select2Container.classList.contains('select2-container')) {
                    const renderSpan = select2Container.querySelector('.select2-selection__rendered');
                    if (renderSpan) renderSpan.textContent = cand.option.text;
                }
                
                // Wait for the colony AJAX to finish loading category type options
                await new Promise(r => setTimeout(r, 450));
                
                // 2. Select Category Type (Residential) now that options are populated for this colony
                if (ddlCatType) {
                    showStatusToast(`Checking: Selecting Category Residential for ${cand.option.text}...`);
                    await setSelectValueByText(ddlCatType, "Residential");
                    await new Promise(r => setTimeout(r, 200));
                }
                
                // 3. Select Location (Interior / Exterior)
                if (locRadio) {
                    showStatusToast(`Checking: Setting Location for ${cand.option.text}...`);
                    locRadio.checked = true;
                    locRadio.click();
                    locRadio.dispatchEvent(new Event('change', { bubbles: true }));
                    await new Promise(r => setTimeout(r, 200));
                }
                
                // Wait for the DLC rate AJAX to populate
                await new Promise(r => setTimeout(r, 550));
                
                let cleanDlc = 0;
                if (dlcInput) {
                    const dlcText = dlcInput.value || "";
                    cleanDlc = parseFloat(dlcText.replace(/[^0-9.]/g, '')) || 0;
                    if (cleanDlc > maxDLC) {
                        maxDLC = cleanDlc;
                        bestOption = cand.option;
                    }
                }
                checkedRatesLog.push({ colony: cand.option.text, rate: cleanDlc });
                console.log(`[SD Autofill] Checked option: "${cand.option.text}" -> DLC Rate: ${cleanDlc}`);
            }
            
            console.log("[SD Autofill] --- DLC Comparison Log Summary ---");
            checkedRatesLog.forEach((item, index) => {
                console.log(`  [${index + 1}] Colony: "${item.colony}" | Rate: ${item.rate}`);
            });
            console.log(`[SD Autofill] Selected best candidate: "${bestOption ? bestOption.text : 'None'}" with rate ${maxDLC}`);
            
            if (bestOption) {
                // Show a comprehensive toast to the user listing all rates
                const summaryText = checkedRatesLog.map(r => `${r.colony.substring(0, 18)}..: Rs ${r.rate}`).join('\n');
                showStatusToast(`DLC Rates Checked:\n${summaryText}\nSelecting: ${bestOption.text} (DLC: ${maxDLC})...`, true);
                
                ddlColony.value = bestOption.value;
                ddlColony.dispatchEvent(new Event('change', { bubbles: true }));
                const select2Container = ddlColony.nextElementSibling;
                if (select2Container && select2Container.classList.contains('select2-container')) {
                    const renderSpan = select2Container.querySelector('.select2-selection__rendered');
                    if (renderSpan) renderSpan.textContent = bestOption.text;
                }
                await new Promise(r => setTimeout(r, 450));
            } else if (ddlColony.options.length > 1) {
                ddlColony.value = ddlColony.options[1].value;
                ddlColony.dispatchEvent(new Event('change', { bubbles: true }));
                await new Promise(r => setTimeout(r, 450));
            }
        }
        
        // Confirm Category Type is selected on the final choice
        showStatusToast("Confirming Category Type: Residential...");
        if (ddlCatType) {
            await setSelectValueByText(ddlCatType, "Residential");
        }
        await new Promise(r => setTimeout(r, 300));
        
        // Confirm Location (Interior / Exterior) is selected on the final choice
        showStatusToast(`Confirming Location...`);
        if (locRadio) {
            locRadio.checked = true;
            locRadio.click();
            locRadio.dispatchEvent(new Event('change', { bubbles: true }));
        }
        await new Promise(r => setTimeout(r, 450));
        await new Promise(r => setTimeout(r, 450));
        
        // 2.5 Plot Number
        showStatusToast("Entering Plot Number details...");
        const { plot1, plot2, plot3 } = splitPlotNumber(prop.plot_no);
        const p1Input = document.getElementById('plotNo1');
        const p2Input = document.getElementById('plotNo2');
        const p3Input = document.getElementById('plotNo3');
        if (p1Input) p1Input.value = plot1;
        if (p2Input) p2Input.value = plot2;
        if (p3Input) p3Input.value = plot3;
        
        // 2.6 Colony/Village (Property Address)
        const otherColonySelect = document.getElementById('othercolonyvillage');
        if (otherColonySelect && bestOption) {
            await setSelectValueByText(otherColonySelect, bestOption.text);
        }
        
        // 2.7 City / District
        const citySelect = document.getElementById('city');
        await setSelectValueByText(citySelect, "JAIPUR");
        
        // 2.8 Road Width Input
        const rwInput = document.getElementById('txtRoadWidth') || document.querySelector('input[name*="roadwidth" i]') || document.querySelector('input[id*="roadwidth" i]');
        if (rwInput) {
            rwInput.value = roadWidth;
            rwInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        // 2.9 Property Area (Gaj/SqYards to SqMtrs)
        showStatusToast("Setting Property Area...");
        const plotAreaInput = document.getElementById('txtPlotArea');
        if (plotAreaInput) {
            const rawArea = parseFloat(prop.area || 0);
            // Check if conversion is needed (default is Sq. Yards)
            const convertedArea = rawArea * 0.836127;
            plotAreaInput.value = convertedArea.toFixed(2);
            plotAreaInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        // 2.10 Coordinates (Lat/Long)
        const latInput = document.getElementById('latitude');
        const lngInput = document.getElementById('longitude');
        if (latInput) latInput.value = prop.latitude || "0";
        if (lngInput) lngInput.value = prop.longitude || "0";
        
        // 2.11 Boundaries
        const eastInput = document.getElementById('east');
        const westInput = document.getElementById('west');
        const northInput = document.getElementById('north');
        const southInput = document.getElementById('south');
        if (eastInput) eastInput.value = prop.east || "";
        if (westInput) westInput.value = prop.west || "";
        if (northInput) northInput.value = prop.north || "";
        if (southInput) southInput.value = prop.south || "";
        
        // 2.12 Intermediate Documents: No
        const intermediateRadio = document.getElementById('radiointermediateNo');
        if (intermediateRadio) {
            intermediateRadio.checked = true;
            intermediateRadio.click();
            intermediateRadio.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        await new Promise(r => setTimeout(r, 600));
        
        // 2.13 Click Save
        showStatusToast("Saving property address...");
        const saveAddressBtn = document.getElementById('btnsaveproperty');
        if (saveAddressBtn) {
            saveAddressBtn.click();
            sendResponse({ success: true, message: 'Property address successfully saved!' });
        } else {
            sendResponse({ success: false, error: 'Could not find the Save button (btnsaveproperty).' });
        }
    } catch (e) {
        sendResponse({ success: false, error: e.message });
    }
}

// Set Datepicker value via page jQuery context injection
function setDatePickerValue(inputEl, value) {
    if (!inputEl) return;
    if (!inputEl.id) {
        inputEl.id = 'date_' + Math.random().toString(36).substring(2, 9);
    }
    inputEl.removeAttribute('readonly');
    setInputValue(inputEl, value);
    inputEl.setAttribute('readonly', 'readonly');
    
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
                        } catch(e) {}
                    }
                    $(el).attr('readonly', 'readonly');
                }
            })();
        `;
        (document.head || document.documentElement).appendChild(script);
        script.remove();
    } catch (e) {
        console.error("[SD Autofill] Error injecting datepicker script:", e);
    }
}

function setInputValue(inputEl, value) {
    if (!inputEl) return false;
    inputEl.value = value;
    inputEl.dispatchEvent(new Event('input', { bubbles: true }));
    inputEl.dispatchEvent(new Event('change', { bubbles: true }));
    inputEl.dispatchEvent(new Event('blur', { bubbles: true }));
    return true;
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

// 3. Calculate Stamp Duty Automation
async function autofillCalculateDuty(data, sendResponse) {
    try {
        const url = window.location.href.toLowerCase();
        
        if (url.includes('/propertyvaluation/propertydetail')) {
            // First look for the "Add Property" button if details are being filled
            const addPropertyBtn = Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"]')).find(b => {
                const txt = b.textContent.toUpperCase();
                return txt.includes('ADD PROPERTY') || txt.includes('प्रॉपर्टी जोड़ें') || (b.value && b.value.toUpperCase().includes('ADD PROPERTY'));
            });
            
            if (addPropertyBtn && (addPropertyBtn.offsetWidth > 0 || addPropertyBtn.offsetHeight > 0)) {
                showStatusToast("Saving Property Details (Clicking Add Property)...");
                addPropertyBtn.click();
                sendResponse({ success: true, message: 'Clicked Add Property!' });
                return;
            }

            // Otherwise, look for the "Calculate Stamp Duty" button to proceed
            showStatusToast("Navigating to Calculate Stamp Duty...");
            const calcBtn = document.querySelector('button[formaction*="/PropertyValuation/CalculateDuty" i]') || 
                            document.querySelector('button[formaction*="calculateduty" i]') ||
                            Array.from(document.querySelectorAll('button, a')).find(b => {
                                const txt = b.textContent.toUpperCase();
                                return txt.includes('CALCULATE DUTY') || txt.includes('ड्यूटी की गणना करें') || txt.includes('CALCULATE STAMP DUTY');
                            });
                            
            if (calcBtn) {
                calcBtn.click();
                sendResponse({ success: true, message: 'Clicked Calculate Duty!' });
            } else {
                sendResponse({ success: false, error: 'Could not find Add Property or Calculate Duty button.' });
            }
            return;
        }
        
        if (url.includes('/propertyvaluation/calculateduty')) {
            const dateInput = document.getElementById('execution_date');
            const faceValueInput = document.getElementById('face_value');
            
            if (dateInput && faceValueInput) {
                let execDate = data.execution_date;
                if (!execDate) {
                    const today = new Date();
                    const dd = String(today.getDate()).padStart(2, '0');
                    const mm = String(today.getMonth() + 1).padStart(2, '0');
                    const yyyy = today.getFullYear();
                    execDate = `${dd}-${mm}-${yyyy}`;
                }
                
                const valAmount = (data.amount || data.face_value || 0).toString();
                showStatusToast(`Setting Date: ${execDate} & Face Value: ${valAmount}...`);
                setDatePickerValue(dateInput, execDate);
                setInputValue(faceValueInput, valAmount);
                
                await new Promise(r => setTimeout(r, 600));
                
                showStatusToast("Submitting Stamp Duty (Clicking Calculate & Save)...");
                const calcSaveBtn = document.querySelector('input[type="submit"][value="Calculate & Save"]') || 
                                    document.querySelector('button[value="Calculate & Save"]') ||
                                    triggerButtonByText("Calculate & Save") || 
                                    triggerButtonByText("गणना और सहेजें");
                
                if (calcSaveBtn) {
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
                        }, 8000);
                    });
                } else {
                    sendResponse({ success: false, error: 'Could not find Calculate & Save button.' });
                }
            } else {
                sendResponse({ success: false, error: 'Date or Face Value inputs not found.' });
            }
        }
    } catch (e) {
        sendResponse({ success: false, error: e.message });
    }
}

// 4. Quotation Scraping & Persistent Backend Storage
function scrapeValuationQuote() {
    let stampDuty = "";
    let regFee = "";
    let cessSurcharge = "";
    let totalFee = "";
    
    // Scan all cells in the document
    const cells = Array.from(document.querySelectorAll('td, th, label, span, div'));
    
    function extractValueNextTo(keywordText) {
        const index = cells.findIndex(c => c.textContent.replace(/\s+/g, ' ').trim().toUpperCase().includes(keywordText.toUpperCase()));
        if (index !== -1) {
            const cell = cells[index];
            if (cell.tagName === 'TD' || cell.tagName === 'TH') {
                const row = cell.closest('tr');
                if (row) {
                    const rowCells = Array.from(row.cells);
                    const cellIndex = rowCells.indexOf(cell);
                    if (cellIndex !== -1 && cellIndex + 1 < rowCells.length) {
                        return rowCells[cellIndex + 1].textContent.trim();
                    }
                }
            }
            let next = cell.nextElementSibling;
            if (next) return next.textContent.trim();
            
            const parent = cell.parentElement;
            if (parent && parent.nextElementSibling) {
                return parent.nextElementSibling.textContent.trim();
            }
        }
        return "";
    }
    
    stampDuty = extractValueNextTo("STAMP DUTY") || extractValueNextTo("स्टाम्प शुल्क") || extractValueNextTo("स्टाम्प ड्यूटी");
    regFee = extractValueNextTo("REGISTRATION FEE") || extractValueNextTo("पंजीयन शुल्क") || extractValueNextTo("पंजीकरण शुल्क");
    cessSurcharge = extractValueNextTo("SURCHARGE") || extractValueNextTo("सरचार्ज") || extractValueNextTo("CESS");
    totalFee = extractValueNextTo("TOTAL") || extractValueNextTo("कुल");
    
    // Grid search fallback
    if (!totalFee) {
        const rows = Array.from(document.querySelectorAll('tr'));
        for (let row of rows) {
            const txt = row.textContent.toUpperCase();
            const cellsList = Array.from(row.cells).map(c => c.textContent.trim());
            if (txt.includes("TOTAL") || txt.includes("कुल")) {
                totalFee = cellsList[cellsList.length - 1] || "";
            }
            if (txt.includes("STAMP") || txt.includes("स्टाम्प")) {
                stampDuty = cellsList[cellsList.length - 1] || "";
            }
            if (txt.includes("REGISTRATION") || txt.includes("पंजीयन")) {
                regFee = cellsList[cellsList.length - 1] || "";
            }
            if (txt.includes("SURCHARGE") || txt.includes("सरचार्ज")) {
                cessSurcharge = cellsList[cellsList.length - 1] || "";
            }
        }
    }
    
    return {
        stamp_duty: stampDuty,
        registration_fee: regFee,
        cess_surcharge: cessSurcharge,
        total_fee: totalFee
    };
}

async function saveQuoteToBackend(caseId, quote) {
    try {
        showStatusToast("Saving valuation quote to backend...");
        const response = await fetch(`http://localhost:5000/api/case/${caseId}/save_valuation_quote`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(quote)
        });
        const res = await response.json();
        if (res.success) {
            showStatusToast("Valuation quote saved successfully!", false);
        } else {
            console.error("[SD Autofill] Failed to save quote:", res.error);
        }
    } catch (e) {
        console.error("[SD Autofill] Error saving quote:", e);
    }
}

// 5. Automated state loading machine (on DOM load)
// 5. Automated state loading machine (on DOM load)
async function checkAutomatedStateOnLoad() {
    if (!chrome || !chrome.storage || !chrome.storage.local) return;
    
    chrome.storage.local.get(['oneClickRunning', 'oneClickData', 'stampDutyCalculated', 'publicLookupRunning'], async (res) => {
        const url = window.location.href.toLowerCase();
        
        // A. Handle public SRO and DLC rate lookup workflow
        if (res.publicLookupRunning && res.oneClickData) {
            if (url.includes('/#/public/home')) {
                showStatusToast("Clicking DLC Profile...");
                const dlcProfileBtn = document.querySelector('div[name="dlcprofile"]') || 
                                      document.querySelector('.service-sml-cards[name="dlcprofile"]') ||
                                      Array.from(document.querySelectorAll('div, a, button')).find(el => el.textContent.trim().includes('DLC Profile'));
                
                if (dlcProfileBtn) {
                    dlcProfileBtn.click();
                } else {
                    showStatusToast("Could not find DLC Profile button. Resetting...", false);
                    chrome.storage.local.set({ publicLookupRunning: false });
                }
                return;
            }
            
            if (url.includes('/#/public/dlcrate')) {
                showStatusToast("Selecting Jaipur District (Urban)...");
                const rows = Array.from(document.querySelectorAll('div.row'));
                const jaipurRow = rows.find(r => r.textContent.toUpperCase().includes('JAIPUR') || r.textContent.includes('21.'));
                
                if (jaipurRow) {
                    const urbanBtn = jaipurRow.querySelector('.urban-button');
                    if (urbanBtn) {
                        urbanBtn.click();
                    } else {
                        showStatusToast("Could not find Urban button for Jaipur.", false);
                        chrome.storage.local.set({ publicLookupRunning: false });
                    }
                } else {
                    showStatusToast("Could not find Jaipur row.", false);
                    chrome.storage.local.set({ publicLookupRunning: false });
                }
                return;
            }
            
            if (url.includes('/#/public/finddlcrate') || url.includes('/#/public/fincdlcrate')) {
                setTimeout(async () => {
                    await runPublicDlcLookupAutomated(res.oneClickData);
                }, 1000);
                return;
            }
        }

        // B. Handle normal logged-in document feeding automation
        if (!res.oneClickRunning || !res.oneClickData) return;
        
        // Scraping and pausing stage
        if (url.includes('/propertyvaluation/propertydetail') && res.stampDutyCalculated) {
            showStatusToast("Scraping calculated valuation quote...");
            const quote = scrapeValuationQuote();
            await saveQuoteToBackend(res.oneClickData.case_id, quote);
            
            // Clear automation states
            chrome.storage.local.remove(['stampDutyCalculated']);
            chrome.storage.local.set({ oneClickRunning: false });
            
            showStatusToast("⚡ One-click property valuation complete!", false);
            alert(`Valuation Complete!\n\nStamp Duty: ${quote.stamp_duty}\nRegistration Fee: ${quote.registration_fee}\nSurcharges: ${quote.cess_surcharge}\nTotal Fee: ${quote.total_fee}`);
            return;
        }
        
        // Next step transition loop
        if (url.includes('/citizen/dashboard')) {
            // Wait for user to trigger or click district
        } else if (url.includes('/propertyvaluation')) {
            // Trigger automation step on page load
            setTimeout(() => {
                oneClickAutofill(res.oneClickData, () => {});
            }, 800);
        }
    });
}

// 6. Public un-logged-in DLC Lookup workflow
async function runPublicDlcLookup(data, sendResponse) {
    try {
        const url = window.location.href.toLowerCase();
        
        // Phase 1: Home page
        if (url.includes('/#/public/home')) {
            showStatusToast("Clicking DLC Profile...");
            const dlcProfileBtn = document.querySelector('div[name="dlcprofile"]') || 
                                  document.querySelector('.service-sml-cards[name="dlcprofile"]') ||
                                  Array.from(document.querySelectorAll('div, a, button')).find(el => el.textContent.trim().includes('DLC Profile'));
            
            if (dlcProfileBtn) {
                dlcProfileBtn.click();
                sendResponse({ success: true, message: 'Navigated to public DLC rate page!' });
            } else {
                sendResponse({ success: false, error: 'Could not find DLC Profile button.' });
            }
            return;
        }
        
        // Phase 2: District select page
        if (url.includes('/#/public/dlcrate')) {
            showStatusToast("Selecting Jaipur District (Urban)...");
            const rows = Array.from(document.querySelectorAll('div.row'));
            const jaipurRow = rows.find(r => r.textContent.toUpperCase().includes('JAIPUR') || r.textContent.includes('21.'));
            
            if (jaipurRow) {
                const urbanBtn = jaipurRow.querySelector('.urban-button');
                if (urbanBtn) {
                    urbanBtn.click();
                    sendResponse({ success: true, message: 'Selected Jaipur (Urban)!' });
                } else {
                    sendResponse({ success: false, error: 'Could not find Urban button for Jaipur.' });
                }
            } else {
                sendResponse({ success: false, error: 'Could not find Jaipur row.' });
            }
            return;
        }
        
        // Phase 3: Colony rate page
        if (url.includes('/#/public/finddlcrate') || url.includes('/#/public/fincdlcrate')) {
            const sroVal = data.sro || 'JAIPUR-VII';
            const prop = data.property || {};
            const colonyName = prop.colony || '';
            
            // 1. Select the SRO pill
            showStatusToast(`Selecting SRO: ${sroVal}...`);
            const sroBtn = Array.from(document.querySelectorAll('button, a.btn, span')).find(el => {
                const text = el.textContent.trim().toUpperCase();
                return text === sroVal.toUpperCase() || text === sroVal.replace('-', ' ').toUpperCase();
            });
            
            if (sroBtn) {
                sroBtn.click();
                await new Promise(r => setTimeout(r, 600)); // wait for SRO selection to load colony list
            } else {
                console.warn(`[SD Autofill] Could not find SRO pill button for "${sroVal}". Attempting default options lookup...`);
            }
            
            // 2. Select the colony dropdown
            const ddlColony = document.getElementById('ddlColony');
            if (!ddlColony) {
                sendResponse({ success: false, error: 'Could not find ddlColony select box on page.' });
                return;
            }
            
            // We search using the hierarchical strategy (specific to general)
            const cleanTarget = cleanStringForColony(colonyName);
            let bestOption = null;
            
            // Step A: Search fuzzy similarity
            let candidates = [];
            for (let opt of ddlColony.options) {
                if (!opt.value) continue;
                const cleanOpt = cleanStringForColony(opt.text);
                const score = stringSimilarity(cleanTarget, cleanOpt);
                if (score >= 0.85) {
                    candidates.push({ option: opt, score: score });
                }
            }
            
            // Sort by score
            candidates.sort((a, b) => b.score - a.score);
            if (candidates.length > 0) {
                bestOption = candidates[0].option;
            }
            
            // Step B: Fallback to partial substring match
            if (!bestOption) {
                const words = colonyName.split(/\s+/).filter(w => w.length > 2);
                for (let word of words) {
                    const cleanWord = cleanStringForColony(word);
                    bestOption = Array.from(ddlColony.options).find(opt => cleanStringForColony(opt.text).includes(cleanWord));
                    if (bestOption) break;
                }
            }
            
            // Step C: Fallback to JDA
            if (!bestOption) {
                bestOption = Array.from(ddlColony.options).find(opt => {
                    const txt = opt.text.toLowerCase();
                    return txt.includes("jda") || txt.includes("जे.डी.ए");
                });
            }
            
            if (!bestOption && ddlColony.options.length > 1) {
                bestOption = ddlColony.options[1]; // Fallback to first real colony
            }
            
            if (!bestOption) {
                sendResponse({ success: false, error: 'No colonies found or matching your address.' });
                return;
            }
            
            showStatusToast(`Selecting Colony: ${bestOption.text}...`);
            ddlColony.value = bestOption.value;
            ddlColony.dispatchEvent(new Event('change', { bubbles: true }));
            
            // Update Select2 UI
            const select2Container = ddlColony.nextElementSibling;
            if (select2Container && select2Container.classList.contains('select2-container')) {
                const renderSpan = select2Container.querySelector('.select2-selection__rendered');
                if (renderSpan) {
                    renderSpan.textContent = bestOption.text;
                    renderSpan.title = bestOption.text;
                }
            }
            
            // Wait for table to load
            await new Promise(r => setTimeout(r, 1200));
            
            // 3. Parse the SRO rate table
            const table = document.querySelector('table');
            if (!table) {
                sendResponse({ success: false, error: 'Could not find the SRO/Colony rate table after selection.' });
                return;
            }
            
            // Search rows
            const rows = Array.from(table.querySelectorAll('tr'));
            const matchingRow = rows.find(row => {
                const text = row.textContent.toUpperCase();
                return text.includes(bestOption.text.toUpperCase());
            }) || rows[1]; // Fallback to first data row
            
            if (!matchingRow) {
                sendResponse({ success: false, error: 'Could not find the matching colony row in table.' });
                return;
            }
            
            const cells = Array.from(matchingRow.querySelectorAll('td'));
            if (cells.length < 8) {
                sendResponse({ success: false, error: 'Rates table format has changed or is incomplete.' });
                return;
            }
            
            // Extracted values
            const trueSro = cells[1]?.textContent?.trim() || sroVal;
            const zoneName = cells[2]?.textContent?.trim() || '';
            const matchedColName = cells[3]?.textContent?.trim() || bestOption.text;
            
            // Helper to parse exterior limits array
            function parseExteriorRates(text) {
                if (!text || text.trim() === '-') return [];
                const rates = [];
                // Format: "13750 (40 ft)\n15130 (41-60 ft)"
                const lines = text.split('\n');
                for (const line of lines) {
                    const match = line.match(/([0-9]+)\s*\(([^)]+)\)/);
                    if (match) {
                        const rate = parseFloat(match[1]) || 0;
                        const desc = match[2];
                        let limit = 99;
                        const limitMatch = desc.match(/([0-9]+)\s*ft/);
                        if (limitMatch) {
                            limit = parseInt(limitMatch[1]) || 99;
                        }
                        rates.push({ rate, limit, description: desc });
                    } else {
                        const num = parseFloat(line.replace(/[^0-9]/g, ''));
                        if (num) rates.push({ rate: num, limit: 99, description: 'Default' });
                    }
                }
                return rates;
            }
            
            const commercialExtText = cells[4]?.innerText || cells[4]?.textContent || '';
            const commercialIntText = cells[5]?.textContent || '0';
            const residentialExtText = cells[6]?.innerText || cells[6]?.textContent || '';
            const residentialIntText = cells[7]?.textContent || '0';
            
            const publicDlcProfile = {
                sro: trueSro,
                zone: zoneName,
                colony: matchedColName,
                residential: {
                    interior: parseFloat(residentialIntText.replace(/[^0-9.]/g, '')) || 0,
                    exterior: parseExteriorRates(residentialExtText)
                },
                commercial: {
                    interior: parseFloat(commercialIntText.replace(/[^0-9.]/g, '')) || 0,
                    exterior: parseExteriorRates(commercialExtText)
                }
            };
            
            showStatusToast("Public SRO & DLC lookup completed!", false);
            sendResponse({ success: true, message: `Successfully matched SRO: ${trueSro}`, data: publicDlcProfile });
            return;
        }
        
        sendResponse({ success: false, error: 'Please switch to the e-Panjiyan Public Home or DLC Rate page.' });
    } catch (e) {
        sendResponse({ success: false, error: e.message });
    }
}

async function runPublicDlcLookupAutomated(caseData) {
    try {
        const sroVal = caseData.sro || 'JAIPUR-VII';
        const prop = caseData.properties?.[0] || {};
        const colonyName = prop.address?.colony || '';
        
        // 1. Select the SRO pill
        showStatusToast(`Selecting SRO: ${sroVal}...`);
        const sroBtn = Array.from(document.querySelectorAll('button, a.btn, span')).find(el => {
            const text = el.textContent.trim().toUpperCase();
            return text === sroVal.toUpperCase() || text === sroVal.replace('-', ' ').toUpperCase();
        });
        
        if (sroBtn) {
            sroBtn.click();
            await new Promise(r => setTimeout(r, 800)); // wait for SRO selection to load colony list
        }
        
        // 2. Select the colony dropdown
        const ddlColony = document.getElementById('ddlColony');
        if (!ddlColony) {
            showStatusToast("Could not find colony dropdown.", false);
            chrome.storage.local.set({ publicLookupRunning: false });
            return;
        }
        
        const cleanTarget = cleanStringForColony(colonyName);
        let bestOption = null;
        
        // Step A: Search fuzzy similarity
        let candidates = [];
        for (let opt of ddlColony.options) {
            if (!opt.value) continue;
            const cleanOpt = cleanStringForColony(opt.text);
            const score = stringSimilarity(cleanTarget, cleanOpt);
            if (score >= 0.85) {
                candidates.push({ option: opt, score: score });
            }
        }
        
        candidates.sort((a, b) => b.score - a.score);
        if (candidates.length > 0) {
            bestOption = candidates[0].option;
        }
        
        // Step B: Fallback to partial substring match
        if (!bestOption) {
            const words = colonyName.split(/\s+/).filter(w => w.length > 2);
            for (let word of words) {
                const cleanWord = cleanStringForColony(word);
                bestOption = Array.from(ddlColony.options).find(opt => cleanStringForColony(opt.text).includes(cleanWord));
                if (bestOption) break;
            }
        }
        
        // Step C: Fallback to JDA
        if (!bestOption) {
            bestOption = Array.from(ddlColony.options).find(opt => {
                const txt = opt.text.toLowerCase();
                return txt.includes("jda") || txt.includes("जे.डी.ए");
            });
        }
        
        if (!bestOption && ddlColony.options.length > 1) {
            bestOption = ddlColony.options[1];
        }
        
        if (!bestOption) {
            showStatusToast("No matching colony found.", false);
            chrome.storage.local.set({ publicLookupRunning: false });
            return;
        }
        
        showStatusToast(`Selecting Colony: ${bestOption.text}...`);
        ddlColony.value = bestOption.value;
        ddlColony.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Update Select2 UI
        const select2Container = ddlColony.nextElementSibling;
        if (select2Container && select2Container.classList.contains('select2-container')) {
            const renderSpan = select2Container.querySelector('.select2-selection__rendered');
            if (renderSpan) {
                renderSpan.textContent = bestOption.text;
                renderSpan.title = bestOption.text;
            }
        }
        
        // Wait for table to load
        await new Promise(r => setTimeout(r, 1500));
        
        // 3. Parse the SRO rate table
        const table = document.querySelector('table');
        if (!table) {
            showStatusToast("Could not find rates table.", false);
            chrome.storage.local.set({ publicLookupRunning: false });
            return;
        }
        
        const rows = Array.from(table.querySelectorAll('tr'));
        const matchingRow = rows.find(row => {
            const text = row.textContent.toUpperCase();
            return text.includes(bestOption.text.toUpperCase());
        }) || rows[1];
        
        if (!matchingRow) {
            showStatusToast("No matching row in table.", false);
            chrome.storage.local.set({ publicLookupRunning: false });
            return;
        }
        
        const cells = Array.from(matchingRow.querySelectorAll('td'));
        if (cells.length < 8) {
            showStatusToast("Rates table format incomplete.", false);
            chrome.storage.local.set({ publicLookupRunning: false });
            return;
        }
        
        const trueSro = cells[1]?.textContent?.trim() || sroVal;
        const zoneName = cells[2]?.textContent?.trim() || '';
        const matchedColName = cells[3]?.textContent?.trim() || bestOption.text;
        
        function parseExteriorRates(text) {
            if (!text || text.trim() === '-') return [];
            const rates = [];
            const lines = text.split('\n');
            for (const line of lines) {
                const match = line.match(/([0-9]+)\s*\(([^)]+)\)/);
                if (match) {
                    const rate = parseFloat(match[1]) || 0;
                    const desc = match[2];
                    let limit = 99;
                    const limitMatch = desc.match(/([0-9]+)\s*ft/);
                    if (limitMatch) {
                        limit = parseInt(limitMatch[1]) || 99;
                    }
                    rates.push({ rate, limit, description: desc });
                } else {
                    const num = parseFloat(line.replace(/[^0-9]/g, ''));
                    if (num) rates.push({ rate: num, limit: 99, description: 'Default' });
                }
            }
            return rates;
        }
        
        const commercialExtText = cells[4]?.innerText || cells[4]?.textContent || '';
        const commercialIntText = cells[5]?.textContent || '0';
        const residentialExtText = cells[6]?.innerText || cells[6]?.textContent || '';
        const residentialIntText = cells[7]?.textContent || '0';
        
        const publicDlcProfile = {
            sro: trueSro,
            zone: zoneName,
            colony: matchedColName,
            residential: {
                interior: parseFloat(residentialIntText.replace(/[^0-9.]/g, '')) || 0,
                exterior: parseExteriorRates(residentialExtText)
            },
            commercial: {
                interior: parseFloat(commercialIntText.replace(/[^0-9.]/g, '')) || 0,
                exterior: parseExteriorRates(commercialExtText)
            }
        };
        
        showStatusToast("DLC Rate found! Saving to backend...");
        
        const resp = await fetch(`http://localhost:5000/api/case/${caseData.case_id}/public_dlc`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ public_dlc_profile: publicDlcProfile })
        });
        const respJson = await resp.json();
        
        if (respJson.success) {
            showStatusToast("⚡ True SRO & DLC rate lookup complete!", false);
            chrome.storage.local.set({ publicLookupRunning: false });
            alert(`SRO & DLC rate lookup complete!\n\nTrue SRO: ${trueSro}\nZone: ${zoneName}\nColony: ${matchedColName}\nResidential Interior Rate: Rs ${publicDlcProfile.residential.interior}`);
        } else {
            showStatusToast("Failed to save DLC details to server.", false);
            chrome.storage.local.set({ publicLookupRunning: false });
        }
    } catch (e) {
        showStatusToast("Error: " + e.message, false);
        chrome.storage.local.set({ publicLookupRunning: false });
    }
}

// Start page load listener
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(checkAutomatedStateOnLoad, 1000));
} else {
    setTimeout(checkAutomatedStateOnLoad, 1000);
}



