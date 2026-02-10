/**
 * Dashboard API - Communication layer with Agent Zero backend
 * Maps to endpoints defined in python/api/*.py
 */

export class DashboardAPI {
    constructor() {
        this.baseUrl = '';  // Same origin
        this.csrfToken = null;
    }
    
    /**
     * Fetch with automatic JSON handling and error catching
     */
    async fetchAPI(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        const defaultHeaders = {
            'Content-Type': 'application/json',
        };
        
        // Add CSRF token if available
        if (this.csrfToken) {
            defaultHeaders['X-CSRF-Token'] = this.csrfToken;
        }
        
        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return response;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }
    
    /**
     * Get CSRF token
     */
    async getCsrfToken() {
        try {
            const data = await this.fetchAPI('/csrf_token', { method: 'GET' });
            this.csrfToken = data.csrf_token;
            return this.csrfToken;
        } catch (error) {
            console.warn('Failed to get CSRF token:', error);
            return null;
        }
    }
    
    /* ==================== CORE ENDPOINTS ==================== */
    
    /**
     * Health check
     */
    async health() {
        return this.fetchAPI('/health', { method: 'POST', body: JSON.stringify({}) });
    }
    
    /**
     * Poll for updates (beads/logs/progress/tasks/contexts)
     */
    async poll(params = {}) {
        return this.fetchAPI('/poll', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    /* ==================== CHAT/CONTEXT ENDPOINTS ==================== */
    
    async chatCreate(params = {}) {
        return this.fetchAPI('/chat_create', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async chatLoad(params) {
        return this.fetchAPI('/chat_load', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async chatReset(params) {
        return this.fetchAPI('/chat_reset', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async chatRemove(params) {
        return this.fetchAPI('/chat_remove', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async chatExport(params) {
        return this.fetchAPI('/chat_export', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async historyGet(params) {
        return this.fetchAPI('/history_get', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async message(params) {
        return this.fetchAPI('/message', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async messageAsync(params) {
        return this.fetchAPI('/message_async', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async pause(params) {
        return this.fetchAPI('/pause', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async nudge(params) {
        return this.fetchAPI('/nudge', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    /* ==================== SCHEDULER ENDPOINTS ==================== */
    
    async schedulerTasksList(params = {}) {
        return this.fetchAPI('/scheduler_tasks_list', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async schedulerTaskCreate(params) {
        return this.fetchAPI('/scheduler_task_create', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async schedulerTaskUpdate(params) {
        return this.fetchAPI('/scheduler_task_update', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async schedulerTaskRun(params) {
        return this.fetchAPI('/scheduler_task_run', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async schedulerTaskDelete(params) {
        return this.fetchAPI('/scheduler_task_delete', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async schedulerTick(params = {}) {
        return this.fetchAPI('/scheduler_tick', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    /* ==================== PROJECTS ENDPOINT ==================== */
    
    async projects(params = {}) {
        return this.fetchAPI('/projects', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    /* ==================== MEMORY/KNOWLEDGE ENDPOINTS ==================== */
    
    async memoryDashboard(params = {}) {
        return this.fetchAPI('/memory_dashboard', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async importKnowledge(params) {
        return this.fetchAPI('/import_knowledge', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async knowledgeReindex(params = {}) {
        return this.fetchAPI('/knowledge_reindex', {
            method: 'POST',
            body: JSON.STRING(params),
        });
    }
    
    async knowledgePathGet(params = {}) {
        return this.fetchAPI('/knowledge_path_get', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    /* ==================== FILES ENDPOINTS ==================== */
    
    async getWorkDirFiles(params = {}) {
        return this.fetchAPI('/get_work_dir_files', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async fileInfo(params) {
        return this.fetchAPI('/file_info', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async deleteWorkDirFile(params) {
        return this.fetchAPI('/delete_work_dir_file', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async downloadWorkDirFile(params) {
        const queryString = new URLSearchParams(params).toString();
        window.open(`/download_work_dir_file?${queryString}`, '_blank');
    }
    
    async uploadWorkDirFiles(formData) {
        return this.fetchAPI('/upload_work_dir_files', {
            method: 'POST',
            body: formData,
            headers: {}, // Let browser set content-type boundary for FormData
        });
    }
    
    getImageUrl(path) {
        return `/image_get?path=${encodeURIComponent(path)}`;
    }
    
    /* ==================== BACKUP ENDPOINTS ==================== */
    
    async backupGetDefaults(params = {}) {
        return this.fetchAPI('/backup_get_defaults', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async backupCreate(params) {
        return this.fetchAPI('/backup_create', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async backupPreviewGrouped(params = {}) {
        return this.fetchAPI('/backup_preview_grouped', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async backupInspect(params) {
        return this.fetchAPI('/backup_inspect', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async backupRestorePreview(params) {
        return this.fetchAPI('/backup_restore_preview', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async backupRestore(params) {
        return this.fetchAPI('/backup_restore', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async backupTest(params = {}) {
        return this.fetchAPI('/backup_test', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    /* ==================== NOTIFICATIONS ENDPOINTS ==================== */
    
    async notificationCreate(params) {
        return this.fetchAPI('/notification_create', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async notificationsHistory(params = {}) {
        return this.fetchAPI('/notifications_history', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async notificationsMarkRead(params) {
        return this.fetchAPI('/notifications_mark_read', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async notificationsClear(params = {}) {
        return this.fetchAPI('/notifications_clear', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    /* ==================== MCP ENDPOINTS ==================== */
    
    async mcpServersStatus(params = {}) {
        return this.fetchAPI('/mcp_servers_status', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async mcpServersApply(params) {
        return this.fetchAPI('/mcp_servers_apply', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async mcpServerGetDetail(params) {
        return this.fetchAPI('/mcp_server_get_detail', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async mcpServerGetLog(params) {
        return this.fetchAPI('/mcp_server_get_log', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    /* ==================== SETTINGS ENDPOINTS ==================== */
    
    async settingsGet(params = {}) {
        return this.fetchAPI('/settings_get', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async settingsSet(params) {
        return this.fetchAPI('/settings_set', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    /* ==================== TUNNEL/SPEECH ENDPOINTS ==================== */
    
    async tunnel(params) {
        return this.fetchAPI('/tunnel', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    async transcribe(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob);
        return this.fetchAPI('/transcribe', {
            method: 'POST',
            body: formData,
            headers: {}, // Let browser handle FormData headers
        });
    }
    
    async synthesize(params) {
        return this.fetchAPI('/synthesize', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }
    
    /* ==================== VISION ENDPOINTS ==================== */
    
    async visionAnalyze(formData) {
        return this.fetchAPI('/vision_analyze', {
            method: 'POST',
            body: formData,
            headers: {}, // Let browser set content-type boundary for FormData
        });
    }
}
