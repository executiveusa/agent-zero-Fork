/**
 * Cron Panel — Displays and controls scheduled cron jobs
 * Reads from the scheduler API, renders job cards with run/pause/delete
 */

export class CronPanel {
    constructor(api, state, toast) {
        this.api = api;
        this.state = state;
        this.toast = toast;
        this.refreshTimer = null;
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        const refreshBtn = document.getElementById('cron-refresh-btn');
        if (refreshBtn) refreshBtn.addEventListener('click', () => this.refresh());

        const addBtn = document.getElementById('cron-add-btn');
        if (addBtn) addBtn.addEventListener('click', () => this.showAddForm());
    }

    async refresh() {
        const container = document.getElementById('cron-jobs-grid');
        if (!container) return;

        container.innerHTML = '<div class="cron-loading">Loading cron jobs…</div>';

        try {
            const data = await this.api.schedulerTasksList({});
            const cronTasks = (data.tasks || []).filter(t => t.type === 'scheduled');

            if (cronTasks.length === 0) {
                container.innerHTML = '<div class="cron-empty">No cron jobs configured</div>';
                return;
            }

            container.innerHTML = cronTasks.map(task => this.renderJobCard(task)).join('');

            // Bind card actions
            container.querySelectorAll('[data-action]').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const action = btn.dataset.action;
                    const taskId = btn.dataset.taskId;
                    this.handleAction(action, taskId);
                });
            });

            // Update badge count
            const badge = document.querySelector('.cron-count-badge');
            if (badge) badge.textContent = cronTasks.length;

        } catch (err) {
            container.innerHTML = `<div class="cron-error">Failed to load: ${err.message}</div>`;
        }
    }

    renderJobCard(task) {
        const stateColors = {
            idle: 'var(--color-idle)',
            running: 'var(--color-running)',
            disabled: 'var(--color-offline)',
            error: 'var(--color-error)',
        };
        const color = stateColors[task.state] || 'var(--text-muted)';

        const nextRun = task.next_run
            ? new Date(task.next_run * 1000).toLocaleString()
            : 'N/A';
        const lastRun = task.last_run
            ? new Date(task.last_run * 1000).toLocaleString()
            : 'Never';

        return `
            <div class="cron-card" data-task-id="${task.id}">
                <div class="cron-card-header">
                    <span class="cron-dot" style="background:${color}"></span>
                    <span class="cron-name">${this.esc(task.task_name || task.id)}</span>
                    <span class="cron-state">${task.state}</span>
                </div>
                <div class="cron-card-body">
                    <div class="cron-row">
                        <span class="cron-label">Schedule</span>
                        <span class="cron-value">${this.esc(task.schedule || '??')}</span>
                    </div>
                    <div class="cron-row">
                        <span class="cron-label">Next Run</span>
                        <span class="cron-value">${nextRun}</span>
                    </div>
                    <div class="cron-row">
                        <span class="cron-label">Last Run</span>
                        <span class="cron-value">${lastRun}</span>
                    </div>
                    ${task.last_error ? `<div class="cron-row cron-error-row"><span class="cron-label">Error</span><span class="cron-value">${this.esc(task.last_error)}</span></div>` : ''}
                </div>
                <div class="cron-card-actions">
                    <button class="btn-icon" data-action="run" data-task-id="${task.id}" title="Run Now">▶</button>
                    <button class="btn-icon" data-action="${task.state === 'disabled' ? 'enable' : 'disable'}" data-task-id="${task.id}" title="${task.state === 'disabled' ? 'Enable' : 'Disable'}">${task.state === 'disabled' ? '✓' : '⏸'}</button>
                    <button class="btn-icon btn-icon-danger" data-action="delete" data-task-id="${task.id}" title="Delete">✕</button>
                </div>
            </div>
        `;
    }

    async handleAction(action, taskId) {
        try {
            switch (action) {
                case 'run':
                    await this.api.schedulerTaskRun({ task_id: taskId });
                    this.toast?.success('Task triggered');
                    break;
                case 'disable':
                    await this.api.schedulerTaskUpdate({ task_id: taskId, state: 'disabled' });
                    this.toast?.info('Task disabled');
                    break;
                case 'enable':
                    await this.api.schedulerTaskUpdate({ task_id: taskId, state: 'idle' });
                    this.toast?.info('Task enabled');
                    break;
                case 'delete':
                    if (confirm('Delete this cron job?')) {
                        await this.api.schedulerTaskDelete({ task_id: taskId });
                        this.toast?.success('Task deleted');
                    }
                    break;
            }
            await this.refresh();
        } catch (err) {
            this.toast?.error(`Action failed: ${err.message}`);
        }
    }

    showAddForm() {
        const container = document.getElementById('cron-add-form');
        if (!container) return;

        if (container.style.display !== 'none') {
            container.style.display = 'none';
            return;
        }

        container.style.display = '';
        container.innerHTML = `
            <div class="cron-form">
                <input type="text" id="cron-new-name" placeholder="Task name" class="cron-input" />
                <input type="text" id="cron-new-schedule" placeholder="Cron expression (e.g. 0 9 * * *)" class="cron-input" />
                <textarea id="cron-new-prompt" placeholder="Task prompt / instructions" class="cron-textarea"></textarea>
                <div class="cron-form-actions">
                    <button id="cron-save-btn" class="btn btn-primary">Create</button>
                    <button id="cron-cancel-btn" class="btn btn-secondary">Cancel</button>
                </div>
            </div>
        `;

        document.getElementById('cron-save-btn')?.addEventListener('click', () => this.saveNewCron());
        document.getElementById('cron-cancel-btn')?.addEventListener('click', () => {
            container.style.display = 'none';
        });
    }

    async saveNewCron() {
        const name = document.getElementById('cron-new-name')?.value?.trim();
        const schedule = document.getElementById('cron-new-schedule')?.value?.trim();
        const prompt = document.getElementById('cron-new-prompt')?.value?.trim();

        if (!name || !schedule || !prompt) {
            this.toast?.warning('Fill in all fields');
            return;
        }

        try {
            await this.api.schedulerTaskCreate({
                type: 'scheduled',
                task_name: name,
                schedule: schedule,
                prompt: prompt,
            });
            this.toast?.success(`Cron job "${name}" created`);
            document.getElementById('cron-add-form').style.display = 'none';
            await this.refresh();
        } catch (err) {
            this.toast?.error(`Failed: ${err.message}`);
        }
    }

    startAutoRefresh(intervalMs = 30000) {
        this.stopAutoRefresh();
        this.refresh();
        this.refreshTimer = setInterval(() => this.refresh(), intervalMs);
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    esc(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
}
