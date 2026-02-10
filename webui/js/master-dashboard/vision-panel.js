/**
 * Vision Panel — Image upload, analysis, and history
 * Sends images to /vision_analyze for GPT-4o vision analysis
 */

export class VisionPanel {
    constructor(api, toast) {
        this.api = api;
        this.toast = toast;
        this.currentFile = null;
        this.currentBase64 = null;
        this.currentMimeType = null;
        this.history = [];
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        const dropzone = document.getElementById('vision-dropzone');
        const fileInput = document.getElementById('vision-file-input');
        const analyzeBtn = document.getElementById('vision-analyze-btn');
        const clearBtn = document.getElementById('vision-clear-btn');

        if (dropzone) {
            dropzone.addEventListener('click', () => fileInput?.click());
            dropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropzone.classList.add('drag-over');
            });
            dropzone.addEventListener('dragleave', () => {
                dropzone.classList.remove('drag-over');
            });
            dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropzone.classList.remove('drag-over');
                const files = e.dataTransfer?.files;
                if (files?.length) this.loadFile(files[0]);
            });
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files?.length) this.loadFile(e.target.files[0]);
            });
        }

        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.analyze());
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearImage());
        }

        // Also allow paste from clipboard
        document.addEventListener('paste', (e) => {
            // Only handle if vision panel is active
            const panel = document.getElementById('panel-vision');
            if (!panel?.classList.contains('active')) return;

            const items = e.clipboardData?.items || [];
            for (const item of items) {
                if (item.type.startsWith('image/')) {
                    const blob = item.getAsFile();
                    if (blob) this.loadFile(blob);
                    break;
                }
            }
        });
    }

    loadFile(file) {
        if (!file.type.startsWith('image/')) {
            this.toast?.error('Please upload an image file');
            return;
        }
        if (file.size > 20 * 1024 * 1024) {
            this.toast?.error('Image must be under 20 MB');
            return;
        }

        this.currentFile = file;
        this.currentMimeType = file.type;

        const reader = new FileReader();
        reader.onload = (e) => {
            const dataUrl = e.target.result;
            this.currentBase64 = dataUrl.split(',')[1];

            // Show preview
            const previewContainer = document.getElementById('vision-preview-container');
            const previewImg = document.getElementById('vision-preview-img');
            const dropzone = document.getElementById('vision-dropzone');

            if (previewImg) previewImg.src = dataUrl;
            if (previewContainer) previewContainer.style.display = 'block';
            if (dropzone) dropzone.style.display = 'none';

            // Enable analyze button
            const btn = document.getElementById('vision-analyze-btn');
            if (btn) btn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    clearImage() {
        this.currentFile = null;
        this.currentBase64 = null;
        this.currentMimeType = null;

        const previewContainer = document.getElementById('vision-preview-container');
        const dropzone = document.getElementById('vision-dropzone');
        const btn = document.getElementById('vision-analyze-btn');
        const result = document.getElementById('vision-result');

        if (previewContainer) previewContainer.style.display = 'none';
        if (dropzone) dropzone.style.display = 'block';
        if (btn) btn.disabled = true;
        if (result) result.style.display = 'none';
    }

    async analyze() {
        if (!this.currentFile) {
            this.toast?.warning('No image loaded');
            return;
        }

        const prompt = document.getElementById('vision-prompt-input')?.value?.trim()
            || 'Describe what you see in this image in detail.';
        const analyzeBtn = document.getElementById('vision-analyze-btn');
        const resultDiv = document.getElementById('vision-result');
        const resultContent = document.getElementById('vision-result-content');
        const modelUsed = document.getElementById('vision-model-used');

        if (analyzeBtn) {
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = '⏳ Analyzing...';
        }

        try {
            // Use FormData for multipart upload
            const formData = new FormData();
            formData.append('image', this.currentFile);
            formData.append('prompt', prompt);

            const response = await fetch('/vision_analyze', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (data.error) {
                this.toast?.error(data.error);
                if (resultContent) resultContent.textContent = `Error: ${data.error}`;
            } else {
                if (resultContent) resultContent.innerHTML = this.formatMarkdown(data.analysis);
                if (modelUsed) modelUsed.textContent = `Model: ${data.model}`;
                this.toast?.success('Image analyzed successfully');

                // Add to history
                this.addToHistory({
                    prompt,
                    analysis: data.analysis,
                    model: data.model,
                    timestamp: new Date().toLocaleString(),
                    thumbnail: document.getElementById('vision-preview-img')?.src || '',
                });
            }

            if (resultDiv) resultDiv.style.display = 'block';
        } catch (err) {
            this.toast?.error(`Analysis failed: ${err.message}`);
        } finally {
            if (analyzeBtn) {
                analyzeBtn.disabled = false;
                analyzeBtn.textContent = '🔍 Analyze';
            }
        }
    }

    addToHistory(entry) {
        this.history.unshift(entry);
        if (this.history.length > 20) this.history.pop();
        this.renderHistory();
    }

    renderHistory() {
        const list = document.getElementById('vision-history-list');
        if (!list) return;

        if (this.history.length === 0) {
            list.innerHTML = '<div class="text-muted">No analyses yet</div>';
            return;
        }

        list.innerHTML = this.history.map((h, i) => `
            <div class="vision-history-item" data-index="${i}">
                <div class="vision-history-thumb">
                    ${h.thumbnail ? `<img src="${h.thumbnail}" alt="thumb">` : '<span>🖼️</span>'}
                </div>
                <div class="vision-history-info">
                    <div class="vision-history-prompt">${this.esc(h.prompt.substring(0, 80))}${h.prompt.length > 80 ? '...' : ''}</div>
                    <div class="vision-history-meta">${h.timestamp} · ${h.model}</div>
                    <div class="vision-history-excerpt">${this.esc(h.analysis.substring(0, 120))}...</div>
                </div>
            </div>
        `).join('');
    }

    formatMarkdown(text) {
        // Basic markdown formatting
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    esc(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
}
