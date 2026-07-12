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
});
