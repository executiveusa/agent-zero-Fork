/**
 * Beads Timeline - Log visualization as "beads"
 */

export class BeadsTimeline {
    constructor(api, state) {
        this.api = api;
        this.state = state;
        this.container = document.getElementById('beads-container');
        this.filters = {
            type: 'all',
            search: '',
            hideTemp: false,
        };
        
        this.initFilters();
    }
    
    initFilters() {
        // Type filter chips
        const filterChips = document.querySelectorAll('.filter-chip[data-type]');
        filterChips.forEach(chip => {
            chip.addEventListener('click', () => {
                filterChips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                this.filters.type = chip.dataset.type;
                this.render();
            });
        });
        
        // Search input
        const searchInput = document.getElementById('timeline-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filters.search = e.target.value.toLowerCase();
                this.render();
            });
        }
        
        // Hide temporary toggle
        const hideTempCheckbox = document.getElementById('hide-temp-logs');
        if (hideTempCheckbox) {
            hideTempCheckbox.addEventListener('change', (e) => {
                this.filters.hideTemp = e.target.checked;
                this.render();
            });
        }
        
        // Export button
        const exportBtn = document.getElementById('timeline-export');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportTimeline());
        }
        
        // Jump to latest button
        const jumpBtn = document.getElementById('timeline-jump-latest');
        if (jumpBtn) {
            jumpBtn.addEventListener('click', () => this.jumpToLatest());
        }
    }
    
    update(logs) {
        this.logs = logs || [];
        this.render();
    }
    
    render() {
        if (!this.container) return;
        
        const filtered = this.filterLogs(this.logs || []);
        
        if (filtered.length === 0) {
            this.container.innerHTML = '<div class="no-beads">No logs to display</div>';
            return;
        }
        
        this.container.innerHTML = filtered.map((log, index) => this.renderBead(log, index)).join('');
    }
    
    filterLogs(logs) {
        return logs.filter(log => {
            // Type filter
            if (this.filters.type !== 'all' && log.type !== this.filters.type) {
                return false;
            }
            
            // Hide temporary
            if (this.filters.hideTemp && log.temp) {
                return false;
            }
            
            // Search filter
            if (this.filters.search) {
                const searchStr = `${log.heading} ${log.content}`.toLowerCase();
                if (!searchStr.includes(this.filters.search)) {
                    return false;
                }
            }
            
            return true;
        });
    }
    
    renderBead(log, index) {
        const typeColors = {
            error: 'var(--color-error)',
            warning: 'var(--color-waiting)',
            tool: 'var(--color-running)',
            code_exe: 'var(--color-running)',
            browser: 'var(--color-planning)',
            progress: 'var(--color-planning)',
            response: 'var(--color-idle)',
            agent: 'var(--accent-primary)',
            user: 'var(--text-muted)',
        };
        
        const color = typeColors[log.type] || 'var(--text-secondary)';
        const hasScreenshot = log.kvps && log.kvps.screenshot;
        
        return `
            <div class="bead-item bead-type-${log.type}" style="border-left-color: ${color};" data-log-id="${log.id || index}">
                <div class="bead-header">
                    <span class="bead-type" style="background: ${color};">${log.type}</span>
                    <span class="bead-heading">${this.escapeHtml(log.heading || 'No heading')}</span>
                    ${log.temp ? '<span class="bead-temp-badge">TEMP</span>' : ''}
                    ${hasScreenshot ? '<span class="bead-icon">📸</span>' : ''}
                </div>
                <div class="bead-content">
                    ${this.escapeHtml(log.content || '').substring(0, 200)}
                    ${(log.content || '').length > 200 ? '...' : ''}
                </div>
                ${log.kvps ? this.renderKvps(log.kvps) : ''}
            </div>
        `;
    }
    
    renderKvps(kvps) {
        const entries = Object.entries(kvps).slice(0, 5); // Limit to 5 kvps
        if (entries.length === 0) return '';
        
        return `
            <div class="bead-kvps">
                ${entries.map(([key, value]) => `
                    <div class="kvp-item">
                        <strong>${this.escapeHtml(key)}:</strong>
                        <span>${this.escapeHtml(String(value).substring(0, 100))}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    exportTimeline() {
        const data = JSON.stringify(this.logs, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `timeline-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    jumpToLatest() {
        if (this.container) {
            this.container.scrollTop = this.container.scrollHeight;
        }
    }
}

// Add CSS for beads
const style = document.createElement('style');
style.textContent = `
    .beads-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 16px;
        overflow-y: auto;
        max-height: calc(100vh - 300px);
    }
    
    .bead-item {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-left: 4px solid;
        border-radius: 6px;
        padding: 12px;
        transition: all 0.2s;
    }
    
    .bead-item:hover {
        background: var(--bg-tertiary);
        box-shadow: var(--shadow-sm);
    }
    
    .bead-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }
    
    .bead-type {
        font-size: 10px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        color: white;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .bead-heading {
        font-weight: 600;
        flex: 1;
    }
    
    .bead-temp-badge {
        font-size: 10px;
        background: var(--bg-tertiary);
        color: var(--text-muted);
        padding: 2px 6px;
        border-radius: 4px;
    }
    
    .bead-icon {
        font-size: 16px;
    }
    
    .bead-content {
        color: var(--text-secondary);
        font-size: 13px;
        line-height: 1.5;
    }
    
    .bead-kvps {
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid var(--border-color);
        font-size: 12px;
    }
    
    .kvp-item {
        display: flex;
        gap: 6px;
        margin-bottom: 4px;
    }
    
    .kvp-item strong {
        color: var(--text-secondary);
        min-width: 80px;
    }
    
    .no-beads {
        text-align: center;
        color: var(--text-muted);
        padding: 40px;
    }
`;
document.head.appendChild(style);
