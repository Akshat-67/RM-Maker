const API_BASE = 'http://localhost:5000/api';
let activeCaseData = null;

// The default firm mobile number (can be customized)
const FIRM_MOBILE = "8233658093"; 

document.addEventListener('DOMContentLoaded', async () => {
    console.log("[popup.js] DOMContentLoaded triggered.");
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
            
            showMsg(`Loaded: ${activeCaseData.executants[0]?.name_en || 'Unnamed Case'}`, 'success');
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
                const oneClickData = {
                    sro: activeCaseData.sro,
                    tehsil: activeCaseData.tehsil,
                    gender_card: getGenderCardType(activeCaseData.executants),
                    mobile: FIRM_MOBILE,
                    execution_date: activeCaseData.execution_date,
                    face_value: activeCaseData.face_value,
                    executants: activeCaseData.executants,
                    claimant: activeCaseData.claimant,
                    witnesses: activeCaseData.witnesses
                };

                if (chrome && chrome.storage && chrome.storage.local) {
                    chrome.storage.local.set({ 
                        oneClickRunning: true,
                        oneClickData: oneClickData,
                        partyStage: "EXECUTANT"
                    });
                    chrome.storage.local.remove(['stampDutyCalculated']);
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
    
    document.getElementById('btnAutofillLogin').addEventListener('click', () => {
        sendTabMessage('autofill_login', { mobile: FIRM_MOBILE });
    });
    
    document.getElementById('btnAutofillDetails').addEventListener('click', () => {
        sendTabMessage('autofill_details', {
            sro: activeCaseData.sro,
            tehsil: activeCaseData.tehsil,
            gender_card: getGenderCardType(activeCaseData.executants)
        });
    });
    
    document.getElementById('btnCalculateDuty').addEventListener('click', () => {
        sendTabMessage('autofill_calculate_duty', {
            execution_date: activeCaseData.execution_date,
            face_value: activeCaseData.face_value
        });
    });
    
    document.getElementById('btnAutofillExecutants').addEventListener('click', () => {
        sendTabMessage('autofill_executants', { executants: activeCaseData.executants });
    });
    
    document.getElementById('btnAutofillClaimant').addEventListener('click', () => {
        sendTabMessage('autofill_claimant', { claimant: activeCaseData.claimant });
    });
    
    document.getElementById('btnAutofillWitness1').addEventListener('click', () => {
        sendTabMessage('autofill_witness1', { witnesses: activeCaseData.witnesses });
    });
    
    document.getElementById('btnAutofillWitness2').addEventListener('click', () => {
        sendTabMessage('autofill_witness2', { witnesses: activeCaseData.witnesses });
    });
    
    document.getElementById('btnSetPresenter').addEventListener('click', () => {
        sendTabMessage('set_presenter', {});
    });
});

function getGenderCardType(executants) {
    if (!executants || executants.length === 0) return 'MALE_GEN';
    
    const genders = executants.map(e => e.gender);
    const hasMale = genders.includes('MALE');
    const hasFemale = genders.includes('FEMALE');
    
    if (hasMale && hasFemale) {
        return 'JOINT'; // Joint male/female card
    } else if (hasFemale) {
        return 'FEMALE_GEN'; // Female General card
    }
    return 'MALE_GEN'; // Default Male General card
}

function enableActionButtons() {
    document.querySelectorAll('.actions-list button').forEach(btn => btn.removeAttribute('disabled'));
}

document.addEventListener('visibilitychange', () => {
    // Re-check status when opening dropdown
});

function disableActionButtons() {
    document.querySelectorAll('.actions-list button').forEach(btn => btn.setAttribute('disabled', 'true'));
}

function showMsg(text, type) {
    const msg = document.getElementById('statusMsg');
    msg.textContent = text;
    msg.style.display = 'block';
    msg.className = `msg msg-${type}`;
}

async function sendTabMessage(action, data) {
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
        
        chrome.tabs.sendMessage(tab.id, { action, data }, (response) => {
            const err = chrome.runtime.lastError;
            if (err) {
                console.error('[RM-Maker Popup] sendMessage error:', err.message, 'tab:', tab.url);
                showMsg('Autofill failed: Content script not loaded. Please reload the extension at chrome://extensions and refresh the e-Panjiyan page.', 'error');
                return;
            }
            if (response && response.success) {
                showMsg(response.message || 'Action completed successfully!', 'success');
            } else {
                showMsg((response && response.error) || 'Action failed.', 'error');
            }
        });
    } catch (e) {
        showMsg('Error sending message: ' + e.message, 'error');
    }
}
