// Workspace Review Event Handlers

function deleteFile(filename, bucket = null) {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;
    fetch(`/case/${CASE_ID}/delete_file`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ filename: filename, bucket: bucket })
    })
    .then(r => r.json())
    .then(resp => {
        if (resp.success) {
            location.reload();
        } else {
            alert('Failed to delete file: ' + (resp.error || 'Unknown error'));
        }
    })
    .catch(err => alert('Failed to delete file: ' + err));
}

function assignSelectedAadhars() {
    const rows = document.querySelectorAll('tr[id^="ua-row-"]');
    const assignedIndices = [];
    let assignedCount = 0;
    const docType = document.getElementById('docTypeSelect').value;

    const storageKey = 'case_file_roles_' + CASE_ID;
    let roles = JSON.parse(localStorage.getItem(storageKey) || '{}');

    rows.forEach(row => {
        const select = row.querySelector('.ua-role-select');
        if (!select) return;
        const role = select.value;
        if (!role) return;

        const index = select.getAttribute('data-index');
        assignedIndices.push(parseInt(index));

        // Automatically record the file-to-role mappings from data-files attribute
        const filesAttr = row.getAttribute('data-files');
        if (filesAttr) {
            try {
                const rowFiles = JSON.parse(filesAttr);
                if (Array.isArray(rowFiles)) {
                    rowFiles.forEach(item => {
                        if (item && typeof item === 'object' && item.file) {
                            roles[item.file] = {
                                role: role,
                                type: item.type || 'aadhar_front'
                            };
                        } else if (item && typeof item === 'string') {
                            roles[item] = {
                                role: role,
                                type: item.toLowerCase().includes('pan') ? 'pan' : 'aadhar_front'
                            };
                        }
                    });
                }
            } catch (e) {
                console.error("Failed to parse data-files", e);
            }
        }
        localStorage.setItem(storageKey, JSON.stringify(roles));

        const name = row.getAttribute('data-n');
        const nameEn = row.getAttribute('data-n_en') || '';
        const id = row.getAttribute('data-id');
        const age = row.getAttribute('data-a');
        const dob = row.getAttribute('data-dob');
        const relation = row.getAttribute('data-r');
        const relName = row.getAttribute('data-rn');
        const relNameEn = row.getAttribute('data-rn_en') || '';
        const address = row.getAttribute('data-adr');
        const addressEn = row.getAttribute('data-adr_en') || '';
        const isBpl = row.getAttribute('data-is_bpl') || '';
        const pan = row.getAttribute('data-pan') || '';
        const salutation = row.getAttribute('data-s');

        if (docType === 'SD') {
            if (role.startsWith('sellers.')) {
                const idx = role.split('.')[1];
                const nInput = document.getElementById(`field_sellers_${idx}_n`);
                if (nInput) nInput.value = name;
                
                const nEnInput = document.getElementById(`field_sellers_${idx}_n_en`);
                if (nEnInput) nEnInput.value = nameEn;
                
                const aInput = document.getElementById(`field_sellers_${idx}_a`);
                if (aInput) aInput.value = age;
                
                const rInput = document.getElementById(`field_sellers_${idx}_r`);
                if (rInput) rInput.value = relation === 'Father of' ? 'iqr Jh' : (relation === 'Wife of' ? 'iRuh Jh' : relation);
                
                const rnInput = document.getElementById(`field_sellers_${idx}_rn`);
                if (rnInput) rnInput.value = relName;
                
                const rnEnInput = document.getElementById(`field_sellers_${idx}_rn_en`);
                if (rnEnInput) rnEnInput.value = relNameEn;
                
                const adrText = document.getElementById(`field_sellers_${idx}_adr`);
                if (adrText) adrText.value = address;
                
                const adrEnText = document.getElementById(`field_sellers_${idx}_adr_en`);
                if (adrEnText) adrEnText.value = addressEn;
                
                const isBplInput = document.getElementById(`field_sellers_${idx}_is_bpl`);
                if (isBplInput) isBplInput.value = isBpl;
                
                const panInput = document.getElementById(`field_sellers_${idx}_pan`);
                if (panInput) panInput.value = pan;
                
                const idInput = document.getElementById(`field_sellers_${idx}_id`);
                if (idInput) idInput.value = id;

                const dobInput = document.getElementById(`field_sellers_${idx}_dob`);
                if (dobInput) dobInput.value = dob || '';

                ['n','a','r','rn','adr','id','pan','dob'].forEach(k => {
                    const cb = document.querySelector(`.verify-check[data-path="sellers.${idx}.${k}"]`);
                    if (cb) cb.checked = true;
                });
                assignedCount++;
            }
            else if (role.startsWith('buyers.')) {
                const idx = role.split('.')[1];
                const nInput = document.getElementById(`field_buyers_${idx}_n`);
                if (nInput) nInput.value = name;
                
                const nEnInput = document.getElementById(`field_buyers_${idx}_n_en`);
                if (nEnInput) nEnInput.value = nameEn;
                
                const aInput = document.getElementById(`field_buyers_${idx}_a`);
                if (aInput) aInput.value = age;
                
                const rInput = document.getElementById(`field_buyers_${idx}_r`);
                if (rInput) rInput.value = relation === 'Father of' ? 'iqr Jh' : (relation === 'Wife of' ? 'iRuh Jh' : relation);
                
                const rnInput = document.getElementById(`field_buyers_${idx}_rn`);
                if (rnInput) rnInput.value = relName;
                
                const rnEnInput = document.getElementById(`field_buyers_${idx}_rn_en`);
                if (rnEnInput) rnEnInput.value = relNameEn;
                
                const adrText = document.getElementById(`field_buyers_${idx}_adr`);
                if (adrText) adrText.value = address;
                
                const adrEnText = document.getElementById(`field_buyers_${idx}_adr_en`);
                if (adrEnText) adrEnText.value = addressEn;
                
                const isBplInput = document.getElementById(`field_buyers_${idx}_is_bpl`);
                if (isBplInput) isBplInput.value = isBpl;
                
                const panInput = document.getElementById(`field_buyers_${idx}_pan`);
                if (panInput) panInput.value = pan;
                
                const idInput = document.getElementById(`field_buyers_${idx}_id`);
                if (idInput) idInput.value = id;

                ['n','a','r','rn','adr','id','pan'].forEach(k => {
                    const cb = document.querySelector(`.verify-check[data-path="buyers.${idx}.${k}"]`);
                    if (cb) cb.checked = true;
                });
                assignedCount++;
            }
            else if (role.startsWith('ws.')) {
                const idx = role.split('.')[1];
                const nInput = document.getElementById(`field_ws_${idx}_n`);
                if (nInput) nInput.value = name;
                
                const nEnInput = document.getElementById(`field_ws_${idx}_n_en`);
                if (nEnInput) nEnInput.value = nameEn;
                
                const rInput = document.getElementById(`field_ws_${idx}_r`);
                if (rInput) rInput.value = relation === 'Father of' ? 'iqr Jh' : (relation === 'Wife of' ? 'iRuh Jh' : relation);
                
                const rnInput = document.getElementById(`field_ws_${idx}_rn`);
                if (rnInput) rnInput.value = relName;
                
                const rnEnInput = document.getElementById(`field_ws_${idx}_rn_en`);
                if (rnEnInput) rnEnInput.value = relNameEn;
                
                const adrText = document.getElementById(`field_ws_${idx}_adr`);
                if (adrText) adrText.value = address;
                
                const adrEnText = document.getElementById(`field_ws_${idx}_adr_en`);
                if (adrEnText) adrEnText.value = addressEn;

                const idInput = document.getElementById(`field_ws_${idx}_id`);
                if (idInput) idInput.value = id;

                ['n','r','rn','adr','id'].forEach(k => {
                    const cb = document.querySelector(`.verify-check[data-path="ws.${idx}.${k}"]`);
                    if (cb) cb.checked = true;
                });
                assignedCount++;
            }
        } else {
            // RM Assignments
            if (role.startsWith('bs.')) {
                const bIdx = role.split('.')[1];
                const salSelect = document.getElementById(`field_bs_${bIdx}_s`);
                if (salSelect) salSelect.value = salutation || "Mr.";
                
                const nInput = document.getElementById(`field_bs_${bIdx}_n`);
                if (nInput) nInput.value = name;
                
                const aInput = document.getElementById(`field_bs_${bIdx}_a`);
                if (aInput) aInput.value = age;
                
                const dobInput = document.getElementById(`field_bs_${bIdx}_dob`);
                if (dobInput) dobInput.value = dob || "";
                
                const rInput = document.getElementById(`field_bs_${bIdx}_r`);
                if (rInput) rInput.value = relation;
                
                const rnInput = document.getElementById(`field_bs_${bIdx}_rn`);
                if (rnInput) rnInput.value = relName;
                
                const adrText = document.getElementById(`field_bs_${bIdx}_adr`);
                if (adrText) adrText.value = address;
                
                const idInput = document.getElementById(`field_bs_${bIdx}_id`);
                if (idInput) idInput.value = id;

                ['s','n','a','r','rn','adr','id'].forEach(k => {
                    const cb = document.querySelector(`.verify-check[data-path="bs.${bIdx}.${k}"]`);
                    if (cb) cb.checked = true;
                });
                assignedCount++;
            } 
            else if (role.startsWith('ws.')) {
                const wIdx = role.split('.')[1];
                const nInput = document.getElementById(`field_ws_${wIdx}_n`);
                if (nInput) nInput.value = name;
                
                const rInput = document.getElementById(`field_ws_${wIdx}_r`);
                if (rInput) rInput.value = relation;
                
                const rnInput = document.getElementById(`field_ws_${wIdx}_rn`);
                if (rnInput) rnInput.value = relName;
                
                const adrText = document.getElementById(`field_ws_${wIdx}_adr`);
                if (adrText) adrText.value = address;

                const dobInput = document.getElementById(`field_ws_${wIdx}_dob`);
                if (dobInput) dobInput.value = dob || "";

                const aInput = document.getElementById(`field_ws_${wIdx}_a`);
                if (aInput) aInput.value = age || "";

                const idInput = document.getElementById(`field_ws_${wIdx}_id`);
                if (idInput) idInput.value = id || "";

                ['n','r','rn','adr','a','id'].forEach(k => {
                    const cb = document.querySelector(`.verify-check[data-path="ws.${wIdx}.${k}"]`);
                    if (cb) cb.checked = true;
                });
                assignedCount++;
            } 
            else if (role === 'bsign') {
                const sSelect = document.getElementById('field_bsign_s');
                if (sSelect) sSelect.value = salutation || "Mr.";

                const nInput = document.getElementById('field_bsign_n');
                if (nInput) nInput.value = name;

                const aInput = document.getElementById('field_bsign_a');
                if (aInput) aInput.value = age;
                
                const dobInput = document.getElementById('field_bsign_dob');
                if (dobInput) dobInput.value = dob || "";
                
                const rInput = document.getElementById('field_bsign_r');
                if (rInput) rInput.value = relation;
                
                const rnInput = document.getElementById('field_bsign_rn');
                if (rnInput) rnInput.value = relName;

                const idInput = document.getElementById('field_bsign_id');
                if (idInput) idInput.value = id;

                const adrText = document.getElementById('field_bsign_adr');
                if (adrText) adrText.value = address || "";

                ['s','n','a','r','rn','id','adr'].forEach(k => {
                    const cb = document.querySelector(`.verify-check[data-path="bsign.${k}"]`);
                    if (cb) cb.checked = true;
                });
                assignedCount++;
            }
        }
    });

    if (assignedCount === 0) {
        alert('Please select a role for at least one person first.');
        return;
    }

    saveCase((resp) => {
        if (resp.success) {
            fetch(`/case/${CASE_ID}/remove_unassigned_aadhars`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ indices: assignedIndices })
            })
            .then(r => r.json())
            .then(removeResp => {
                if (removeResp.success) {
                    location.reload();
                } else {
                    alert('Failed to remove assignments: ' + removeResp.error);
                }
            });
        } else {
            alert('Save failed: ' + resp.error);
        }
    });
}

function updateFileTabLabels() {
    const docTypeSelect = document.getElementById('docTypeSelect');
    const docType = docTypeSelect ? docTypeSelect.value : 'RM';
    const assignments = []; // Array of { role: "Borrower 1", name: "Kiran Devi", id: "1234..." }

    const getVal = (id) => {
        const el = document.getElementById(id);
        return el ? el.value.trim().toUpperCase() : '';
    };

    if (docType === 'SD') {
        // Sellers
        for (let i = 0; i < 5; i++) {
            const name = getVal(`field_sellers_${i}_n_en`) || getVal(`field_sellers_${i}_n`);
            const id = getVal(`field_sellers_${i}_id`);
            if (name) assignments.push({ role: `Seller ${i + 1}`, name, id });
        }
        // Buyers
        for (let i = 0; i < 5; i++) {
            const name = getVal(`field_buyers_${i}_n_en`) || getVal(`field_buyers_${i}_n`);
            const id = getVal(`field_buyers_${i}_id`);
            if (name) assignments.push({ role: `Buyer ${i + 1}`, name, id });
        }
        // Witnesses
        for (let i = 0; i < 5; i++) {
            const name = getVal(`field_ws_${i}_n_en`) || getVal(`field_ws_${i}_n`);
            const id = getVal(`field_ws_${i}_id`);
            if (name) assignments.push({ role: `Witness ${i + 1}`, name, id });
        }
    } else {
        // Borrowers
        for (let i = 0; i < 5; i++) {
            const name = getVal(`field_bs_${i}_n`);
            const id = getVal(`field_bs_${i}_id`);
            if (name) assignments.push({ role: `Borrower ${i + 1}`, name, id });
        }
        // Witnesses
        for (let i = 0; i < 5; i++) {
            const name = getVal(`field_ws_${i}_n`);
            const id = getVal(`field_ws_${i}_id`);
            if (name) assignments.push({ role: `Witness ${i + 1}`, name, id });
        }
        // Bank Signer
        const signerName = getVal('field_bsign_n');
        const signerId = getVal('field_bsign_id');
        if (signerName) assignments.push({ role: 'Bank Signer', name: signerName, id: signerId });
    }

    // Helper to strip vowels and non-alphanumeric chars for phonetic match
    const getPhoneticClean = (str) => {
        return str.toLowerCase()
                  .replace(/[^a-z0-9]/g, '')
                  .replace(/[aeiou]/g, '');
    };

    const storageKey = 'case_file_roles_' + CASE_ID;
    const manualRoles = JSON.parse(localStorage.getItem(storageKey) || '{}');
    const fileMappings = {}; // filename -> role display name
    const fileTypes = {}; // filename -> "aadhar_front|aadhar_back|pan"

    function getRoleDisplayName(roleKey) {
        if (!roleKey) return '';
        if (roleKey === 'bsign') return 'Bank Signer';
        const parts = roleKey.split('.');
        if (parts.length === 2) {
            const prefix = parts[0];
            const index = parseInt(parts[1]) + 1;
            if (prefix === 'bs') return `Borrower ${index}`;
            if (prefix === 'ws') return `Witness ${index}`;
            if (prefix === 'ss' || prefix === 'sellers') return `Seller ${index}`;
            if (prefix === 'buyers') return `Buyer ${index}`;
        }
        return roleKey;
    }

    function inferFileType(fn) {
        const name = fn.toLowerCase();
        if (name.includes('pan')) return 'pan';
        if (name.includes('back') || name.includes('reverse') || name.includes('rear') || name.includes('2') || name.includes('_b') || name.includes('-b')) {
            return 'aadhar_back';
        }
        return 'aadhar_front';
    }

    ALL_CASE_FILES.forEach(filename => {
        let matchedRole = "";
        let matchedType = "";

        // A. Check manual assignments from localStorage first
        if (manualRoles[filename]) {
            const assigned = manualRoles[filename];
            if (assigned && typeof assigned === 'object') {
                matchedRole = getRoleDisplayName(assigned.role);
                matchedType = assigned.type;
            } else if (typeof assigned === 'string') {
                matchedRole = getRoleDisplayName(assigned);
                matchedType = inferFileType(filename);
            }
        }

        // B. Fall back to automatic matching if no manual role is assigned
        if (!matchedRole) {
            const base = filename.substring(0, filename.lastIndexOf('.')).toLowerCase();
            if (base.includes('pan')) {
                // It's a PAN card
                matchedType = 'pan';
            } else {
                matchedType = inferFileType(filename);
            }

            const baseClean = getPhoneticClean(base);

            // Match by ID (last 4 digits)
            for (const ass of assignments) {
                if (ass.id) {
                    const idClean = ass.id.replace(/\s/g, '');
                    if (idClean.length >= 4) {
                        const last4 = idClean.substring(idClean.length - 4);
                        const baseDigits = base.replace(/[^0-9]/g, '');
                        if (baseDigits.includes(last4)) {
                            matchedRole = ass.role;
                            break;
                        }
                    }
                }
            }

            // Match by name (vowel stripped)
            if (!matchedRole) {
                for (const ass of assignments) {
                    const assClean = getPhoneticClean(ass.name);
                    if (assClean.length >= 2) {
                        if (baseClean.includes(assClean) || assClean.includes(baseClean)) {
                            matchedRole = ass.role;
                            break;
                        }
                    }
                }
            }
        }

        if (matchedRole) {
            fileMappings[filename] = matchedRole;
            fileTypes[filename] = matchedType || inferFileType(filename);
        }
    });

    // Group files by role
    const roleGroups = {};
    Object.entries(fileMappings).forEach(([filename, role]) => {
        if (!roleGroups[role]) roleGroups[role] = [];
        roleGroups[role].push({ file: filename, type: fileTypes[filename] });
    });

    window.CURRENT_ACTIVE_GROUPINGS = roleGroups;

    // Determine active representative and hidden files
    const hiddenFiles = new Set();
    const representativeFiles = {}; // role -> file

    Object.entries(roleGroups).forEach(([role, filesList]) => {
        let rep = filesList.find(f => f.type === 'aadhar_front') ||
                  filesList.find(f => f.type === 'aadhar_back') ||
                  filesList.find(f => f.type === 'pan') ||
                  filesList[0];
        
        if (rep) {
            representativeFiles[role] = rep.file;
            filesList.forEach(f => {
                if (f.file !== rep.file) {
                    hiddenFiles.add(f.file);
                }
            });
        }
    });

    // Update horizontal tabs and sidebar labels
    ALL_CASE_FILES.forEach(filename => {
        const role = fileMappings[filename];
        const isHidden = hiddenFiles.has(filename);
        const isRepresentative = role && (representativeFiles[role] === filename);

        const safeId = 'file-tab-' + filename.replace(/\./g, '_');
        const tabs = document.querySelectorAll(`[id="${safeId}"]`);
        const sidebarItems = document.querySelectorAll(`[data-sidebar-file="${filename}"]`);

        if (isHidden) {
            tabs.forEach(t => t.style.display = 'none');
            sidebarItems.forEach(s => s.style.display = 'none');
        } else {
            tabs.forEach(t => t.style.display = '');
            sidebarItems.forEach(s => s.style.display = '');

            let displayName = filename;
            if (isRepresentative) {
                const ext = filename.split('.').pop();
                displayName = `${role} [KYC].${ext}`;
            }

            tabs.forEach(t => {
                const textEl = t.querySelector('span') || t;
                textEl.textContent = '📄 ' + displayName;
            });

            const sidebarSpan = document.querySelector(`span[data-filename-span="${filename}"]`);
            if (sidebarSpan) {
                sidebarSpan.textContent = displayName;
                sidebarSpan.title = displayName;
            }
        }
    });
}

window.addEventListener('DOMContentLoaded', () => {
    // Run renaming logic on page load
    updateFileTabLabels();

    // Register blur/change event listeners to name/id fields to update tab labels dynamically
    const assignmentInputs = document.querySelectorAll('input[id^="field_"][id$="_n"], input[id^="field_"][id$="_n_en"], input[id^="field_"][id$="_id"]');
    assignmentInputs.forEach(inp => {
        inp.addEventListener('blur', updateFileTabLabels);
        inp.addEventListener('change', updateFileTabLabels);
    });

    // Automatically preview the first file if available
    const firstBtn = document.querySelector('.file-preview-btn');
    if (firstBtn) {
        const filename = firstBtn.getAttribute('data-filename') || firstBtn.getAttribute('title');
        if (filename) {
            previewFile(filename);
        }
    }

    // Shift-selection support for uploaded file checkboxes (both SD & RM modes)
    let lastCheckedFile = null;
    document.addEventListener('click', function (e) {
        const isSdChk = e.target.classList.contains('file-select-chk');
        const isRmChk = e.target.classList.contains('file-select-checkbox');
        
        if (isSdChk || isRmChk) {
            const listContainer = e.target.closest('.file-list-scroll');
            if (!listContainer) return;
            
            const selector = isSdChk ? '.file-select-chk' : '.file-select-checkbox';
            const checkboxes = Array.from(listContainer.querySelectorAll(selector));
            
            if (e.shiftKey && lastCheckedFile && lastCheckedFile !== e.target && checkboxes.includes(lastCheckedFile)) {
                let start = checkboxes.indexOf(lastCheckedFile);
                let end = checkboxes.indexOf(e.target);
                
                if (start !== -1 && end !== -1) {
                    const checkedState = e.target.checked;
                    const [minIdx, maxIdx] = start < end ? [start, end] : [end, start];
                    
                    for (let i = minIdx; i <= maxIdx; i++) {
                        checkboxes[i].checked = checkedState;
                        checkboxes[i].dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
            }
            
            lastCheckedFile = e.target;
        }
    });
});
