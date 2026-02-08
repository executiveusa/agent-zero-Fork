/**
 * SYNTHIA Voice Panel — Voice command control interface
 * Mic input, command routing, TTS playback, command help grid
 */

export class SynthiaVoicePanel {
    constructor(api, state, toast) {
        this.api = api;
        this.state = state;
        this.toast = toast;
        this.isListening = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        const micBtn = document.getElementById('synthia-mic-btn');
        if (micBtn) micBtn.addEventListener('click', () => this.toggleListening());

        const cmdInput = document.getElementById('synthia-cmd-input');
        if (cmdInput) cmdInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.sendTextCommand(cmdInput.value);
        });

        const cmdSend = document.getElementById('synthia-cmd-send');
        if (cmdSend) cmdSend.addEventListener('click', () => {
            const el = document.getElementById('synthia-cmd-input');
            if (el) this.sendTextCommand(el.value);
        });

        const helpBtn = document.getElementById('synthia-help-btn');
        if (helpBtn) helpBtn.addEventListener('click', () => this.showCommandHelp());

        const ttsTest = document.getElementById('synthia-tts-test');
        if (ttsTest) ttsTest.addEventListener('click', () => this.testTTS());
    }

    /* ── Mic toggle ─────────────────────────────────── */
    async toggleListening() {
        const micBtn = document.getElementById('synthia-mic-btn');
        const status = document.getElementById('synthia-mic-status');

        if (this.isListening) {
            this.isListening = false;
            if (this.mediaRecorder?.state !== 'inactive') this.mediaRecorder.stop();
            micBtn?.classList.remove('listening');
            if (status) status.textContent = 'Click to speak';
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (e) => this.audioChunks.push(e.data);
            this.mediaRecorder.onstop = async () => {
                const blob = new Blob(this.audioChunks, { type: 'audio/webm' });
                stream.getTracks().forEach(t => t.stop());
                await this.processAudio(blob);
            };

            this.mediaRecorder.start();
            this.isListening = true;
            micBtn?.classList.add('listening');
            if (status) status.textContent = 'Listening… click to stop';

            setTimeout(() => { if (this.isListening) this.toggleListening(); }, 15000);
        } catch (err) {
            console.error('Mic access denied:', err);
            this.toast?.error('Microphone access denied');
        }
    }

    async processAudio(blob) {
        const status = document.getElementById('synthia-mic-status');
        if (status) status.textContent = 'Transcribing…';
        try {
            const result = await this.api.transcribe(blob);
            const text = result.text || result.transcript || '';
            if (text) {
                document.getElementById('synthia-cmd-input').value = text;
                await this.sendTextCommand(text);
            } else {
                if (status) status.textContent = 'No speech detected';
            }
        } catch {
            if (status) status.textContent = 'Transcription failed';
        }
    }

    /* ── Text command ───────────────────────────────── */
    async sendTextCommand(text) {
        text = text?.trim();
        if (!text) return;
        const input = document.getElementById('synthia-cmd-input');
        if (input) input.value = '';

        this.appendHistory('user', text);
        this.appendHistory('system', 'Routing…');

        try {
            const context = this.state.getActiveContext();
            const result = await this.api.message({
                context: context || '',
                text: `[voice_command] ${text}`,
            });

            this.removeLastHistory();
            this.appendHistory('synthia', result.response || 'Command dispatched.');
        } catch (err) {
            this.removeLastHistory();
            this.appendHistory('error', `Failed: ${err.message}`);
        }
    }

    appendHistory(type, text) {
        const c = document.getElementById('synthia-history');
        if (!c) return;
        const icons = { user: '🎤', synthia: '🤖', system: '⚙️', error: '❌' };
        const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const d = document.createElement('div');
        d.className = `synthia-entry synthia-${type}`;
        d.innerHTML = `<span class="se-time">${t}</span><span class="se-icon">${icons[type] || '•'}</span><span class="se-text">${this.esc(text)}</span>`;
        c.appendChild(d);
        c.scrollTop = c.scrollHeight;
    }

    removeLastHistory() {
        const c = document.getElementById('synthia-history');
        if (c?.lastChild) c.removeChild(c.lastChild);
    }

    /* ── Help grid ──────────────────────────────────── */
    showCommandHelp() {
        const grid = document.getElementById('synthia-commands-grid');
        if (!grid) return;
        const commands = [
            { cat: 'VOICE', cmds: ['call', 'speak/TTS', 'voice status'] },
            { cat: 'COMMS', cmds: ['check messages', 'send message'] },
            { cat: 'TASKS', cmds: ['list tasks', 'set reminder', 'schedule recurring', 'run task', 'cancel task', 'briefing'] },
            { cat: 'MEMORY', cmds: ['remember', 'recall', 'forget'] },
            { cat: 'SEARCH', cmds: ['web search', 'private search', 'private chat'] },
            { cat: 'MEDIA', cmds: ['generate image'] },
            { cat: 'BROWSE', cmds: ['open website'] },
            { cat: 'SYSTEM', cmds: ['system status', 'venice status', 'help'] },
            { cat: 'CODE', cmds: ['run python', 'run terminal'] },
        ];
        grid.innerHTML = commands.map(g => `
            <div class="cmd-group">
                <h4 class="cmd-group-title">${g.cat}</h4>
                ${g.cmds.map(c => `<div class="cmd-chip">${c}</div>`).join('')}
            </div>
        `).join('');
        grid.style.display = grid.style.display === 'none' ? '' : 'none';
    }

    async testTTS() {
        this.toast?.info('Testing TTS…');
        try {
            await this.api.synthesize({ text: 'SYNTHIA voice system online.' });
            this.toast?.success('TTS OK');
        } catch { this.toast?.error('TTS test failed'); }
    }

    async updateStatus() {
        const el = document.getElementById('synthia-service-status');
        if (!el) return;
        try {
            const s = await this.api.fetchAPI('/health', { method: 'POST', body: '{}' });
            el.innerHTML = `
                <div class="svc-row"><span>Agent</span><span class="status-dot online"></span></div>
                <div class="svc-row"><span>Voice Commands</span><span class="status-dot online"></span></div>
                <div class="svc-row"><span>Status</span><span class="status-dot ${s.status === 'ok' ? 'online' : 'offline'}"></span></div>
            `;
        } catch {
            el.innerHTML = '<div class="svc-row"><span>Services</span><span class="status-dot offline"></span></div>';
        }
    }

    esc(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
}
