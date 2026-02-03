/**
 * Master Dashboard - Main Entry Point
 * Coordinates all dashboard functionality and initializes subsystems
 */

import { DashboardAPI } from './api.js';
import { DashboardState } from './state.js';
import { PanelManager } from './panels.js';
import { BeadsTimeline } from './beads.js';
import { LiveView } from './live-view.js';
import { ToastManager } from './toast.js';

class MasterDashboard {
    constructor() {
        this.api = new DashboardAPI();
        this.state = new DashboardState();
        this.panelManager = new PanelManager();
        this.beadsTimeline = new BeadsTimeline(this.api, this.state);
        this.liveView = new LiveView(this.api, this.state);
        this.toast = new ToastManager();
        
        this.pollingInterval = null;
        this.pollingRate = 750; // Default 750ms
        
        this.init();
    }
    
    init() {
        console.log('🚀 Master Dashboard initializing...');
        
        // Initialize navigation
        this.initNavigation();
        
        // Initialize top bar controls
        this.initTopBar();
        
        // Initialize panels
        this.panelManager.init();
        
        // Start polling
        this.startPolling();
        
        // Check health
        this.checkHealth();
        
        console.log('✅ Master Dashboard ready');
        this.toast.success('Master Dashboard initialized');
    }
    
    initNavigation() {
        const navButtons = document.querySelectorAll('.nav-btn[data-panel]');
        navButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const panelName = btn.dataset.panel;
                this.panelManager.showPanel(panelName);
                
                // Update active state
                navButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
    }
    
    initTopBar() {
        // Context selector
        const contextSelector = document.getElementById('context-selector');
        if (contextSelector) {
            contextSelector.addEventListener('change', (e) => {
                this.state.setActiveContext(e.target.value);
            });
        }
        
        // Pause button
        const pauseBtn = document.getElementById('pause-btn');
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => this.togglePause());
        }
        
        // Autonomy slider
        const autonomySlider = document.getElementById('autonomy-slider');
        const autonomyLevel = document.getElementById('autonomy-level');
        if (autonomySlider && autonomyLevel) {
            autonomySlider.addEventListener('input', (e) => {
                const level = parseInt(e.target.value);
                autonomyLevel.textContent = `T${level}`;
                this.state.setAutonomyLevel(level);
                this.toast.info(`Autonomy Level set to Tier ${level}`);
            });
        }
    }
    
    async startPolling() {
        console.log('📡 Starting poll loop...');
        
        const poll = async () => {
            try {
                const context = this.state.getActiveContext();
                const pollData = await this.api.poll({
                    context: context || '',
                    log_from: this.state.getLogVersion(),
                    notifications_from: this.state.getNotificationsVersion()
                });
                
                // Update state
                this.state.updateFromPoll(pollData);
                
                // Update UI
                this.updateUI(pollData);
                
                // Adjust polling rate based on activity
                this.adjustPollingRate(pollData);
                
                // Update connection status
                this.updateConnectionStatus(true);
                
            } catch (error) {
                console.error('Poll error:', error);
                this.updateConnectionStatus(false);
                this.pollingRate = 1500; // Slow down on error
            }
        };
        
        // Initial poll
        await poll();
        
        // Start interval
        this.pollingInterval = setInterval(poll, this.pollingRate);
    }
    
    adjustPollingRate(pollData) {
        // Adaptive polling based on activity
        const isActive = pollData.log_progress_active;
        const hasRunningTasks = pollData.tasks?.some(t => t.state === 'running');
        const hasErrors = pollData.logs?.some(l => l.type === 'error');
        
        let newRate;
        if (isActive || hasRunningTasks) {
            newRate = 500; // Fast when active
        } else if (hasErrors) {
            newRate = 750; // Medium when errors
        } else {
            newRate = 1500; // Slow when idle
        }
        
        if (newRate !== this.pollingRate) {
            this.pollingRate = newRate;
            clearInterval(this.pollingInterval);
            this.pollingInterval = setInterval(() => this.startPolling(), this.pollingRate);
        }
    }
    
    updateUI(pollData) {
        // Update progress bar
        this.updateProgressBar(pollData);
        
        // Update context selector
        this.updateContextSelector(pollData);
        
        // Update error badge
        this.updateErrorBadge(pollData);
        
        // Update mission control cards
        this.updateMissionControl(pollData);
        
        // Update beads timeline (if visible)
        if (this.panelManager.isActive('beads')) {
            this.beadsTimeline.update(pollData.logs);
        }
        
        // Update live view (if visible)
        if (this.panelManager.isActive('live-view')) {
            this.liveView.update(pollData.logs, pollData.log_progress);
        }
    }
    
    updateProgressBar(pollData) {
        const progressBar = document.querySelector('.progress-bar');
        const progressText = document.querySelector('.progress-text');
        
        if (pollData.log_progress_active && pollData.log_progress) {
            progressText.textContent = pollData.log_progress;
            progressBar.style.width = '100%';
            progressBar.style.animation = 'progress-slide 2s infinite';
        } else if (pollData.log_progress) {
            progressText.textContent = pollData.log_progress;
            progressBar.style.width = '0%';
            progressBar.style.animation = 'none';
        } else {
            progressText.textContent = 'Idle';
            progressBar.style.width = '0%';
        }
    }
    
    updateContextSelector(pollData) {
        const selector = document.getElementById('context-selector');
        if (!selector) return;
        
        const currentValue = selector.value;
        selector.innerHTML = '<option value="">No Context</option>';
        
        pollData.contexts?.forEach(ctx => {
            const option = document.createElement('option');
            option.value = ctx.id;
            option.textContent = ctx.name || ctx.id;
            selector.appendChild(option);
        });
        
        if (currentValue) {
            selector.value = currentValue;
        }
    }
    
    updateErrorBadge(pollData) {
        const errorBadge = document.getElementById('error-badge');
        const errorCount = document.querySelector('.error-count');
        
        const errors = pollData.logs?.filter(l => l.type === 'error' || l.type === 'warning') || [];
        
        if (errors.length > 0) {
            errorBadge.classList.remove('hidden');
            errorCount.textContent = errors.length;
        } else {
            errorBadge.classList.add('hidden');
        }
    }
    
    updateMissionControl(pollData) {
        // Update contexts count and list
        const contextsCount = document.getElementById('contexts-count');
        const contextsList = document.getElementById('contexts-list');
        if (contextsCount) contextsCount.textContent = pollData.contexts?.length || 0;
        if (contextsList) {
            contextsList.innerHTML = pollData.contexts?.slice(0, 5).map(ctx => `
                <div class="context-item">
                    <strong>${ctx.name || 'Chat ' + ctx.id.substring(0, 8)}</strong>
                    <small>${ctx.paused ? '⏸ Paused' : '▶️ Active'}</small>
                </div>
            `).join('') || '<div class="text-muted">No active contexts</div>';
        }
        
        // Update running tasks count and list
        const runningTasks = pollData.tasks?.filter(t => t.state === 'running') || [];
        const tasksRunningCount = document.getElementById('tasks-running-count');
        const tasksRunningList = document.getElementById('tasks-running-list');
        if (tasksRunningCount) tasksRunningCount.textContent = runningTasks.length;
        if (tasksRunningList) {
            tasksRunningList.innerHTML = runningTasks.slice(0, 5).map(task => `
                <div class="task-item">
                    <strong>${task.task_name || 'Task'}</strong>
                    <small>${task.type}</small>
                </div>
            `).join('') || '<div class="text-muted">No running tasks</div>';
        }
        
        // Update recent beads mini
        const recentBeadsMini = document.getElementById('recent-beads');
        if (recentBeadsMini && pollData.logs) {
            const recent = pollData.logs.slice(-3).reverse();
            recentBeadsMini.innerHTML = recent.map(log => `
                <div class="bead-mini bead-${log.type}">
                    <span class="bead-heading">${log.heading || log.type}</span>
                </div>
            `).join('');
        }
        
        // Update alerts
        const alertList = document.getElementById('alert-list');
        if (alertList) {
            const alerts = pollData.logs?.filter(l => l.type === 'error' || l.type === 'warning').slice(-5) || [];
            alertList.innerHTML = alerts.length > 0 
                ? alerts.map(alert => `
                    <div class="alert-item alert-${alert.type}">
                        <strong>${alert.heading}</strong>
                        <p>${alert.content?.substring(0, 100) || ''}</p>
                    </div>
                `).join('')
                : '<div class="no-alerts">No critical alerts</div>';
        }
    }
    
    updateConnectionStatus(isOnline) {
        const connectionStatus = document.getElementById('connection-status');
        const statusText = connectionStatus?.querySelector('.status-text');
        const lastUpdate = connectionStatus?.querySelector('.last-update');
        
        if (connectionStatus) {
            if (isOnline) {
                connectionStatus.classList.remove('offline');
                connectionStatus.classList.add('online');
                if (statusText) statusText.textContent = 'Online';
            } else {
                connectionStatus.classList.remove('online');
                connectionStatus.classList.add('offline');
                if (statusText) statusText.textContent = 'Offline';
            }
        }
        
        if (lastUpdate) {
            const now = new Date();
            lastUpdate.textContent = `Updated ${now.toLocaleTimeString()}`;
        }
    }
    
    async togglePause() {
        const context = this.state.getActiveContext();
        if (!context) {
            this.toast.warning('No context selected');
            return;
        }
        
        try {
            await this.api.pause({ context });
            this.toast.success('Toggled pause state');
        } catch (error) {
            this.toast.error('Failed to toggle pause');
        }
    }
    
    async checkHealth() {
        try {
            const health = await this.api.health();
            console.log('Health check:', health);
            
            const healthMetrics = document.getElementById('health-metrics');
            if (healthMetrics) {
                healthMetrics.innerHTML = `
                    <div class="metric">
                        <div class="metric-label">Status</div>
                        <div class="metric-value">${health.status || 'OK'}</div>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Health check failed:', error);
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.masterDashboard = new MasterDashboard();
});

// Add CSS animation for progress bar
const style = document.createElement('style');
style.textContent = `
    @keyframes progress-slide {
        0% { transform: translateX(-100%); }
        50% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
`;
document.head.appendChild(style);
