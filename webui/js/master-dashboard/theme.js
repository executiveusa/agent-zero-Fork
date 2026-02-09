/**
 * Theme Manager — Light/Dark mode with persistence
 */
export class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('agent-claw-theme') || 'dark';
    }

    init() {
        document.documentElement.setAttribute('data-theme', this.theme);
        this._injectToggle();
        console.log(`🎨 Theme: ${this.theme}`);
    }

    toggle() {
        this.theme = this.theme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', this.theme);
        localStorage.setItem('agent-claw-theme', this.theme);
        const cb = document.getElementById('theme-checkbox');
        if (cb) cb.checked = this.theme === 'dark';
    }

    _injectToggle() {
        const bar = document.querySelector('.status-bar-right');
        if (!bar) return;
        const wrapper = document.createElement('label');
        wrapper.className = 'theme-toggle';
        wrapper.title = 'Toggle Light / Dark';
        wrapper.innerHTML = `
            <span class="theme-icon">☀️</span>
            <input type="checkbox" id="theme-checkbox" ${this.theme === 'dark' ? 'checked' : ''}>
            <span class="theme-toggle-track"></span>
            <span class="theme-icon">🌙</span>
        `;
        wrapper.querySelector('input').addEventListener('change', () => this.toggle());
        bar.prepend(wrapper);
    }
}
