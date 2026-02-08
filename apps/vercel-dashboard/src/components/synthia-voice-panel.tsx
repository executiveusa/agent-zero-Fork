'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

interface VoiceCommand {
  id: string;
  utterance: string;
  matched_command: string | null;
  confidence: number;
  tool_name: string | null;
  timestamp: Date;
  status: 'matched' | 'no_match' | 'executing' | 'done' | 'error';
  result?: string;
}

interface SynthiaState {
  listening: boolean;
  speaking: boolean;
  connected: boolean;
  ttsQuota: number | null;
  lastHeard: string | null;
}

const QUICK_COMMANDS = [
  { label: 'Check Messages', icon: '💬', utterance: 'check my messages' },
  { label: 'System Status', icon: '⚡', utterance: 'system status' },
  { label: 'Morning Briefing', icon: '☀️', utterance: 'morning briefing' },
  { label: 'List Tasks', icon: '📋', utterance: 'list my tasks' },
  { label: 'Venice Search', icon: '🔒', utterance: 'private search' },
  { label: 'Help', icon: '❓', utterance: 'what can you do' },
];

export function SynthiaVoicePanel() {
  const [state, setState] = useState<SynthiaState>({
    listening: false,
    speaking: false,
    connected: false,
    ttsQuota: null,
    lastHeard: null,
  });
  const [history, setHistory] = useState<VoiceCommand[]>([]);
  const [textInput, setTextInput] = useState('');
  const [expanded, setExpanded] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Check SYNTHIA connectivity on mount
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch('/api/az/health');
        if (res.ok) {
          setState(s => ({ ...s, connected: true }));
        }
      } catch {
        setState(s => ({ ...s, connected: false }));
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  // Send a voice command (text-based for now, mic integration later)
  const sendCommand = useCallback(async (utterance: string) => {
    if (!utterance.trim()) return;

    const cmd: VoiceCommand = {
      id: crypto.randomUUID(),
      utterance: utterance.trim(),
      matched_command: null,
      confidence: 0,
      tool_name: null,
      timestamp: new Date(),
      status: 'executing',
    };
    setHistory(h => [cmd, ...h].slice(0, 20));
    setTextInput('');
    setState(s => ({ ...s, lastHeard: utterance.trim() }));

    try {
      // Route through Agent Zero — send the utterance as a message
      const res = await fetch('/api/az/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: `[VOICE COMMAND] ${utterance.trim()}`,
          context: 'default',
        }),
      });

      if (res.ok) {
        setHistory(h =>
          h.map(c =>
            c.id === cmd.id
              ? { ...c, status: 'done', matched_command: 'sent', confidence: 1 }
              : c
          )
        );
      } else {
        throw new Error(`HTTP ${res.status}`);
      }
    } catch (err) {
      setHistory(h =>
        h.map(c =>
          c.id === cmd.id
            ? { ...c, status: 'error', result: String(err) }
            : c
        )
      );
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendCommand(textInput);
  };

  const toggleListening = () => {
    setState(s => ({ ...s, listening: !s.listening }));
    // Browser SpeechRecognition would go here
  };

  return (
    <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="relative">
            <span className="text-2xl">🎙️</span>
            {state.connected && (
              <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-500 rounded-full border-2 border-slate-900" />
            )}
          </div>
          <div className="text-left">
            <h2 className="text-sm font-semibold text-slate-200">SYNTHIA Voice</h2>
            <p className="text-xs text-slate-500">
              {state.listening ? 'Listening...' : state.connected ? 'Ready' : 'Offline'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {state.listening && (
            <div className="flex gap-0.5 items-end h-4">
              {[1, 2, 3, 4, 3].map((h, i) => (
                <div
                  key={i}
                  className="w-1 bg-accent-primary rounded-full animate-pulse"
                  style={{
                    height: `${h * 4}px`,
                    animationDelay: `${i * 100}ms`,
                  }}
                />
              ))}
            </div>
          )}
          <svg
            className={`w-4 h-4 text-slate-500 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-slate-800">
          {/* Quick Commands Grid */}
          <div className="p-3 grid grid-cols-3 gap-2">
            {QUICK_COMMANDS.map(qc => (
              <button
                key={qc.label}
                onClick={() => sendCommand(qc.utterance)}
                className="flex flex-col items-center gap-1 p-2.5 bg-slate-800/60 hover:bg-slate-700/60 rounded-lg transition-colors text-center"
              >
                <span className="text-lg">{qc.icon}</span>
                <span className="text-[10px] text-slate-400 leading-tight">{qc.label}</span>
              </button>
            ))}
          </div>

          {/* Text Input */}
          <form onSubmit={handleSubmit} className="px-3 pb-3">
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={textInput}
                onChange={e => setTextInput(e.target.value)}
                placeholder="Type a command..."
                className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-accent-primary"
              />
              <button
                type="button"
                onClick={toggleListening}
                className={`p-2 rounded-lg transition-colors ${
                  state.listening
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-slate-800 hover:bg-slate-700 text-slate-400'
                }`}
              >
                🎤
              </button>
              <button
                type="submit"
                disabled={!textInput.trim()}
                className="px-3 py-2 bg-accent-primary hover:bg-blue-600 disabled:bg-slate-700 disabled:text-slate-500 rounded-lg text-sm font-medium transition-colors"
              >
                Send
              </button>
            </div>
          </form>

          {/* Command History */}
          {history.length > 0 && (
            <div className="border-t border-slate-800 max-h-48 overflow-y-auto">
              {history.slice(0, 5).map(cmd => (
                <div key={cmd.id} className="px-4 py-2 border-b border-slate-800/50 last:border-0">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-300 truncate flex-1">
                      &ldquo;{cmd.utterance}&rdquo;
                    </span>
                    <span className={`text-[10px] uppercase font-mono ml-2 ${
                      cmd.status === 'done' ? 'text-emerald-500' :
                      cmd.status === 'error' ? 'text-red-500' :
                      cmd.status === 'executing' ? 'text-blue-500 animate-pulse' :
                      'text-slate-500'
                    }`}>
                      {cmd.status}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-600 mt-0.5">
                    {cmd.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
