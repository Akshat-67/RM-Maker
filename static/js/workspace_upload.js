// Workspace Upload Event Handlers

function setupDropZone() {
    // Prevent default drag behaviors globally to stop browser from opening files
    window.addEventListener("dragover", function(e) {
        e.preventDefault();
    }, false);
    window.addEventListener("drop", function(e) {
        e.preventDefault();
    }, false);

    const zones = document.querySelectorAll('.drop-zone');
    zones.forEach(zone => {
        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(evt => {
            zone.addEventListener(evt, e => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(evt => {
            zone.addEventListener(evt, e => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.remove('dragover');
            }, false);
        });

        // Handle dropped files
        zone.addEventListener('drop', e => {
            e.preventDefault();
            e.stopPropagation();
            const files = e.dataTransfer.files;
            if (!files.length) return;

            const input = zone.querySelector('input[type="file"]');
            if (input) {
                const id = input.id;
                if (id === 'kycFiles') {
                    uploadBucketFiles(files, 'kyc');
                } else if (id === 'legalFiles') {
                    uploadBucketFiles(files, 'legal');
                } else if (id === 'atsFiles') {
                    uploadBucketFiles(files, 'ats');
                } else if (id === 'titleFiles') {
                    uploadBucketFiles(files, 'title_chain');
                } else if (id === 'ocrFiles') {
                    uploadBucketFiles(files, 'ocr');
                } else if (id === 'docFiles') {
                    uploadFiles(files);
                }
            }
        }, false);
    });
}

function handleBucketFileSelect(input, bucket) {
    if (input.files.length) uploadBucketFiles(input.files, bucket);
}

function uploadBucketFiles(files, bucket) {
    const formData = new FormData();
    for (let f of files) {
        formData.append('files', f);
    }

    document.getElementById('statusMsg').textContent = 'Uploading files to ' + bucket + '...';

    fetch(`/case/${CASE_ID}/upload_bucket/${bucket}`, {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(resp => {
        if (resp.success) {
            let listId = '';
            if (bucket === 'kyc') listId = 'kycFileList';
            else if (bucket === 'legal') listId = 'legalFileList';
            else if (bucket === 'ats') listId = 'atsFileList';
            else if (bucket === 'title_chain') listId = 'titleFileList';
            else if (bucket === 'ocr') listId = 'ocrFileList';

            const list = document.getElementById(listId);
            if (list) {
                resp.new_files.forEach(name => {
                    const filename = name.split('/').pop().split('\\').pop();
                    
                    // Create uploader list item
                    const div = document.createElement('div');
                    div.className = "d-flex justify-content-between align-items-center bg-light rounded px-1.5 py-0.5 mb-1";
                    div.style.fontSize = "0.62rem";
                    div.style.lineHeight = "1";
                    
                    const span = document.createElement('span');
                    span.className = "text-truncate";
                    span.style.maxWidth = "80%";
                    span.style.cursor = "pointer";
                    span.textContent = filename;
                    span.onclick = () => previewFile(filename);
                    span.title = "Click to Preview";
                    
                    const closeSpan = document.createElement('span');
                    closeSpan.className = "cursor-pointer text-danger fw-bold ms-1";
                    closeSpan.textContent = "×";
                    closeSpan.onclick = () => deleteFile(filename, bucket);
                    
                    div.appendChild(span);
                    div.appendChild(closeSpan);
                    list.appendChild(div);

                    // Add to preview container
                    const previewContainer = document.querySelector('.preview-scroll-container');
                    if (previewContainer) {
                        const safeId = 'file-tab-' + filename.replace(/\./g, '_');
                        if (!document.getElementById(safeId)) {
                            const btn = document.createElement('button');
                            btn.className = "btn btn-outline-secondary btn-sm me-1 file-preview-btn text-truncate";
                            btn.id = safeId;
                            btn.style.maxWidth = "140px";
                            btn.style.fontSize = "0.7rem";
                            btn.style.padding = "0.2rem 0.5rem";
                            btn.title = filename;
                            btn.onclick = () => previewFile(filename);
                            btn.innerHTML = `📄 ${filename}`;
                            previewContainer.appendChild(btn);
                        }
                    }
                });
            }
            // Enable corresponding Extract button dynamically
            const extBtn = document.getElementById(`extractBtn_${bucket}`);
            if (extBtn) {
                extBtn.disabled = false;
                extBtn.removeAttribute('title');
            }
            document.getElementById('statusMsg').textContent = 'Files uploaded successfully to ' + bucket + '.';
        } else {
            alert('Upload failed: ' + resp.error);
        }
    })
    .catch(e => alert('Upload error: ' + e));
}

function handleFileSelect(input) {
    if (input.files.length) uploadFiles(input.files);
}

function uploadFiles(files) {
    const formData = new FormData();
    for (let f of files) {
        formData.append('files', f);
    }

    document.getElementById('statusMsg').textContent = 'Uploading files...';
    
    fetch(`/case/${CASE_ID}/upload_files`, {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(resp => {
        if (resp.success) {
            document.getElementById('statusMsg').textContent = 'Files uploaded successfully.';
            setTimeout(() => location.reload(), 300);
        } else {
            alert('Upload failed: ' + resp.error);
        }
    })
    .catch(e => alert('Upload error: ' + e));
}
