// Workspace Preview Event Handlers
let activeGroupFiles = [];


function showGroupedFile(type) {
    const match = activeGroupFiles.find(f => f.type === type);
    if (match) {
        previewFileDirect(match.file);
        // Highlight buttons
        const btnFront = document.getElementById('btnToggleFront');
        const btnBack = document.getElementById('btnToggleBack');
        const btnPan = document.getElementById('btnTogglePan');
        
        btnFront.className = type === 'aadhar_front' ? "btn btn-primary btn-xs fw-bold px-2.5 py-1" : "btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white";
        btnBack.className = type === 'aadhar_back' ? "btn btn-primary btn-xs fw-bold px-2.5 py-1" : "btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white";
        btnPan.className = type === 'pan' ? "btn btn-primary btn-xs fw-bold px-2.5 py-1" : "btn btn-outline-secondary btn-xs fw-bold px-2.5 py-1 bg-white";
    }
}

function previewFileDirect(filename) {
    const iframe = document.getElementById('previewIframe');
    const img = document.getElementById('previewImg');
    const placeholder = document.getElementById('previewPlaceholder');
    
    iframe.style.display = 'none';
    img.style.display = 'none';
    placeholder.style.display = 'none';
    
    const fileUrl = `/case/${CASE_ID}/file/${filename}`;
    const ext = filename.split('.').pop().toLowerCase();
    if (ext === 'pdf') {
        iframe.src = fileUrl;
        iframe.style.display = 'block';
    } else if (['png', 'jpg', 'jpeg'].includes(ext)) {
        img.src = fileUrl;
        img.style.display = 'block';
    } else {
        placeholder.style.display = 'block';
        placeholder.querySelector('span:last-child').textContent = `Preview not supported for .${ext} files. Click download options to view.`;
    }
}

function previewFile(filename) {
    // Deactivate all buttons highlights
    document.querySelectorAll('.file-preview-btn').forEach(btn => btn.classList.remove('active-preview'));
    
    // Find role and matching group
    const storageKey = 'case_file_roles_' + CASE_ID;
    const manualRoles = JSON.parse(localStorage.getItem(storageKey) || '{}');
    
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

    const assigned = manualRoles[filename];
    let role = "";
    if (assigned && typeof assigned === 'object') {
        role = getRoleDisplayName(assigned.role);
    } else if (typeof assigned === 'string') {
        role = getRoleDisplayName(assigned);
    }

    // If not found in localStorage manual assignments, try resolving from active mappings
    if (!role && window.CURRENT_ACTIVE_GROUPINGS) {
        for (const [r, files] of Object.entries(window.CURRENT_ACTIVE_GROUPINGS)) {
            if (files.some(f => f.file === filename)) {
                role = r;
                break;
            }
        }
    }
    
    const toggleContainer = document.getElementById('frontBackToggleContainer');
    const btnFront = document.getElementById('btnToggleFront');
    const btnBack = document.getElementById('btnToggleBack');
    const btnPan = document.getElementById('btnTogglePan');
    
    if (role && window.CURRENT_ACTIVE_GROUPINGS && window.CURRENT_ACTIVE_GROUPINGS[role]) {
        activeGroupFiles = window.CURRENT_ACTIVE_GROUPINGS[role];
        toggleContainer.style.display = 'flex';
        
        const hasFront = activeGroupFiles.some(f => f.type === 'aadhar_front');
        const hasBack = activeGroupFiles.some(f => f.type === 'aadhar_back');
        const hasPan = activeGroupFiles.some(f => f.type === 'pan');
        
        btnFront.style.display = hasFront ? 'inline-block' : 'none';
        btnBack.style.display = hasBack ? 'inline-block' : 'none';
        btnPan.style.display = hasPan ? 'inline-block' : 'none';
        
        // Determine active type of the selected file
        const currentMap = activeGroupFiles.find(f => f.file === filename);
        const currentType = currentMap ? currentMap.type : (hasFront ? 'aadhar_front' : (hasBack ? 'aadhar_back' : 'pan'));
        showGroupedFile(currentType);
    } else {
        activeGroupFiles = [];
        toggleContainer.style.display = 'none';
        previewFileDirect(filename);
    }
    
    // Highlight the tab itself
    const safeId = 'file-tab-' + filename.replace(/\./g, '_');
    const activeBtn = document.getElementById(safeId);
    if (activeBtn) {
        activeBtn.classList.add('active-preview');
    }
    
    const titleEl = document.getElementById('previewTitle');
    if (titleEl) {
        titleEl.textContent = filename;
        titleEl.title = filename;
    }
}

function refreshDraftPreview() {
    const contentDiv = document.getElementById('draftPreviewContent');
    if (!contentDiv) return;
    
    contentDiv.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
            <span class="ms-2 small text-muted">Compiling live template draft...</span>
        </div>
    `;
    
    const data = collectFieldData();
    const verified = collectVerifiedFields();
    const docType = document.getElementById('docTypeSelect').value;
    
    fetch(`/case/${CASE_ID}/preview_draft`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            doc_type: docType,
            bank: document.getElementById('bankSelect')?.value || '',
            borrowers: document.getElementById('borrowerSelect')?.value || '1',
            loans: document.getElementById('loanSelect')?.value || '1',
            properties: document.getElementById('propertiesSelect')?.value || '1',
            sellers_count: document.getElementById('sellersSelect')?.value || '1',
            buyers_count: document.getElementById('buyersSelect')?.value || '1',
            property_type: document.getElementById('propertyTypeSelect')?.value || 'Plot',
            selected_template: customTemplateFilename,
            data: data,
            verified_fields: verified
        })
    })
    .then(r => r.json())
    .then(resp => {
        if (resp.success) {
            contentDiv.innerHTML = resp.preview_html;
        } else {
            contentDiv.innerHTML = `<div class="alert alert-danger small p-2 m-2">Preview failed: ${resp.error}</div>`;
        }
    })
    .catch(e => {
        contentDiv.innerHTML = `<div class="alert alert-danger small p-2 m-2">Error: ${e}</div>`;
    });
}

function renderRichNarrative() {
    const val = document.getElementById('chainNarrativePreview')?.value || "";
    const target = document.getElementById('richNarrativeContent');
    if (!target) return;
    
    if (!val.trim()) {
        target.innerHTML = `<div class="text-center text-muted py-4 small">No narrative text generated yet. Complete step 3 configuration to generate prior title chain events.</div>`;
        return;
    }
    
    target.innerHTML = `
        <div class="p-3 bg-white border rounded shadow-sm text-secondary small" style="line-height:1.7;">
            ${val.replace(/\n/g, '<br>')}
        </div>
    `;
}

// Automatically trigger preview when switching to the draft tab
window.addEventListener('DOMContentLoaded', () => {
    // Sync Dropdown selector with Bootstrap Tab changes
    document.querySelectorAll('#verificationTabs button').forEach(tab => {
        tab.addEventListener('shown.bs.tab', (e) => {
            const targetId = e.target.getAttribute('data-bs-target').replace('#', '');
            const selector = document.getElementById('verificationSectionSelector');
            if (selector) {
                selector.value = targetId;
            }
        });
    });

    const draftTab = document.getElementById('draft-main-tab') || document.getElementById('draft-tab');
    if (draftTab) {
        draftTab.addEventListener('shown.bs.tab', () => {
            // Auto-generate if it still has placeholder
            if (document.getElementById('draftPreviewContent') && document.getElementById('draftPreviewContent').querySelector('.spinner-border') === null) {
                refreshDraftPreview();
            }
        });
    }

    // Initialize document snapping focus listener
    initWorkspaceFocusAttribution();
});

function getRoleForInputId(id) {
    if (!id.startsWith('field_')) return null;
    const parts = id.replace('field_', '').split('_');
    if (parts[0] === 'bsign') {
        return 'bsign';
    }
    if (parts.length >= 2) {
        const prefix = parts[0];
        const index = parts[1];
        if (!isNaN(index)) {
            return `${prefix}.${index}`;
        }
    }
    return null;
}

function previewFileWithPage(filename, page) {
    document.querySelectorAll('.file-preview-btn').forEach(btn => {
        if (btn.getAttribute('data-filename') === filename) {
            btn.classList.add('active-preview');
        } else {
            btn.classList.remove('active-preview');
        }
    });

    const iframe = document.getElementById('previewIframe');
    const img = document.getElementById('previewImg');
    const placeholder = document.getElementById('previewPlaceholder');
    
    iframe.style.display = 'none';
    img.style.display = 'none';
    placeholder.style.display = 'none';
    
    const ext = filename.split('.').pop().toLowerCase();
    let fileUrl = `/case/${CASE_ID}/file/${filename}`;
    if (ext === 'pdf') {
        fileUrl += `#page=${page}`;
        iframe.src = fileUrl;
        iframe.style.display = 'block';
    } else if (['png', 'jpg', 'jpeg'].includes(ext)) {
        img.src = fileUrl;
        img.style.display = 'block';
    } else {
        placeholder.style.display = 'block';
        placeholder.querySelector('span:last-child').textContent = `Preview not supported for .${ext} files. Click download options to view.`;
    }
}

function snapPreviewToFieldSource(id) {
    return; // Disabled to prevent left side document preview reload on field focus
}


function renderSourceChip(parent, extInfo) {
    const oldChip = document.querySelector('.source-attribution-chip');
    if (oldChip) {
        oldChip.remove();
    }
    if (!parent) return;

    const labelRow = parent.querySelector('.d-flex.justify-content-between') || parent;
    const chip = document.createElement('span');
    chip.className = 'source-attribution-chip text-muted small ms-2';

    if (extInfo && extInfo.source_file) {
        chip.style.cssText = 'font-size: 0.72rem; padding: 0.1rem 0.35rem; background-color: #f1f5f9; border-radius: 4px; border: 1px solid #cbd5e1; display: inline-flex; align-items: center; gap: 4px; cursor: pointer; color: #475569 !important; font-weight: bold;';
        chip.innerHTML = `📄 ${extInfo.source_file} P${extInfo.page_number || 1}`;
        
        chip.onclick = () => {
            previewFileWithPage(extInfo.source_file, extInfo.page_number || 1);
            drawHighlightOverlay(extInfo.bounding_box);
        };
    } else {
        chip.style.cssText = 'font-size: 0.72rem; padding: 0.1rem 0.35rem; background-color: #f8fafc; border-radius: 4px; border: 1px dashed #cbd5e1; color: #94a3b8 !important;';
        chip.textContent = 'No attribution available';
    }

    const label = labelRow.querySelector('label');
    if (label) {
        label.after(chip);
    } else {
        labelRow.prepend(chip);
    }
}

function drawHighlightOverlay(boundingBox) {
    const overlay = document.getElementById('previewHighlightOverlay');
    if (!overlay) return;

    if (boundingBox && Array.isArray(boundingBox) && boundingBox.length === 4) {
        const [y1, x1, y2, x2] = boundingBox;
        overlay.style.top = y1 + '%';
        overlay.style.left = x1 + '%';
        overlay.style.width = (x2 - x1) + '%';
        overlay.style.height = (y2 - y1) + '%';
        overlay.style.display = 'block';
    } else {
        overlay.style.display = 'none';
    }
}

function initWorkspaceFocusAttribution() {
    // Focus snapping event listeners on inputs disabled by user request to prevent left side preview reload

    // Register progress update change listeners
    const verifyCheckboxes = document.querySelectorAll('.verify-check');
    verifyCheckboxes.forEach(cb => {
        cb.addEventListener('change', updateVerificationProgress);
        cb.tabIndex = -1; // Skip verify checkboxes during tab sequence
    });

    // Apply visual confidence decorations to form controls
    applyVisualConfidenceBorders();

    // Dynamically append "Verify Category" buttons to card/sub-section headers
    addVerifyCategoryButtons();

    // Hook into global saveCase function to refresh validation state on save
    if (typeof saveCase === 'function') {
        const originalSaveCase = saveCase;
        saveCase = function(callback) {
            originalSaveCase((resp) => {
                if (callback) {
                    callback(resp);
                } else {
                    const btn = document.querySelector('button[onclick="saveCase()"]');
                    if (btn) {
                        const oldText = btn.textContent;
                        btn.textContent = '✅ Saved!';
                        setTimeout(() => btn.textContent = oldText, 1500);
                    }
                }
                fetchAndUpdateCaseHealth();
            });
        };
    }

    // Run initial progress calculations
    updateVerificationProgress();
}

function applyVisualConfidenceBorders() {
    return; // Visual confidence markers and badges removed by user request
}

function updateVerificationProgress() {
    const checkboxes = document.querySelectorAll('.verify-check');
    if (checkboxes.length === 0) return;

    let checkedCount = 0;
    checkboxes.forEach(cb => {
        if (cb.checked) checkedCount++;
    });

    const percent = Math.round((checkedCount / checkboxes.length) * 100);

    const bar = document.getElementById('overallProgressBar');
    const label = document.getElementById('overallProgressLabel');
    if (bar) {
        bar.style.width = percent + '%';
        bar.setAttribute('aria-valuenow', checkedCount);
        bar.setAttribute('aria-valuemax', checkboxes.length);
    }
    if (label) {
        label.textContent = `Verified: ${checkedCount} / ${checkboxes.length} fields (${percent}%)`;
    }

    const categories = [
        { paneId: 'pane-parties', badgeId: 'badge-parties' },
        { paneId: 'pane-witnesses', badgeId: 'badge-witnesses' },
        { paneId: 'pane-property', badgeId: 'badge-property' },
        { paneId: 'pane-loan', badgeId: 'badge-loans' },
        { paneId: 'pane-schedules', badgeId: 'badge-schedules' },
        { paneId: 'pane-payments', badgeId: 'badge-loans' } // SD matches loans badge key
    ];

    categories.forEach(cat => {
        const pane = document.getElementById(cat.paneId);
        const badge = document.getElementById(cat.badgeId);
        if (!pane || !badge) return;

        const subCheckboxes = pane.querySelectorAll('.verify-check');
        if (subCheckboxes.length === 0) {
            badge.style.display = 'none';
            return;
        }

        let subChecked = 0;
        subCheckboxes.forEach(cb => {
            if (cb.checked) subChecked++;
        });

        badge.style.display = 'inline-block';
        if (subChecked === subCheckboxes.length) {
            badge.className = 'tab-completion-badge tab-badge-complete';
            badge.innerHTML = `✓ ${subChecked}/${subCheckboxes.length}`;
        } else {
            badge.className = 'tab-completion-badge tab-badge-incomplete';
            badge.textContent = `${subChecked}/${subCheckboxes.length}`;
        }
    });

    updateCompileSafetyGate(percent, checkedCount, checkboxes.length);
    fetchAndUpdateCaseHealth();
}

function updateCompileSafetyGate(percent, checkedCount, totalCount) {
    const isSD = (typeof CASE_DOC_TYPE !== 'undefined' && CASE_DOC_TYPE === 'SD');
    const generateBtn = document.querySelector(isSD ? 'button[onclick="generateSD()"]' : 'button[onclick="generateRM()"]');
    if (!generateBtn) return;

    // Always keep generate button active and green by user request
    generateBtn.disabled = false;
    generateBtn.title = 'Ready to compile final document';
    generateBtn.classList.remove('btn-secondary');
    generateBtn.classList.add('btn-success');
}

// -------------------------------------------------------------
// Version 2.1 Keyboard Workflow Event Listeners & Shortcuts
// -------------------------------------------------------------
let lastBulkActionState = null;

document.addEventListener('keydown', (e) => {
    // 1. Ctrl+S: Save Progress
    if (e.ctrlKey && e.key.toLowerCase() === 's') {
        e.preventDefault();
        if (typeof saveCase === 'function') {
            saveCase();
        }
    }

    // 2. Ctrl+Enter: Compile final document
    if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        const isSD = (typeof CASE_DOC_TYPE !== 'undefined' && CASE_DOC_TYPE === 'SD');
        const generateBtn = document.querySelector(isSD ? 'button[onclick="generateSD()"]' : 'button[onclick="generateRM()"]');
        if (generateBtn && !generateBtn.disabled) {
            generateBtn.click();
        }
    }

    // 3. Alt+N: Jump to next unverified field
    if (e.altKey && e.key.toLowerCase() === 'n') {
        e.preventDefault();
        focusNextUnverifiedField();
    }

    // 4. Alt+V: Toggle verification checkbox for active field
    if (e.altKey && e.key.toLowerCase() === 'v') {
        e.preventDefault();
        toggleActiveFieldVerification();
    }

    // 5. Alt+A: Verify current Section
    if (e.altKey && e.key.toLowerCase() === 'a') {
        e.preventDefault();
        verifySection();
    }

    // 6. Ctrl+Z: Undo last bulk verification action
    if (e.ctrlKey && e.key.toLowerCase() === 'z') {
        e.preventDefault();
        undoLastBulkAction();
    }
});

function focusNextUnverifiedField() {
    const inputs = Array.from(document.querySelectorAll('input[id^="field_"]:not([type="hidden"]), textarea[id^="field_"]'));
    // Filter to only visible fields (not hidden inside non-active tab panes)
    const visibleInputs = inputs.filter(inp => {
        const pane = inp.closest('.tab-pane');
        return !pane || pane.classList.contains('active');
    });

    if (visibleInputs.length === 0) return;

    let startIndex = 0;
    const active = document.activeElement;
    if (active && visibleInputs.includes(active)) {
        startIndex = visibleInputs.indexOf(active) + 1;
    }

    for (let i = 0; i < visibleInputs.length; i++) {
        const idx = (startIndex + i) % visibleInputs.length;
        const inp = visibleInputs[idx];
        const parent = inp.parentElement;
        if (parent) {
            const checkbox = parent.querySelector('.verify-check');
            if (checkbox && !checkbox.checked) {
                inp.focus();
                inp.scrollIntoView({ behavior: 'smooth', block: 'center' });
                break;
            }
        }
    }
}

function toggleActiveFieldVerification() {
    const active = document.activeElement;
    if (active && (active.id.startsWith('field_') || active.tagName === 'INPUT' || active.tagName === 'TEXTAREA')) {
        const parent = active.parentElement;
        if (parent) {
            const checkbox = parent.querySelector('.verify-check');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change'));
            }
        }
    }
}

function verifySection() {
    const activePane = document.querySelector('.tab-pane.active');
    if (!activePane) return;
    const checkboxes = activePane.querySelectorAll('.verify-check');
    bulkVerifyCheckboxes(checkboxes, true, 'Section');
}

function verifyCategory(btn) {
    const card = btn.closest('.card');
    if (!card) return;
    const checkboxes = card.querySelectorAll('.verify-check');
    const header = card.querySelector('h6');
    const titleText = header ? header.firstChild.textContent.trim() : 'Category';
    bulkVerifyCheckboxes(checkboxes, true, `Category "${titleText}"`);
}

function addVerifyCategoryButtons() {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        const header = card.querySelector('h6');
        if (!header) return;

        if (header.querySelector('.verify-category-btn')) return;

        header.classList.add('d-flex', 'justify-content-between', 'align-items-center');

        const btn = document.createElement('span');
        btn.className = 'badge bg-light text-primary border cursor-pointer verify-category-btn ms-2 py-1';
        btn.style.fontSize = '0.65rem';
        btn.style.cursor = 'pointer';
        btn.textContent = '✓ Verify Category';
        
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const checkboxes = card.querySelectorAll('.verify-check');
            const titleText = header.firstChild.textContent.trim();
            bulkVerifyCheckboxes(checkboxes, true, `Category "${titleText}"`);
        });

        header.appendChild(btn);
    });
}

function bulkVerifyCheckboxes(checkboxes, verifyState, customLabel = 'Section') {
    if (checkboxes.length === 0) return;

    lastBulkActionState = [];
    checkboxes.forEach(cb => {
        lastBulkActionState.push({
            element: cb,
            wasChecked: cb.checked
        });
        cb.checked = verifyState;
        cb.dispatchEvent(new Event('change'));
    });

    const banner = document.getElementById('bulkUndoBanner');
    const msg = document.getElementById('bulkUndoMessage');
    if (banner && msg) {
        msg.textContent = `${customLabel} bulk verified: checked ${checkboxes.length} fields.`;
        banner.classList.remove('d-none');
        banner.classList.add('d-flex');
    }
}

function undoLastBulkAction() {
    if (!lastBulkActionState || lastBulkActionState.length === 0) return;

    lastBulkActionState.forEach(item => {
        item.element.checked = item.wasChecked;
        item.element.dispatchEvent(new Event('change'));
    });

    lastBulkActionState = null;

    const banner = document.getElementById('bulkUndoBanner');
    if (banner) {
        banner.classList.add('d-none');
        banner.classList.remove('d-flex');
    }
}

function fetchAndUpdateCaseHealth() {
    if (typeof CASE_ID === 'undefined') return;

    fetch(`/api/case/${CASE_ID}/validation`)
        .then(res => res.json())
        .then(data => {
            const badge = document.getElementById('caseHealthBadge');
            if (badge) {
                badge.style.display = 'inline-block';
                if (data.is_valid) {
                    badge.className = 'badge bg-success ms-2';
                    badge.innerHTML = 'Case Health: 🟢 Ready';
                    badge.title = 'No validation errors found';
                } else {
                    badge.className = 'badge bg-warning text-dark ms-2';
                    badge.innerHTML = 'Case Health: ⚠️ Issues Found';
                    const count = data.discrepancies.length;
                    badge.title = `${count} validation discrepancy issue(s) detected.`;
                }
            }
            renderLiveValidation(data);
        })
        .catch(err => console.error("Error fetching validation:", err));
}

function renderLiveValidation(data) {
    const listContainer = document.getElementById('validationChecklistContent');
    if (!listContainer) return;
    
    listContainer.innerHTML = '';
    const discrepancies = data.discrepancies || [];
    
    // Update the tab badge count
    const badge = document.getElementById('checklist-count-badge');
    if (badge) {
        const count = discrepancies.length;
        if (count > 0) {
            badge.textContent = count;
            badge.classList.remove('d-none');
        } else {
            badge.classList.add('d-none');
        }
    }
    
    if (discrepancies.length === 0) {
        listContainer.innerHTML = `
            <div class="text-center py-4 text-muted">
                <span class="fs-1 d-block mb-2">🎉</span>
                <span class="fw-bold">All checks passed!</span>
                <p class="small mt-1 mb-0">No discrepancies or missing fields detected.</p>
            </div>
        `;
        const statusText = document.getElementById('validationStatusText');
        if (statusText) statusText.innerHTML = '🟢 <strong>Ready</strong>';
        return;
    }
    
    const severityOrder = { "high": 0, "medium": 1, "low": 2 };
    discrepancies.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);
    
    let highCount = 0;
    let mediumCount = 0;
    let lowCount = 0;
    
    discrepancies.forEach(d => {
        if (d.severity === 'high') highCount++;
        else if (d.severity === 'medium') mediumCount++;
        else lowCount++;
        
        const itemDiv = document.createElement('div');
        itemDiv.className = `discrepancy-item discrepancy-item-${d.severity}`;
        
        const categoryLabel = d.category ? d.category.toUpperCase() : 'CHECK';
        
        let fixButtonHtml = '';
        if (d.auto_fix_available && d.auto_fix_payload) {
            const p = d.auto_fix_payload;
            fixButtonHtml = `
                <div class="mt-2 text-end">
                    <button class="btn btn-xs btn-outline-primary discrepancy-fix-btn bg-white" onclick="applyAutoFix('${p.action_type}', '${p.target_path}', '${p.value}')">
                        ⚡ Auto-Fix
                    </button>
                </div>
            `;
        }
        
        itemDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <strong class="discrepancy-title">${categoryLabel}</strong>
                <span class="badge rounded-pill bg-${d.severity === 'high' ? 'danger' : d.severity === 'medium' ? 'warning text-dark' : 'success'}">${d.severity}</span>
            </div>
            <div class="discrepancy-explanation">${d.explanation}</div>
            <div class="text-muted small">💡 ${d.suggested_fix}</div>
            ${fixButtonHtml}
        `;
        listContainer.appendChild(itemDiv);
    });
    
    const statusText = document.getElementById('validationStatusText');
    if (statusText) {
        statusText.innerHTML = `⚠️ <strong>${highCount} Errors, ${mediumCount} Warnings</strong>`;
    }
}

function applyAutoFix(actionType, targetPath, value) {
    const parts = targetPath.split('.');
    let fieldId = '';
    if (parts[0] === 'bs' && parts.length === 3) {
        fieldId = `field_bs_${parts[1]}_${parts[2]}`;
    } else if (parts[0] === 'bsign' && parts.length === 2) {
        fieldId = `field_bsign_${parts[1]}`;
    } else if (parts[0] === 'ls' && parts.length === 3) {
        fieldId = `field_ls_${parts[1]}_${parts[2]}`;
    } else if (parts[0] === 'ps' && parts.length === 3) {
        fieldId = `field_ps_${parts[1]}_${parts[2]}`;
    }
    
    if (fieldId) {
        const input = document.getElementById(fieldId);
        if (input) {
            input.value = value;
            input.dispatchEvent(new Event('change', { bubbles: true }));
            if (typeof saveCase === 'function') {
                saveCase();
            }
            return;
        }
    }
    alert(`Could not automatically fix ${targetPath}. Please update the field manually.`);
}

function triggerAIProofreader() {
    const btn = document.getElementById('btnRunProofreader');
    const spinner = document.getElementById('validationSpinner');
    
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '🤖 Running...';
    }
    if (spinner) spinner.classList.remove('d-none');
    
    fetch(`/api/case/${CASE_ID}/validation?run_proofreader=true`)
        .then(res => res.json())
        .then(data => {
            renderLiveValidation(data);
            
            // Activate the checklist tab automatically
            const tabEl = document.getElementById('checklist-main-tab');
            if (tabEl) {
                const tab = new bootstrap.Tab(tabEl);
                tab.show();
            }
        })
        .catch(err => {
            console.error("Error during AI proofreader run:", err);
            alert("AI proofreader failed: " + err.message);
        })
        .finally(() => {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '🤖 AI Proofread';
            }
            if (spinner) spinner.classList.add('d-none');
        });
}

// Debounce input updates for auto-validation
let validationDebounceTimer = null;
function debounceValidation() {
    clearTimeout(validationDebounceTimer);
    validationDebounceTimer = setTimeout(() => {
        if (typeof saveCase === 'function') {
            saveCase();
        }
    }, 600);
}

document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch
    setTimeout(fetchAndUpdateCaseHealth, 1000);
    
    const container = document.getElementById('verificationContent');
    if (container) {
        container.addEventListener('input', (e) => {
            if (e.target.classList.contains('ua-role-select')) return;
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                debounceValidation();
            }
        });
        container.addEventListener('change', (e) => {
            if (e.target.classList.contains('ua-role-select')) return;
            if (e.target.tagName === 'SELECT' || e.target.tagName === 'INPUT') {
                debounceValidation();
            }
        });
    }
});









