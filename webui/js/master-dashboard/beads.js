/**
 * Beads Timeline - Log visualization as "beads"
 * Enhanced with persistent memory beads for project context tracking.
 */

// Persistent memory store - survives page reloads via localStorage
const MEMORY_KEY = 'agent_zero_beads_memory';

export class BeadsMemory {
    constructor() {
        this.memories = this._load();
    }

    _load() {
        try {
            return JSON.parse(localStorage.getItem(MEMORY_KEY) || '[]');
        } catch { return []; }
    }

    _save() {
        localStorage.setItem(MEMORY_KEY, JSON.stringify(this.memories));
    }

    /** Store a context bead - persists across sessions */
    store(category, title, data) {
        const bead = {
            id: `mem_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
            category,          // e.g. 'model_providers', 'deployment', 'swarm', 'schedule'
            title,
            data,
            timestamp: new Date().toISOString(),
            pinned: false,
        };
        this.memories.push(bead);
        this._save();
        return bead;
    }

    /** Update an existing memory bead by id */
    update(id, updates) {
        const idx = this.memories.findIndex(m => m.id === id);
        if (idx >= 0) {
            Object.assign(this.memories[idx], updates, { updated: new Date().toISOString() });
            this._save();
            return this.memories[idx];
        }
        return null;
    }

    /** Remove a memory bead */
    remove(id) {
        this.memories = this.memories.filter(m => m.id !== id);
        this._save();
    }

    /** Get all memory beads, optionally filtered by category */
    get(category = null) {
        if (!category) return [...this.memories];
        return this.memories.filter(m => m.category === category);
    }

    /** Pin / unpin a memory bead */
    togglePin(id) {
        const mem = this.memories.find(m => m.id === id);
        if (mem) { mem.pinned = !mem.pinned; this._save(); }
        return mem;
    }

    /** Clear all memory beads (or by category) */
    clear(category = null) {
        if (!category) { this.memories = []; }
        else { this.memories = this.memories.filter(m => m.category !== category); }
        this._save();
    }

    /** Export all memory beads as JSON */
    export() {
        return JSON.stringify(this.memories, null, 2);
    }

    /** Import memory beads from JSON (merges) */
    import(json) {
        try {
            const imported = JSON.parse(json);
            if (Array.isArray(imported)) {
                const existingIds = new Set(this.memories.map(m => m.id));
                for (const m of imported) {
                    if (!existingIds.has(m.id)) this.memories.push(m);
                }
                this._save();
            }
        } catch (e) { console.error('BeadsMemory import failed:', e); }
    }
}

export class BeadsTimeline {
    constructor(api, state) {
        this.api = api;
        this.state = state;
        this.container = document.getElementById('beads-container');
        this.memory = new BeadsMemory();
        this.filters = {
            type: 'all',
            search: '',
            hideTemp: false,
        };

        this.initFilters();
        this._seedProjectContext();
    }
    
    /** Seed persistent project context if not already present */
    _seedProjectContext() {
        const existing = this.memory.get('project_context');
        if (existing.length === 0) {
            this.memory.store('project_context', 'Autonomous Agent Swarm', {
                phase: 'Implementation',
                models: ['Kimi K2 (moonshot)', 'GLM-4.7 (zhipu)', 'Gemini 2.5 Pro (google)', 'Claude (anthropic)', 'GPT-4o (openai)'],
                integrations: ['ZenFlow IDE', 'Google AI Studio', 'GitHub Pipeline', 'Telegram Command Center'],
                capabilities: ['Model Router', 'Agent Swarms', 'Scheduled Tasks', 'Self-Improvement Loop'],
                deployment: { vercel: 'prj_M2GbBvi8XMtxISpPrBFoidOVWzHs', url: 'https://agent-zero-fork.vercel.app' },
                status: 'Phase 1 - Adding model providers',
            });
            this.memory.store('model_providers', 'Model Provider Registry', {
                moonshot: { name: 'Moonshot/Kimi', api: 'https://api.moonshot.ai/v1', models: ['kimi-k2-turbo-preview', 'kimi-k2.5', 'kimi-k2-thinking'] },
                zhipu: { name: 'Zhipu AI/GLM', api: 'https://open.bigmodel.cn/api/paas/v4', models: ['glm-4-plus', 'glm-4-flash'] },
                google: { name: 'Google Gemini', models: ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-3-flash-preview'] },
            });
            this.memory.store('swarm_config', 'Agent Swarm Configuration', {
                profiles: ['developer', 'researcher', 'hacker', 'cloud-coding', 'zenflow-coder', 'aistudio-coder', 'project-finisher'],
                router_rules: { code: 'kimi-k2', reasoning: 'kimi-k2-thinking', vision: 'gemini-2.5-pro', fast: 'glm-4-flash' },
                telegram_commands: ['/swarm', '/model', '/repos', '/finish', '/schedule', '/status'],
            });
        }
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
        
        // Render pinned memory beads at top, then regular beads
        const memoryBeads = this.memory.get().filter(m => m.pinned || this.filters.type === 'all' || this.filters.type === 'memory');
        const memoryHtml = memoryBeads.map(m => this.renderMemoryBead(m)).join('');
        
        if (filtered.length === 0 && memoryBeads.length === 0) {
            this.container.innerHTML = '<div class="no-beads">No logs to display</div>';
            return;
        }
        
        this.container.innerHTML = memoryHtml + filtered.map((log, index) => this.renderBead(log, index)).join('');
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

    renderMemoryBead(mem) {
        const catColors = {
            project_context: 'var(--accent-primary)',
            model_providers: 'var(--color-running)',
            swarm_config: 'var(--color-planning)',
            deployment: 'var(--color-idle)',
            schedule: 'var(--color-waiting)',
        };
        const color = catColors[mem.category] || 'var(--text-secondary)';
        const dataEntries = Object.entries(mem.data || {}).slice(0, 6);
        const pinIcon = mem.pinned ? '📌' : '📎';
        const age = this._timeAgo(mem.timestamp);

        return `
            <div class="bead-item bead-type-memory" style="border-left-color: ${color}; background: var(--bg-tertiary);" data-mem-id="${mem.id}">
                <div class="bead-header">
                    <span class="bead-type" style="background: ${color};">MEMORY</span>
                    <span class="bead-heading">${pinIcon} ${this.escapeHtml(mem.title)}</span>
                    <span class="bead-temp-badge">${this.escapeHtml(mem.category)}</span>
                    <span class="bead-temp-badge">${age}</span>
                </div>
                <div class="bead-kvps">
                    ${dataEntries.map(([key, value]) => `
                        <div class="kvp-item">
                            <strong>${this.escapeHtml(key)}:</strong>
                            <span>${this.escapeHtml(this._formatValue(value))}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    _formatValue(val) {
        if (Array.isArray(val)) return val.join(', ');
        if (typeof val === 'object' && val !== null) return JSON.stringify(val).substring(0, 120);
        return String(val).substring(0, 120);
    }

    _timeAgo(isoStr) {
        const diff = Date.now() - new Date(isoStr).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1) return 'just now';
        if (mins < 60) return `${mins}m ago`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return `${hrs}h ago`;
        return `${Math.floor(hrs / 24)}d ago`;
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
