/**
 * Toast Notifications Manager
 * Simple toast notification system for user feedback
 */

export class ToastManager {
    constructor() {
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    }
    
    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icon = this.getIcon(type);
        toast.innerHTML = `
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${this.escapeHtml(message)}</span>
            <button class="toast-close">✕</button>
        `;
        
        this.container.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.classList.add('toast-visible'), 10);
        
        // Auto-dismiss
        const timeoutId = setTimeout(() => this.dismiss(toast), duration);
        
        // Manual dismiss
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            clearTimeout(timeoutId);
            this.dismiss(toast);
        });
        
        return toast;
    }
    
    dismiss(toast) {
        toast.classList.remove('toast-visible');
        setTimeout(() => toast.remove(), 300);
    }
    
    success(message, duration) {
        return this.show(message, 'success', duration);
    }
    
    error(message, duration) {
        return this.show(message, 'error', duration);
    }
    
    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }
    
    info(message, duration) {
        return this.show(message, 'info', duration);
    }
    
    getIcon(type) {
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ',
        };
        return icons[type] || 'ℹ';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Add CSS for toasts
const style = document.createElement('style');
style.textContent = `
    .toast {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: var(--shadow-lg);
        min-width: 300px;
        max-width: 400px;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
        margin-bottom: 8px;
    }
    
    .toast-visible {
        opacity: 1;
        transform: translateX(0);
    }
    
    .toast-success {
        background: var(--color-idle);
        color: white;
    }
    
    .toast-error {
        background: var(--color-error);
        color: white;
    }
    
    .toast-warning {
        background: var(--color-waiting);
        color: var(--bg-primary);
    }
    
    .toast-info {
        background: var(--color-planning);
        color: white;
    }
    
    .toast-icon {
        font-size: 20px;
        font-weight: 700;
    }
    
    .toast-message {
        flex: 1;
        font-size: 14px;
    }
    
    .toast-close {
        background: none;
        border: none;
        color: inherit;
        font-size: 18px;
        cursor: pointer;
        padding: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        opacity: 0.7;
    }
    
    .toast-close:hover {
        opacity: 1;
        background: rgba(0, 0, 0, 0.1);
    }
`;
document.head.appendChild(style);
