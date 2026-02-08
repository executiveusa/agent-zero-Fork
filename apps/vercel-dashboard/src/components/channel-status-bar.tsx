'use client';

import { AgentContext, OperationalState } from '@/types';

interface ChannelStatusProps {
  contexts: AgentContext[];
  operationalState: OperationalState;
}

const CHANNELS = [
  { id: 'whatsapp', label: 'WhatsApp', icon: '📱', color: '#25D366' },
  { id: 'telegram', label: 'Telegram', icon: '✈️', color: '#0088cc' },
  { id: 'discord', label: 'Discord', icon: '🎮', color: '#5865F2' },
  { id: 'slack', label: 'Slack', icon: '💼', color: '#4A154B' },
  { id: 'voice', label: 'Voice', icon: '📞', color: '#00D4AA' },
  { id: 'web', label: 'Web UI', icon: '🌐', color: '#3b82f6' },
];

export function ChannelStatusBar({ contexts, operationalState }: ChannelStatusProps) {
  // Derive which channels are active from contexts
  const activeChannelIds = new Set(
    contexts
      .filter(c => c.type)
      .map(c => c.type!.toLowerCase())
  );

  return (
    <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
      <h2 className="text-sm font-semibold text-slate-400 mb-3">CHANNELS</h2>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {CHANNELS.map(ch => {
          const active = activeChannelIds.has(ch.id) || (ch.id === 'web' && operationalState !== 'offline');
          return (
            <div
              key={ch.id}
              className={`flex-shrink-0 flex flex-col items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
                active ? 'bg-slate-800' : 'bg-slate-800/30 opacity-40'
              }`}
            >
              <div className="relative">
                <span className="text-lg">{ch.icon}</span>
                <div
                  className={`absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full border border-slate-900 ${
                    active ? 'bg-emerald-500' : 'bg-slate-600'
                  }`}
                />
              </div>
              <span className="text-[9px] text-slate-500 whitespace-nowrap">{ch.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
