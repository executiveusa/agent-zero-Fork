/**
 * Voice Call Panel — Twilio + ElevenLabs integration
 * Allows the user to call the agent or have the agent call them.
 * Provides call history, persona selection, and conversation context.
 */
export class VoiceCallPanel {
    constructor(api, state, toast) {
        this.api = api;
        this.state = state;
        this.toast = toast;
        this.callActive = false;
    }

    init() {
        this._bindButtons();
    }

    _bindButtons() {
        // Quick-call button
        const callMeBtn = document.getElementById('voice-call-me-btn');
        if (callMeBtn) {
            callMeBtn.addEventListener('click', () => this.callMe());
        }

        // Outbound call form
        const callBtn = document.getElementById('voice-make-call-btn');
        if (callBtn) {
            callBtn.addEventListener('click', () => this.showCallDialog());
        }

        // Refresh log
        const logBtn = document.getElementById('voice-refresh-log-btn');
        if (logBtn) {
            logBtn.addEventListener('click', () => this.refreshCallLog());
        }

        // Persona selector
        const personaSelect = document.getElementById('voice-persona-select');
        if (personaSelect) {
            personaSelect.addEventListener('change', (e) => {
                localStorage.setItem('agent-claw-voice-persona', e.target.value);
            });
        }
    }

    async callMe() {
        const yourNumber = localStorage.getItem('agent-claw-phone') || '';
        if (!yourNumber) {
            this.showPhoneSetup();
            return;
        }

        const persona = localStorage.getItem('agent-claw-voice-persona') || 'professional';
        this.callActive = true;
        this._updateCallStatus('Calling you...');

        try {
            const result = await this.api.post('/voice', {
                action: 'make_call',
                to: yourNumber,
                message: 'Hey, this is your AI agent. You asked me to give you a call. How can I help you today?',
                voice: persona,
            });
            if (result.success) {
                this.toast.success('Call initiated! Your phone should ring shortly.');
                this._updateCallStatus('Call in progress...');
            } else {
                this.toast.error(result.error || 'Call failed');
                this._updateCallStatus('Call failed');
            }
        } catch (err) {
            this.toast.error('Voice service error: ' + err.message);
            this._updateCallStatus('Error');
        }
        this.callActive = false;
    }

    showPhoneSetup() {
        const phone = prompt('Enter your phone number (E.164 format, e.g. +13234842914):');
        if (phone && phone.startsWith('+')) {
            localStorage.setItem('agent-claw-phone', phone);
            this.toast.success('Phone number saved! Click Call Me again.');
            const display = document.getElementById('voice-your-number');
            if (display) display.textContent = phone;
        } else if (phone) {
            this.toast.warning('Phone must start with + (E.164 format)');
        }
    }

    showCallDialog() {
        const phone = prompt('Enter number to call (E.164 format):');
        const message = prompt('What should the agent say?');
        if (phone && message) {
            this.makeOutboundCall(phone, message);
        }
    }

    async makeOutboundCall(to, message) {
        const persona = localStorage.getItem('agent-claw-voice-persona') || 'professional';
        try {
            const result = await this.api.post('/voice', {
                action: 'make_call',
                to,
                message,
                voice: persona,
            });
            if (result.success) {
                this.toast.success('Call sent!');
                this.refreshCallLog();
            } else {
                this.toast.error(result.error || 'Call failed');
            }
        } catch (err) {
            this.toast.error('Call error: ' + err.message);
        }
    }

    async refreshCallLog() {
        const container = document.getElementById('voice-call-log');
        if (!container) return;

        try {
            const result = await this.api.post('/voice', { action: 'call_log', limit: 20 });
            if (result.success && result.calls) {
                container.innerHTML = result.calls.map(c => `
                    <div class="call-log-item call-${c.status?.includes('failed') ? 'failed' : 'ok'}">
                        <div class="call-direction">${c.direction === 'outbound' ? '📞→' : '←📞'}</div>
                        <div class="call-details">
                            <strong>${c.direction === 'outbound' ? c.to_number : c.from_number}</strong>
                            <small>${c.created_at ? new Date(c.created_at).toLocaleString() : ''}</small>
                        </div>
                        <div class="call-status">${c.status}</div>
                        <div class="call-transcript">${(c.agent_response || c.transcription || '').substring(0, 80)}</div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<div class="text-muted">No calls yet</div>';
            }
        } catch (err) {
            container.innerHTML = `<div class="text-muted">Error loading: ${err.message}</div>`;
        }
    }

    _updateCallStatus(text) {
        const el = document.getElementById('voice-call-status');
        if (el) el.textContent = text;
    }
}
