// Audiogram Interpreter - Frontend Logic

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const previewContainer = document.getElementById('preview-container');
const previewImage = document.getElementById('preview-image');
const clearBtn = document.getElementById('clear-btn');
const analyzeBtn = document.getElementById('analyze-btn');
const uploadSection = document.getElementById('upload-section');
const loading = document.getElementById('loading');
const errorBanner = document.getElementById('error-banner');
const results = document.getElementById('results');

let selectedFile = null;

// Drag and drop
dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
});

dropzone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
});

clearBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    previewContainer.hidden = true;
    dropzone.hidden = false;
    analyzeBtn.disabled = true;
    results.hidden = true;
    errorBanner.hidden = true;
});

analyzeBtn.addEventListener('click', analyze);

function handleFile(file) {
    const validTypes = ['image/jpeg', 'image/png', 'image/bmp', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        showError('Unsupported file type. Please upload a JPG, PNG, BMP, or WebP image.');
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        showError('File too large. Maximum size is 10 MB.');
        return;
    }

    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        previewContainer.hidden = false;
        dropzone.hidden = true;
        analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

async function analyze() {
    if (!selectedFile) return;

    loading.hidden = false;
    results.hidden = true;
    errorBanner.hidden = true;
    analyzeBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            showError(data.error || 'Analysis failed');
            return;
        }

        renderResults(data);
    } catch (err) {
        showError('Network error: ' + err.message);
    } finally {
        loading.hidden = true;
        analyzeBtn.disabled = false;
    }
}

function showError(msg) {
    errorBanner.textContent = msg;
    errorBanner.hidden = false;
}

function renderResults(data) {
    results.hidden = false;

    // Confidence badge
    const badge = document.getElementById('confidence-badge');
    const conf = data.extraction_confidence || 'medium';
    badge.textContent = `Extraction confidence: ${conf}`;
    badge.className = `confidence-badge confidence-${conf}`;

    // Ear cards
    renderEarCard('right', data.right);
    renderEarCard('left', data.left);

    // Threshold table
    renderThresholdTable(data);

    // Diagnoses
    renderDiagnoses(data.diagnoses);

    // Masking warnings
    const allMaskingErrors = [
        ...(data.right.masking_errors || []),
        ...(data.left.masking_errors || []),
    ];
    const maskingSection = document.getElementById('masking-section');
    const maskingList = document.getElementById('masking-warnings');
    if (allMaskingErrors.length > 0) {
        // Deduplicate
        const unique = [...new Set(allMaskingErrors)];
        maskingList.innerHTML = unique.map(e => `<li>${escapeHtml(e)}</li>`).join('');
        maskingSection.hidden = false;
    } else {
        maskingSection.hidden = true;
    }

    // Bilateral notes
    const bilateralSection = document.getElementById('bilateral-section');
    const bilateralList = document.getElementById('bilateral-notes');
    if (data.bilateral_notes && data.bilateral_notes.length > 0) {
        bilateralList.innerHTML = data.bilateral_notes.map(n => `<li>${escapeHtml(n)}</li>`).join('');
        bilateralSection.hidden = false;
    } else {
        bilateralSection.hidden = true;
    }

    // Extraction notes
    const extractionSection = document.getElementById('extraction-section');
    const extractionList = document.getElementById('extraction-notes');
    if (data.extraction_notes && data.extraction_notes.length > 0) {
        extractionList.innerHTML = data.extraction_notes.map(n => `<li>${escapeHtml(n)}</li>`).join('');
        extractionSection.hidden = false;
    } else {
        extractionSection.hidden = true;
    }
}

function renderEarCard(side, ear) {
    document.getElementById(`${side}-fh`).textContent = ear.fh != null ? ear.fh.toFixed(1) : '-';
    document.getElementById(`${side}-fhi`).textContent = ear.fhi != null ? ear.fhi.toFixed(1) : '-';
    document.getElementById(`${side}-degree`).textContent = ear.degree || '-';
    document.getElementById(`${side}-type`).textContent = ear.loss_type || '-';
    document.getElementById(`${side}-config`).textContent = ear.configuration || '-';

    // Speech results
    const speechDiv = document.getElementById(`${side}-speech`);
    let speechHtml = '';

    if (ear.srt != null) {
        speechHtml += `<div class="speech-item"><span>SRT</span><span>${ear.srt} dB</span></div>`;
    }
    if (ear.max_discrimination != null) {
        speechHtml += `<div class="speech-item"><span>Max discrimination</span><span>${ear.max_discrimination}%</span></div>`;
    }
    if (ear.srt_fh_concordance) {
        const icon = ear.srt_fh_concordance === 'concordant' ? '&#10003;' : '&#9888;';
        speechHtml += `<div class="speech-item"><span>SRT-FH concordance</span><span>${icon} ${ear.srt_fh_concordance}</span></div>`;
    }
    if (ear.discrimination_rating) {
        speechHtml += `<div class="speech-item"><span>Discrimination</span><span>${ear.discrimination_rating}</span></div>`;
    }
    if (ear.rollover_index != null) {
        speechHtml += `<div class="speech-item"><span>Rollover index</span><span>${ear.rollover_index.toFixed(2)}</span></div>`;
    }

    speechDiv.innerHTML = speechHtml || '<div class="speech-item" style="color:var(--text-light)">No speech data</div>';
}

function renderThresholdTable(data) {
    const freqs = ['250', '500', '1000', '2000', '4000', '8000'];
    const tbody = document.getElementById('threshold-tbody');

    const rows = [
        { label: 'Right AC', side: 'right', key: 'ac_thresholds', cls: 'right-row' },
        { label: 'Right BC', side: 'right', key: 'bc_thresholds', cls: 'right-row' },
        { label: 'Right ABG', side: 'right', key: 'air_bone_gaps', cls: 'right-row gap-row' },
        { label: 'Left AC', side: 'left', key: 'ac_thresholds', cls: 'left-row' },
        { label: 'Left BC', side: 'left', key: 'bc_thresholds', cls: 'left-row' },
        { label: 'Left ABG', side: 'left', key: 'air_bone_gaps', cls: 'left-row gap-row' },
    ];

    let html = '';
    for (const row of rows) {
        const earData = data[row.side];
        const thresholds = earData[row.key] || {};
        html += `<tr class="${row.cls}"><td>${row.label}</td>`;
        for (const f of freqs) {
            const val = thresholds[f];
            html += `<td>${val != null ? val : '-'}</td>`;
        }
        html += '</tr>';
    }

    tbody.innerHTML = html;
}

function renderDiagnoses(diagnoses) {
    const list = document.getElementById('diagnoses-list');
    if (!diagnoses || diagnoses.length === 0) {
        list.innerHTML = '<p style="color:var(--text-light);font-size:0.9rem">No specific diagnoses could be determined from the available data.</p>';
        return;
    }

    const labels = ['Most likely', '2nd', '3rd'];
    list.innerHTML = diagnoses.map((d, i) => `
        <div class="diagnosis-card">
            <div class="diag-rank">${labels[i] || `#${i + 1}`}</div>
            <div class="diag-name">${escapeHtml(d.name)}</div>
            <div class="diag-reasoning">${escapeHtml(d.reasoning)}</div>
            <span class="diag-confidence conf-${d.confidence}">${d.confidence} confidence</span>
        </div>
    `).join('');
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
