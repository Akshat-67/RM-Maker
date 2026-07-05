const API_BASE = 'http://localhost:5000/api';
let activeCaseData = null;

// The default firm mobile number (can be customized)
const FIRM_MOBILE = "9799967384"; 

document.addEventListener('DOMContentLoaded', async () => {
    console.log("[popup.js] DOMContentLoaded triggered for SD Autofill.");
    const caseSelect = document.getElementById('caseSelect');
    const statusBadge = document.getElementById('statusBadge');
    
    async function loadCaseData(caseId) {
        console.log("[popup.js] loadCaseData called with caseId:", caseId);
        if (!caseId) {
            console.log("[popup.js] Empty caseId, disabling buttons.");
            disableActionButtons();
            activeCaseData = null;
            return;
        }
        
        showMsg('Loading case details...', 'success');
        try {
            const url = `${API_BASE}/case/${caseId}/epanjiyan_data`;
            console.log("[popup.js] Fetching case details from:", url);
            const resp = await fetch(url);
            console.log("[popup.js] Fetch response status:", resp.status);
            if (!resp.ok) throw new Error('Failed to load case data');
            activeCaseData = await resp.json();
            console.log("[popup.js] Loaded activeCaseData successfully:", activeCaseData);
            if (chrome && chrome.storage && chrome.storage.local) {
                chrome.storage.local.set({ activeCaseData });
            }
            
            showMsg(`Loaded: ${activeCaseData.executants?.[0]?.name_en || 'Unnamed Case'}`, 'success');
            enableActionButtons();
        } catch (err) {
            console.error("[popup.js] Error in loadCaseData:", err);
            showMsg('Error loading case details: ' + err.message, 'error');
            disableActionButtons();
            activeCaseData = null;
        }
    }
    
    try {
        console.log("[popup.js] Fetching recent cases...");
        const response = await fetch(`${API_BASE}/cases/recent`);
        console.log("[popup.js] Fetch recent response status:", response.status);
        if (!response.ok) throw new Error('Failed to fetch cases');
        const cases = await response.json();
        console.log("[popup.js] Retrieved cases list:", cases);
        
        caseSelect.innerHTML = '<option value="">-- Select Case --</option>';
        if (cases.length === 0) {
            caseSelect.innerHTML = '<option value="">No recent cases found</option>';
            return;
        }
        
        cases.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.case_id;
            opt.textContent = `${c.name} [${c.doc_type}]`;
            caseSelect.appendChild(opt);
        });
        
        statusBadge.textContent = 'ONLINE';
        statusBadge.style.color = '#10b981';
        statusBadge.style.backgroundColor = 'rgba(16, 185, 129, 0.15)';
        statusBadge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
        
        // Auto-select and auto-load the first case
        if (cases.length > 0) {
            console.log("[popup.js] Auto-selecting first case:", cases[0].case_id);
            caseSelect.value = cases[0].case_id;
            loadCaseData(cases[0].case_id);
        }
        
    } catch (e) {
        console.error("[popup.js] Error fetching recent cases:", e);
        showMsg('Could not connect to local RM-Maker app (make sure it is running on port 5000)', 'error');
        caseSelect.innerHTML = '<option value="">Connection error</option>';
    }
    
    // Listen for dropdown changes
    caseSelect.addEventListener('change', (e) => {
        console.log("[popup.js] Dropdown change event, value:", e.target.value);
        loadCaseData(e.target.value);
    });
    
    // Set up button event handlers
    if (chrome && chrome.storage && chrome.storage.local) {
        chrome.storage.local.get(['oneClickRunning'], (res) => {
            const btn = document.getElementById('btnOneClickAutofill');
            if (res.oneClickRunning) {
                btn.innerHTML = '<span>⚡ STOP AUTOMATION</span>';
                btn.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
            }
        });
    }

    document.getElementById('btnOneClickAutofill').addEventListener('click', async () => {
        try {
            if (!activeCaseData) {
                showMsg('No case loaded. Please select a case first.', 'error');
                return;
            }

            let isRunning = false;
            if (chrome && chrome.storage && chrome.storage.local) {
                const res = await new Promise(r => chrome.storage.local.get(['oneClickRunning'], r));
                isRunning = !!res.oneClickRunning;
            }

            const btn = document.getElementById('btnOneClickAutofill');
            if (isRunning) {
                if (chrome && chrome.storage && chrome.storage.local) {
                    chrome.storage.local.set({ oneClickRunning: false });
                }
                btn.innerHTML = '<span>⚡ ONE-CLICK AUTOFILL</span>';
                btn.style.background = 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)';
                showMsg('Automation stopped.', 'success');
            } else {
                const prop = activeCaseData.properties?.[0] || {};
                const propAddress = prop.address || {};
                const oneClickData = {
                    case_id: activeCaseData.case_id,
                    sro: activeCaseData.sro,
                    tehsil: activeCaseData.tehsil,
                    amount: activeCaseData.amount || activeCaseData.face_value,
                    gender: activeCaseData.executants?.[0]?.gender?.toLowerCase() || 'male',
                    caste: activeCaseData.executants?.[0]?.caste || 'General',
                    isBPL: activeCaseData.executants?.[0]?.is_bpl || false,
                    isJoint: activeCaseData.executants?.length > 1,
                    property: {
                        colony: propAddress.colony || '',
                        plot_no: propAddress.house_no || '',
                        area: prop.area || 0,
                        road_width: prop.road_width || 30,
                        latitude: prop.latitude || '0',
                        longitude: prop.longitude || '0',
                        east: prop.east || '',
                        west: prop.west || '',
                        north: prop.north || '',
                        south: prop.south || ''
                    }
                };

                if (chrome && chrome.storage && chrome.storage.local) {
                    chrome.storage.local.set({ 
                        oneClickRunning: true,
                        oneClickData: oneClickData
                    });
                }
                btn.innerHTML = '<span>⚡ STOP AUTOMATION</span>';
                btn.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
                
                sendTabMessage('one_click_autofill', oneClickData);
            }
        } catch (e) {
            console.error('[RM-Maker Popup] One-click error:', e);
            showMsg('Error: ' + e.message, 'error');
        }
    });

    document.getElementById('btnAutofillDistrict').addEventListener('click', () => {
        sendTabMessage('autofill_district', {});
    });
    
    document.getElementById('btnAutofillDetails').addEventListener('click', () => {
        sendTabMessage('autofill_details', {
            sro: activeCaseData.sro,
            tehsil: activeCaseData.tehsil,
            gender: activeCaseData.executants?.[0]?.gender?.toLowerCase() || 'male',
            caste: activeCaseData.executants?.[0]?.caste || 'General',
            isBPL: activeCaseData.executants?.[0]?.is_bpl || false,
            isJoint: activeCaseData.executants?.length > 1
        });
    });
    
    document.getElementById('btnAutofillAddress').addEventListener('click', () => {
        const prop = activeCaseData.properties?.[0] || {};
        const propAddress = prop.address || {};
        sendTabMessage('autofill_address', {
            property: {
                colony: propAddress.colony || '',
                plot_no: propAddress.house_no || '',
                area: prop.area || 0,
                road_width: prop.road_width || 30,
                latitude: prop.latitude || '0',
                longitude: prop.longitude || '0',
                east: prop.east || '',
                west: prop.west || '',
                north: prop.north || '',
                south: prop.south || ''
            }
        });
    });
    
    document.getElementById('btnCalculateDuty').addEventListener('click', () => {
        sendTabMessage('autofill_calculate_duty', {
            amount: activeCaseData.amount || activeCaseData.face_value
        });
    });

    document.getElementById('btnPublicDlcLookup').addEventListener('click', () => {
        if (!activeCaseData) return;
        const prop = activeCaseData.properties?.[0] || {};
        const propAddress = prop.address || {};
        
        showMsg('Starting public SRO & DLC lookup...', 'success');
        
        const caseDataPayload = {
            case_id: activeCaseData.case_id,
            sro: activeCaseData.sro || 'JAIPUR-VII',
            properties: activeCaseData.properties || []
        };
        
        chrome.storage.local.set({ 
            publicLookupRunning: true, 
            oneClickData: caseDataPayload 
        }, () => {
            sendTabMessage('public_dlc_lookup_start', {}, (response) => {
                if (response && response.success) {
                    showMsg('Public SRO & DLC lookup initiated...', 'success');
                } else {
                    showMsg('Verification initiated on page.', 'success');
                }
            });
        });
    });
});

function enableActionButtons() {
    document.querySelectorAll('.actions-list button').forEach(btn => btn.removeAttribute('disabled'));
}

function disableActionButtons() {
    document.querySelectorAll('.actions-list button').forEach(btn => btn.setAttribute('disabled', 'true'));
}

function showMsg(text, type) {
    const msg = document.getElementById('statusMsg');
    msg.textContent = text;
    msg.style.display = 'block';
    msg.className = `msg msg-${type}`;
}

async function sendTabMessage(action, data, callback) {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab) {
            showMsg('No active browser tab found.', 'error');
            return;
        }
        
        if (!tab.url || !tab.url.includes('rajasthan.gov.in')) {
            showMsg('Please switch to the e-Panjiyan tab first!', 'error');
            return;
        }
        
        function deliverMessage() {
            chrome.tabs.sendMessage(tab.id, { action, data }, (response) => {
                const err = chrome.runtime.lastError;
                if (err) {
                    const errMsg = err.message || '';
                    if (errMsg.includes('cache') || errMsg.includes('Receiving end does not exist') || errMsg.includes('connection')) {
                        console.log('[popup.js] Ignored expected connection close error due to page navigation:', errMsg);
                        // Still trigger callback if needed, or simply log it as harmless
                        if (callback) callback({ success: true, message: 'Navigation triggered.' });
                        return;
                    }
                    console.error('[popup.js] sendMessage error:', errMsg);
                    showMsg('Autofill failed: Content script could not be loaded.', 'error');
                    return;
                }
                if (callback) {
                    callback(response);
                } else {
                    if (response && response.success) {
                        showMsg(response.message || 'Action completed!', 'success');
                    } else {
                        showMsg((response && response.error) || 'Action failed.', 'error');
                    }
                }
            });
        }
        
        // Ping the content script first to verify if it is loaded
        chrome.tabs.sendMessage(tab.id, { action: 'ping' }, (response) => {
            const err = chrome.runtime.lastError;
            if (err) {
                console.log('[popup.js] Content script not responding. Programmatically injecting content.js...');
                chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    files: ['content.js']
                }, () => {
                    const injectErr = chrome.runtime.lastError;
                    if (injectErr) {
                        console.error('[popup.js] Script injection failed:', injectErr.message);
                        showMsg('Autofill failed: Content script not loaded. Reload e-Panjiyan page.', 'error');
                    } else {
                        console.log('[popup.js] content.js successfully injected! Retrying message...');
                        setTimeout(deliverMessage, 250);
                    }
                });
            } else {
                deliverMessage();
            }
        });
    } catch (e) {
        showMsg('Error sending message: ' + e.message, 'error');
    }
}
