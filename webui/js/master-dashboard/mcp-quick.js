/**
 * MCP Quick-Access Panel — One-click MCP server management
 */
export class MCPQuickAccess {
    constructor(api, toast) {
        this.api = api;
        this.toast = toast;
        this.servers = [];
    }

    init() {
        this._bindButtons();
    }

    _bindButtons() {
        const refreshBtn = document.getElementById('mcp-quick-refresh');
        if (refreshBtn) refreshBtn.addEventListener('click', () => this.refresh());

        const applyBtn = document.getElementById('mcp-quick-apply');
        if (applyBtn) applyBtn.addEventListener('click', () => this.applyConfig());
    }

    async refresh() {
        try {
            const result = await this.api.get('/mcp_servers_status');
            if (result && result.servers) {
                this.servers = result.servers;
                this.render();
            }
        } catch (err) {
            this.toast.error('Failed to load MCP servers');
        }
    }

    render() {
        const container = document.getElementById('mcp-quick-grid');
        if (!container) return;

        if (this.servers.length === 0) {
            container.innerHTML = '<div class="text-muted">No MCP servers configured. Click Refresh.</div>';
            return;
        }

        container.innerHTML = this.servers.map(s => `
            <div class="mcp-server-card ${s.status === 'running' ? 'active' : 'inactive'}">
                <div class="mcp-server-indicator ${s.status === 'running' ? 'green' : 'red'}"></div>
                <div class="mcp-server-info">
                    <strong>${s.name || s.id}</strong>
                    <small>${s.tools_count || 0} tools</small>
                </div>
                <div class="mcp-server-status">${s.status}</div>
            </div>
        `).join('');
    }

    async applyConfig() {
        try {
            const result = await this.api.post('/mcp_servers_apply', {});
            this.toast.success('MCP config applied');
            setTimeout(() => this.refresh(), 2000);
        } catch (err) {
            this.toast.error('Failed to apply MCP config');
        }
    }
}
