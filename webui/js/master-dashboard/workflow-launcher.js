/**
 * Workflow Launcher — One-click deploy common workflows
 * Quick-access toggles for the most common agent operations
 */
export class WorkflowLauncher {
    constructor(api, state, toast) {
        this.api = api;
        this.state = state;
        this.toast = toast;
    }

    init() {
        this._bindButtons();
        this._loadSavedWorkflows();
    }

    _bindButtons() {
        document.querySelectorAll('[data-workflow]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const wf = btn.dataset.workflow;
                this.launchWorkflow(wf);
            });
        });

        // Custom workflow
        const customBtn = document.getElementById('wf-custom-btn');
        if (customBtn) {
            customBtn.addEventListener('click', () => this.launchCustom());
        }
    }

    async launchWorkflow(name) {
        const workflows = {
            'web-research': {
                prompt: 'Perform comprehensive web research and summarize findings.',
                agent: 'MASTER',
            },
            'code-review': {
                prompt: 'Review the current codebase for issues, bugs, and improvements.',
                agent: 'MASTER',
            },
            'deploy-check': {
                prompt: 'Run deployment readiness check: verify Docker, health endpoints, configs.',
                agent: 'TACTICAL',
            },
            'content-gen': {
                prompt: 'Generate content for our brand channels based on latest strategy.',
                agent: 'DESIGNER',
            },
            'voice-checkin': {
                prompt: 'Call the owner for a quick status check-in.',
                agent: 'VOICE',
            },
            'memory-sweep': {
                prompt: 'Consolidate and clean up agent memory. Archive old conversations.',
                agent: 'MEMORY',
            },
            'swarm-dispatch': {
                prompt: 'Dispatch swarm agents for parallel task execution on current queue.',
                agent: 'MASTER',
            },
            'knowledge-index': {
                prompt: 'Re-index all knowledge base documents and update vector embeddings.',
                agent: 'MEMORY',
            },
        };

        const wf = workflows[name];
        if (!wf) {
            this.toast.warning(`Unknown workflow: ${name}`);
            return;
        }

        this.toast.info(`Launching workflow: ${name}...`);

        try {
            const result = await this.api.post('/message', {
                text: `[WORKFLOW: ${name}] ${wf.prompt}`,
                context: this.state.getActiveContext() || '',
            });
            this.toast.success(`Workflow "${name}" dispatched!`);
        } catch (err) {
            this.toast.error(`Workflow failed: ${err.message}`);
        }
    }

    async launchCustom() {
        const prompt = document.getElementById('wf-custom-prompt')?.value;
        if (!prompt?.trim()) {
            this.toast.warning('Enter a task description first');
            return;
        }

        this.toast.info('Launching custom workflow...');
        try {
            const result = await this.api.post('/message', {
                text: prompt.trim(),
                context: this.state.getActiveContext() || '',
            });
            this.toast.success('Custom task dispatched!');
            document.getElementById('wf-custom-prompt').value = '';
        } catch (err) {
            this.toast.error(`Failed: ${err.message}`);
        }
    }

    _loadSavedWorkflows() {
        // Load any user-saved custom workflow templates
        const saved = JSON.parse(localStorage.getItem('agent-claw-custom-workflows') || '[]');
        const container = document.getElementById('wf-saved-list');
        if (container && saved.length > 0) {
            container.innerHTML = saved.map((wf, i) => `
                <button class="wf-saved-btn" data-saved-idx="${i}">
                    <span class="wf-icon">⚡</span>
                    <span class="wf-name">${wf.name}</span>
                </button>
            `).join('');
            container.querySelectorAll('.wf-saved-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const idx = parseInt(btn.dataset.savedIdx);
                    this.api.post('/message', {
                        text: saved[idx].prompt,
                        context: this.state.getActiveContext() || '',
                    });
                    this.toast.success(`Launched: ${saved[idx].name}`);
                });
            });
        }
    }
}
