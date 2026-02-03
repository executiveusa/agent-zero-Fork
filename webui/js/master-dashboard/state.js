/**
 * Dashboard State Management
 * Centralized state for the entire dashboard
 */

export class DashboardState {
    constructor() {
        this.state = {
            activeContext: null,
            contexts: [],
            tasks: [],
            logs: [],
            logVersion: 0,
            logGuid: null,
            notifications: [],
            notificationsVersion: 0,
            notificationsGuid: null,
            paused: false,
            logProgress: '',
            logProgressActive: false,
            autonomyLevel: 2, // Default Tier 2
        };
        
        // Subscribe listeners
        this.listeners = [];
    }
    
    /**
     * Subscribe to state changes
     */
    subscribe(callback) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter(cb => cb !== callback);
        };
    }
    
    /**
     * Notify all listeners of state change
     */
    notify() {
        this.listeners.forEach(callback => callback(this.state));
    }
    
    /**
     * Update state from poll response
     */
    updateFromPoll(pollData) {
        this.state.contexts = pollData.contexts || [];
        this.state.tasks = pollData.tasks || [];
        this.state.logs = pollData.logs || [];
        this.state.logVersion = pollData.log_version || 0;
        this.state.logGuid = pollData.log_guid;
        this.state.notifications = pollData.notifications || [];
        this.state.notificationsVersion = pollData.notifications_version || 0;
        this.state.notificationsGuid = pollData.notifications_guid;
        this.state.paused = pollData.paused || false;
        this.state.logProgress = pollData.log_progress || '';
        this.state.logProgressActive = pollData.log_progress_active || false;
        
        // If context was deselected by backend, clear active context
        if (pollData.deselect_chat) {
            this.state.activeContext = null;
        }
        
        this.notify();
    }
    
    /**
     * Set active context
     */
    setActiveContext(contextId) {
        this.state.activeContext = contextId;
        this.notify();
    }
    
    /**
     * Get active context
     */
    getActiveContext() {
        return this.state.activeContext;
    }
    
    /**
     * Get log version for polling
     */
    getLogVersion() {
        return this.state.logVersion;
    }
    
    /**
     * Get notifications version for polling
     */
    getNotificationsVersion() {
        return this.state.notificationsVersion;
    }
    
    /**
     * Set autonomy level (Tier 0-4)
     */
    setAutonomyLevel(level) {
        this.state.autonomyLevel = level;
        this.notify();
    }
    
    /**
     * Get autonomy level
     */
    getAutonomyLevel() {
        return this.state.autonomyLevel;
    }
    
    /**
     * Get all logs
     */
    getLogs() {
        return this.state.logs;
    }
    
    /**
     * Get all contexts
     */
    getContexts() {
        return this.state.contexts;
    }
    
    /**
     * Get all tasks
     */
    getTasks() {
        return this.state.tasks;
    }
}
