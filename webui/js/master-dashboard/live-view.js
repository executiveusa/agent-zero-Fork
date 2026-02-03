/**
 * Live View - Agent browser automation observation
 * Displays screenshots and narrated steps
 */

export class LiveView {
    constructor(api, state) {
        this.api = api;
        this.state = state;
        this.screenshotViewer = document.getElementById('screenshot-viewer');
        this.stepNarration = document.getElementById('step-narration');
        this.currentToolCard = document.getElementById('current-tool-card');
        this.blockersCard = document.getElementById('blockers-card');
        this.toolOutputViewer = document.getElementById('tool-output-viewer');
        
        this.currentScreenshot = null;
        this.autoRefresh = true;
        
        this.initControls();
    }
    
    initControls() {
        // Auto refresh toggle
        const autoRefreshCheckbox = document.getElementById('auto-refresh-screenshots');
        if (autoRefreshCheckbox) {
            autoRefreshCheckbox.addEventListener('change', (e) => {
                this.autoRefresh = e.target.checked;
            });
        }
        
        // Pin screenshot button
        const pinBtn = document.getElementById('pin-screenshot');
        if (pinBtn) {
            pinBtn.addEventListener('click', () => this.pinScreenshot());
        }
        
        // Download screenshot button
        const downloadBtn = document.getElementById('download-screenshot');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadScreenshot());
        }
    }
    
    update(logs, progress) {
        // Update screenshot display
        if (this.autoRefresh) {
            this.updateScreenshot(logs);
        }
        
        // Update step narration
        this.updateStepNarration(logs, progress);
        
        // Update current tool
        this.updateCurrentTool(logs);
        
        // Update blockers
        this.updateBlockers(logs);
        
        // Update tool output
        this.updateToolOutput(logs);
    }
    
    updateScreenshot(logs) {
        // Find most recent log with screenshot
        const screenshotLog = [...logs].reverse().find(log => 
            log.kvps && log.kvps.screenshot
        );
        
        if (screenshotLog && screenshotLog.kvps.screenshot) {
            const screenshot = screenshotLog.kvps.screenshot;
            
            // Parse img:// format: img://<abs_path>&t=<timestamp>
            const match = screenshot.match(/img:\/\/([^&]+)(?:&t=(.+))?/);
            if (match) {
                const path = match[1];
                const imageUrl = this.api.getImageUrl(path);
                
                if (this.currentScreenshot !== imageUrl) {
                    this.currentScreenshot = imageUrl;
                    this.renderScreenshot(imageUrl, screenshotLog.heading);
                }
            }
        }
    }
    
    renderScreenshot(imageUrl, caption) {
        if (!this.screenshotViewer) return;
        
        this.screenshotViewer.innerHTML = `
            <div class="screenshot-container">
                <img src="${imageUrl}" alt="Agent Screenshot" class="screenshot-image" />
                <div class="screenshot-caption">${this.escapeHtml(caption || 'Agent View')}</div>
            </div>
        `;
    }
    
    updateStepNarration(logs, progress) {
        if (!this.stepNarration) return;
        
        // Get browser, progress, and agent logs
        const relevantLogs = logs
            .filter(log => ['browser', 'progress', 'agent'].includes(log.type))
            .slice(-10)
            .reverse();
        
        if (relevantLogs.length === 0) {
            this.stepNarration.innerHTML = '<div class="no-narration">No agent activity</div>';
            return;
        }
        
        this.stepNarration.innerHTML = relevantLogs.map(log => `
            <div class="narration-step">
                <div class="narration-icon">${this.getTypeIcon(log.type)}</div>
                <div class="narration-content">
                    <div class="narration-heading">${this.escapeHtml(log.heading)}</div>
                    ${log.content ? `<div class="narration-detail">${this.escapeHtml(log.content.substring(0, 100))}</div>` : ''}
                </div>
            </div>
        `).join('');
    }
    
    updateCurrentTool(logs) {
        if (!this.currentToolCard) return;
        
        // Find most recent tool execution
        const toolLog = [...logs].reverse().find(log => log.type === 'tool' || log.type === 'code_exe');
        
        if (toolLog) {
            this.currentToolCard.innerHTML = `
                <div class="tool-name">${this.escapeHtml(toolLog.heading)}</div>
                <div class="tool-type">${toolLog.type === 'code_exe' ? '💻 Code Execution' : '🔧 Tool Call'}</div>
                ${toolLog.kvps ? this.renderToolArgs(toolLog.kvps) : ''}
            `;
        } else {
            this.currentToolCard.innerHTML = '<div class="no-tool">No active tool</div>';
        }
    }
    
    updateBlockers(logs) {
        if (!this.blockersCard) return;
        
        // Find recent errors and warnings
        const blockers = logs
            .filter(log => log.type === 'error' || log.type === 'warning')
            .slice(-3)
            .reverse();
        
        if (blockers.length === 0) {
            this.blockersCard.innerHTML = '<div class="no-blockers">✅ No blockers</div>';
            return;
        }
        
        this.blockersCard.innerHTML = blockers.map(blocker => `
            <div class="blocker-item blocker-${blocker.type}">
                <div class="blocker-heading">${this.escapeHtml(blocker.heading)}</div>
                <div class="blocker-content">${this.escapeHtml(blocker.content?.substring(0, 150) || '')}</div>
            </div>
        `).join('');
    }
    
    updateToolOutput(logs) {
        if (!this.toolOutputViewer) return;
        
        // Find most recent tool/code execution with output
        const outputLog = [...logs].reverse().find(log => 
            (log.type === 'tool' || log.type === 'code_exe') && log.content
        );
        
        if (outputLog) {
            this.toolOutputViewer.innerHTML = `
                <div class="output-header">${this.escapeHtml(outputLog.heading)}</div>
                <pre class="output-content">${this.escapeHtml(outputLog.content.substring(0, 500))}</pre>
            `;
        } else {
            this.toolOutputViewer.innerHTML = '';
        }
    }
    
    renderToolArgs(kvps) {
        const entries = Object.entries(kvps).slice(0, 3);
        if (entries.length === 0) return '';
        
        return `
            <div class="tool-args">
                ${entries.map(([key, value]) => `
                    <div><strong>${this.escapeHtml(key)}:</strong> ${this.redactValue(value)}</div>
                `).join('')}
            </div>
        `;
    }
    
    redactValue(value) {
        const str = String(value);
        // Redact potential secrets
        if (str.length > 50 || /token|key|password|secret/i.test(String(value))) {
            return '<span class="redacted">[REDACTED]</span>';
        }
        return this.escapeHtml(str.substring(0, 100));
    }
    
    getTypeIcon(type) {
        const icons = {
            browser: '🌐',
            progress: '⚡',
            agent: '🤖',
            tool: '🔧',
            code_exe: '💻',
        };
        return icons[type] || '📌';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    pinScreenshot() {
        this.autoRefresh = false;
        document.getElementById('auto-refresh-screenshots').checked = false;
        alert('Screenshot pinned. Disable auto-refresh to keep viewing this screenshot.');
    }
    
    downloadScreenshot() {
        if (this.currentScreenshot) {
            window.open(this.currentScreenshot, '_blank');
        }
    }
}

// Add CSS for live view
const style = document.createElement('style');
style.textContent = `
    .screenshot-container {
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .screenshot-image {
        flex: 1;
        width: 100%;
        height: 100%;
        object-fit: contain;
        background: #000;
    }
    
    .screenshot-caption {
        padding: 8px;
        background: var(--bg-tertiary);
        font-size: 12px;
        text-align: center;
        border-top: 1px solid var(--border-color);
    }
    
    .narration-step {
        display: flex;
        gap: 12px;
        padding: 12px;
        border-bottom: 1px solid var(--border-color);
    }
    
    .narration-icon {
        font-size: 20px;
    }
    
    .narration-content {
        flex: 1;
    }
    
    .narration-heading {
        font-weight: 600;
        margin-bottom: 4px;
    }
    
    .narration-detail {
        font-size: 12px;
        color: var(--text-secondary);
    }
    
    .tool-name {
        font-weight: 600;
        font-size: 16px;
        margin-bottom: 8px;
    }
    
    .tool-type {
        font-size: 12px;
        color: var(--text-secondary);
        margin-bottom: 12px;
    }
    
    .tool-args {
        font-size: 12px;
        padding: 8px;
        background: var(--bg-tertiary);
        border-radius: 4px;
    }
    
    .tool-args div {
        margin-bottom: 4px;
    }
    
    .redacted {
        color: var(--color-error);
        font-style: italic;
    }
    
    .blocker-item {
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
    
    .blocker-error {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid var(--color-error);
    }
    
    .blocker-warning {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid var(--color-waiting);
    }
    
    .blocker-heading {
        font-weight: 600;
        margin-bottom: 6px;
    }
    
    .blocker-content {
        font-size: 12px;
        color: var(--text-secondary);
    }
    
    .output-header {
        font-weight: 600;
        margin-bottom: 8px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border-color);
    }
    
    .output-content {
        font-family: var(--font-mono);
        font-size: 11px;
        white-space: pre-wrap;
        color: var(--text-secondary);
        margin: 0;
    }
    
    .no-narration, .no-tool, .no-blockers {
        text-align: center;
        color: var(--text-muted);
        padding: 20px;
    }
`;
document.head.appendChild(style);
