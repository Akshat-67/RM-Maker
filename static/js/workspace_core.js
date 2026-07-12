// Workspace Core Helpers

function switchStep(stepNum) {
    // Persist the active step selection in localStorage (scoped by case ID)
    if (typeof CASE_ID !== 'undefined') {
        localStorage.setItem('activeCaseStep_' + CASE_ID, stepNum);
    }
    const uploadView = document.getElementById('step-upload-view');
    const reviewView = document.getElementById('step-review-view');
    const chainView = document.getElementById('step-chain-view');
    
    const indicatorUpload = document.getElementById('step-indicator-upload');
    const indicatorReview = document.getElementById('step-indicator-review');
    const indicatorChain = document.getElementById('step-indicator-chain');
    
    if (stepNum === 1) {
        uploadView.classList.remove('d-none');
        reviewView.classList.add('d-none');
        chainView.classList.add('d-none');
        
        indicatorUpload.classList.add('active-step');
        indicatorReview.classList.remove('active-step');
        indicatorChain.classList.remove('active-step');
        document.body.style.overflow = 'auto';
    } else if (stepNum === 2) {
        uploadView.classList.add('d-none');
        reviewView.classList.remove('d-none');
        chainView.classList.add('d-none');
        
        indicatorUpload.classList.remove('active-step');
        indicatorReview.classList.add('active-step');
        indicatorChain.classList.remove('active-step');
        document.body.style.overflow = 'hidden';
        
        // Automatically preview first file if iframe source is empty
        const iframe = document.getElementById('previewIframe');
        const img = document.getElementById('previewImg');
        if (!iframe.src && !img.src) {
            const firstBtn = document.querySelector('.file-preview-btn');
            if (firstBtn) {
                const filename = firstBtn.getAttribute('title');
                if (filename) previewFile(filename);
            }
        }
    } else if (stepNum === 3) {
        uploadView.classList.add('d-none');
        reviewView.classList.add('d-none');
        chainView.classList.remove('d-none');
        
        indicatorUpload.classList.remove('active-step');
        indicatorReview.classList.remove('active-step');
        indicatorChain.classList.add('active-step');
        document.body.style.overflow = 'auto';
        
        // Initialize timeline view on display
        renderTimeline();
        selectNode(parseInt(document.getElementById('activeNodeIndex').value) || 0);
    }
}

function loadModels() {
    const select = document.getElementById('modelSelect');
    if (!select) return;
    const prevValue = select.value;
    select.innerHTML = '<option disabled selected>Loading models...</option>';

    fetch('/get_models')
        .then(r => r.json())
        .then(resp => {
            if (resp.success && resp.models.length > 0) {
                select.innerHTML = '';
                let matched = false;

                resp.models.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.textContent = m.replace('models/', '');
                    select.appendChild(opt);

                    if (m === prevValue) {
                        opt.selected = true;
                        matched = true;
                    }
                });

                if (!matched) {
                    const preferred = ['gemini-2.5-flash', 'flash', 'gemini-2'];
                    let found = false;
                    for (const keyword of preferred) {
                        const opt = Array.from(select.options).find(o => o.value.includes(keyword));
                        if (opt) { opt.selected = true; found = true; break; }
                    }
                    if (!found) select.options[0].selected = true;
                }
            } else {
                select.innerHTML = '<option value="gemini-1.5-flash">gemini-1.5-flash</option>';
            }
        })
        .catch(() => {
            select.innerHTML = '<option value="gemini-1.5-flash">gemini-1.5-flash</option>';
        });
}

// Dynamic State reload routines
function onDocTypeChange() {
    saveCase(() => { location.reload(); });
}
function onBankChange() {
    saveCase(() => { location.reload(); });
}
function onBorrowerChange() {
    saveCase(() => { location.reload(); });
}
function onLoanChange() {
    saveCase(() => { location.reload(); });
}
function onPropertiesChange() {
    saveCase(() => { location.reload(); });
}
function onSellersChange() {
    saveCase(() => { location.reload(); });
}
function onBuyersChange() {
    saveCase(() => { location.reload(); });
}
function onPropertyTypeChange() {
    saveCase(() => { location.reload(); });
}

function updateTemplateDisplay() {
    const docType = document.getElementById('docTypeSelect')?.value || 'RM';
    const display = document.getElementById('templateDisplay');
    if (!display) return;

    if (customTemplateFilename) {
        display.textContent = `✓ Selected Template: ${customTemplateFilename}`;
        display.classList.remove('text-danger', 'text-muted');
        display.classList.add('text-success', 'fw-bold');
        
        // Set label on the dropdown button
        const labelSpan = document.getElementById('doc_template_label');
        if (labelSpan) {
            labelSpan.textContent = customTemplateFilename;
        }
        
        // Highlight in dropdown
        const container = document.getElementById('doc_template_options_list');
        if (container) {
            container.querySelectorAll(".doc-template-option-btn").forEach(btn => {
                if (btn.getAttribute("data-filename") === customTemplateFilename) {
                    btn.classList.add("active");
                } else {
                    btn.classList.remove("active");
                }
            });
        }
        
        // Show clear button
        const clearBtn = document.getElementById('clearCustomTemplateBtn');
        if (clearBtn) clearBtn.style.display = 'inline-block';
        return;
    }

    // Otherwise, it's auto-selected
    // Hide clear button
    const clearBtn = document.getElementById('clearCustomTemplateBtn');
    if (clearBtn) clearBtn.style.display = 'none';
    
    // Reset label on dropdown button
    const labelSpan = document.getElementById('doc_template_label');
    if (labelSpan) {
        labelSpan.textContent = "Auto-Select Template";
    }
    
    // Highlight Auto-Select in dropdown
    const container = document.getElementById('doc_template_options_list');
    if (container) {
        container.querySelectorAll(".doc-template-option-btn").forEach(btn => {
            if (btn.getAttribute("data-filename") === "") {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        });
    }

    display.classList.remove('text-success', 'fw-bold');
    display.classList.add('text-muted');
    display.textContent = 'Auto-selecting template...';

    let url = '';
    if (docType === 'SD') {
        const sellers = document.getElementById('sellersSelect')?.value || '1';
        const buyers = document.getElementById('buyersSelect')?.value || '1';
        url = `/get_template_info?doc_type=SD&sellers=${sellers}&buyers=${buyers}&case_id=${CASE_ID}`;
    } else {
        const bank = document.getElementById('bankSelect')?.value;
        const borrowers = document.getElementById('borrowerSelect')?.value;
        const loans = document.getElementById('loanSelect')?.value;
        const properties = document.getElementById('propertiesSelect')?.value;
        if (!bank) {
            display.textContent = 'Select a bank to view template';
            return;
        }
        url = `/get_template_info?bank=${bank}&borrowers=${borrowers}&loans=${loans}&properties=${properties}&case_id=${CASE_ID}`;
    }

    fetch(url)
        .then(r => r.json())
        .then(resp => {
            if (resp.success) {
                display.textContent = `✓ Auto-Selected: ${resp.filename}`;
                display.classList.remove('text-danger', 'text-muted');
                display.classList.add('text-success');
            } else {
                display.textContent = `No template found for settings`;
                display.classList.remove('text-success', 'text-muted');
                display.classList.add('text-danger');
            }
        });
}

function clearTemplate() {
    document.getElementById('templateFile').value = '';
    fetch(`/case/${CASE_ID}/clear_custom_template`, {
        method: 'POST'
    })
    .then(r => r.json())
    .then(resp => {
        if (resp.success) {
            customTemplateFilename = '';
            updateTemplateDisplay();
        } else {
            alert('Failed to clear custom template: ' + resp.error);
        }
    })
    .catch(err => alert('Error clearing template: ' + err));
}

function selectDocTemplate(filename, label) {
    customTemplateFilename = filename;
    const labelSpan = document.getElementById('doc_template_label');
    if (labelSpan) {
        labelSpan.textContent = label;
    }
    
    // Highlight active item in the list
    const container = document.getElementById('doc_template_options_list');
    if (container) {
        container.querySelectorAll(".doc-template-option-btn").forEach(btn => {
            if (btn.getAttribute("data-filename") === filename) {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        });
    }
    
    // Show/hide clear custom button
    const clearBtn = document.getElementById('clearCustomTemplateBtn');
    if (clearBtn) {
        clearBtn.style.display = filename ? 'inline-block' : 'none';
    }

    // Save selection to backend
    saveCase();
    
    // Update display text
    updateTemplateDisplay();
}

function filterDocTemplateDropdown() {
    const searchInput = document.getElementById('doc_template_search_input');
    const listContainer = document.getElementById('doc_template_options_list');
    if (!searchInput || !listContainer) return;
    
    const query = searchInput.value.toLowerCase().trim();
    const options = listContainer.querySelectorAll(".doc-template-option-btn");
    
    // Clear keyboard highlight on filter
    options.forEach(opt => opt.classList.remove("highlighted-option"));
    
    options.forEach(opt => {
        const filename = opt.getAttribute("data-filename") || "";
        const text = opt.textContent.toLowerCase();
        if (!query || filename.toLowerCase().includes(query) || text.includes(query)) {
            opt.style.display = "block";
        } else {
            opt.style.display = "none";
        }
    });
}

function handleDocTemplateKeydown(e) {
    const listContainer = document.getElementById('doc_template_options_list');
    if (!listContainer) return;
    
    const visibleOptions = Array.from(listContainer.querySelectorAll(".doc-template-option-btn")).filter(opt => opt.style.display !== "none");
    if (visibleOptions.length === 0) return;
    
    let currentIdx = visibleOptions.findIndex(opt => opt.classList.contains("highlighted-option"));
    
    if (e.key === "ArrowDown") {
        e.preventDefault();
        if (currentIdx !== -1) {
            visibleOptions[currentIdx].classList.remove("highlighted-option");
        }
        currentIdx = (currentIdx + 1) % visibleOptions.length;
        const nextOpt = visibleOptions[currentIdx];
        nextOpt.classList.add("highlighted-option");
        nextOpt.scrollIntoView({ block: "nearest" });
    } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (currentIdx !== -1) {
            visibleOptions[currentIdx].classList.remove("highlighted-option");
        }
        currentIdx = (currentIdx - 1 + visibleOptions.length) % visibleOptions.length;
        const prevOpt = visibleOptions[currentIdx];
        prevOpt.classList.add("highlighted-option");
        prevOpt.scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter") {
        e.preventDefault();
        if (currentIdx !== -1) {
            visibleOptions[currentIdx].click();
        } else if (visibleOptions.length > 0) {
            visibleOptions[0].click();
        }
    } else if (e.key === "Escape") {
        const btnEl = document.getElementById('doc_template_btn');
        if (btnEl) {
            const dropdownInstance = bootstrap.Dropdown.getOrCreateInstance(btnEl);
            if (dropdownInstance) dropdownInstance.hide();
        }
    }
}

function handleDropdownKeydown(e, idx) {
    const listContainer = document.getElementById(`field_chain_${idx}_options_list`);
    if (!listContainer) return;
    
    const visibleOptions = Array.from(listContainer.querySelectorAll(".template-option-btn")).filter(opt => opt.style.display !== "none");
    if (visibleOptions.length === 0) return;
    
    let currentIdx = visibleOptions.findIndex(opt => opt.classList.contains("highlighted-option"));
    
    if (e.key === "ArrowDown") {
        e.preventDefault();
        if (currentIdx !== -1) {
            visibleOptions[currentIdx].classList.remove("highlighted-option");
        }
        currentIdx = (currentIdx + 1) % visibleOptions.length;
        const nextOpt = visibleOptions[currentIdx];
        nextOpt.classList.add("highlighted-option");
        nextOpt.scrollIntoView({ block: "nearest" });
    } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (currentIdx !== -1) {
            visibleOptions[currentIdx].classList.remove("highlighted-option");
        }
        currentIdx = (currentIdx - 1 + visibleOptions.length) % visibleOptions.length;
        const prevOpt = visibleOptions[currentIdx];
        prevOpt.classList.add("highlighted-option");
        prevOpt.scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter") {
        e.preventDefault();
        if (currentIdx !== -1) {
            visibleOptions[currentIdx].click();
        } else if (visibleOptions.length > 0) {
            visibleOptions[0].click();
        }
    } else if (e.key === "Escape") {
        const btnEl = document.getElementById(`field_chain_${idx}_event_type_btn`);
        if (btnEl) {
            const dropdownInstance = bootstrap.Dropdown.getOrCreateInstance(btnEl);
            if (dropdownInstance) dropdownInstance.hide();
        }
    }
}

function collectVerifiedFields() {
    return Array.from(document.querySelectorAll('.verify-check:checked'))
        .map(cb => cb.getAttribute('data-path'));
}

// --- Dynamic Grids Rows Add / Remove ---
function addPaymentRow() {
    const tbody = document.getElementById('paymentsTableBody');
    if (!tbody) return;
    const idx = tbody.children.length;
    const tr = document.createElement('tr');
    tr.id = `payment-row-${idx}`;
    tr.innerHTML = `
        <td><input class="form-control form-control-sm" id="field_payments_${idx}_a" placeholder="e.g. 5,00,000/-"></td>
        <td><input class="form-control form-control-sm" id="field_payments_${idx}_d" placeholder="e.g. 20.05.2026"></td>
        <td><input class="form-control form-control-sm" id="field_payments_${idx}_n" placeholder="Cheque / IMPS / UTR"></td>
        <td><input class="form-control form-control-sm" id="field_payments_${idx}_b" placeholder="Issuing Bank"></td>
        <td class="text-center"><button type="button" class="btn-icon-danger" onclick="removePaymentRow(${idx})" aria-label="Remove payment row" title="Remove payment row">✖</button></td>
    `;
    tbody.appendChild(tr);
}

function removePaymentRow(idx) {
    const row = document.getElementById(`payment-row-${idx}`);
    if (row) row.remove();
}

function convertHindiToEnglishDigits(str) {
    if (!str) return str;
    const hindiDigits = ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'];
    return str.replace(/[०-९]/g, function(match) {
        return hindiDigits.indexOf(match);
    });
}

function enforceEnglishDigits() {
    const workspace = document.getElementById('verificationContent');
    if (!workspace) return;
    const inputs = workspace.querySelectorAll('input, textarea');
    inputs.forEach(el => {
        if (el.value) {
            const converted = convertHindiToEnglishDigits(el.value);
            if (converted !== el.value) {
                el.value = converted;
            }
        }
    });
}
