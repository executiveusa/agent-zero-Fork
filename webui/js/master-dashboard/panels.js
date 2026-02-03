/**
 * Panel Manager - Handles navigation and panel visibility
 */

export class PanelManager {
    constructor() {
        this.panels = {};
        this.activePanel = null;
    }
    
    init() {
        // Register all panels
        const panelElements = document.querySelectorAll('[id^="panel-"]');
        panelElements.forEach(panel => {
            const panelName = panel.id.replace('panel-', '');
            this.panels[panelName] = panel;
        });
        
        // Set default panel
        this.showPanel('mission-control');
    }
    
    showPanel(panelName) {
        // Hide all panels
        Object.values(this.panels).forEach(panel => {
            panel.classList.remove('active');
        });
        
        // Show requested panel
        if (this.panels[panelName]) {
            this.panels[panelName].classList.add('active');
            this.activePanel = panelName;
        }
    }
    
    isActive(panelName) {
        return this.activePanel === panelName;
    }
    
    getActivePanel() {
        return this.activePanel;
    }
}
