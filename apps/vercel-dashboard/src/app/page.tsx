'use client';

import { useEffect, useState } from 'react';
import { PollResponse, OperationalState } from '@/types';
import { SynthiaVoicePanel, CronPanel, SystemStatusPanel, ChannelStatusBar } from '@/components';

export default function Home() {
  const [pollData, setPollData] = useState<PollResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [operationalState, setOperationalState] = useState<OperationalState>('offline');

  // Fetch /api/az/poll every 750ms
  useEffect(() => {
    let mounted = true;
    let intervalId: NodeJS.Timeout;

    const fetchPoll = async () => {
      try {
        const res = await fetch('/api/az/poll', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        });

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }

        const data = await res.json();
        
        if (mounted) {
          setPollData(data);
          setOperationalState(deriveOperationalState(data));
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Network error');
          setOperationalState('offline');
          setLoading(false);
        }
      }
    };

    // Initial fetch
    fetchPoll();

    // Poll every 750ms
    intervalId = setInterval(fetchPoll, 750);

    return () => {
      mounted = false;
      clearInterval(intervalId);
    };
  }, []);

  // Derive operational state from poll data
  const deriveOperationalState = (data: PollResponse): OperationalState => {
    if (!data) return 'offline';
    if (data.paused) return 'paused';
    if (data.log_progress_active) {
      if (data.log_progress.includes('error')) return 'error';
      if (data.log_progress.includes('waiting')) return 'waiting';
      return 'running';
    }
    if (data.tasks?.some(t => t.state === 'running')) return 'running';
    if (data.logs?.some(l => l.type === 'error')) return 'error';
    return 'idle';
  };

  // Get state color
  const getStateColor = (state: OperationalState): string => {
    const colors: Record<OperationalState, string> = {
      idle: 'text-emerald-500',
      planning: 'text-cyan-500',
      running: 'text-blue-500',
      waiting: 'text-amber-500',
      paused: 'text-purple-500',
      error: 'text-red-500',
      offline: 'text-slate-500',
    };
    return colors[state];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-slate-400">Connecting to Agent Zero...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="text-center">
          <div className="text-red-500 text-5xl mb-4">⚠</div>
          <h1 className="text-2xl font-bold text-red-500 mb-2">Connection Error</h1>
          <p className="text-slate-400 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950">
      {/* Top Status Bar */}
      <header className="bg-slate-900 border-b border-slate-800 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-2xl">🐾</div>
            <div>
              <h1 className="text-lg font-bold">Agent Claw</h1>
              <p className="text-sm text-slate-400">SYNTHIA Mission Control</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              operationalState === 'offline' ? 'bg-slate-500' :
              operationalState === 'error' ? 'bg-red-500 animate-pulse' :
              operationalState === 'running' ? 'bg-blue-500 animate-pulse' :
              'bg-emerald-500'
            }`}></div>
            <span className={`text-sm uppercase font-semibold ${getStateColor(operationalState)}`}>
              {operationalState}
            </span>
          </div>
        </div>
      </header>

      {/* Mission Control Grid */}
      <div className="p-4 space-y-4">
        {/* Active Context Card */}
        <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
          <h2 className="text-sm font-semibold text-slate-400 mb-3">ACTIVE CONTEXT</h2>
          {pollData?.context ? (
            <div>
              <p className="text-lg font-medium mb-1">{pollData.context}</p>
              {pollData.contexts?.find(c => c.id === pollData.context)?.project_name && (
                <div className="flex items-center gap-2 mt-2">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ 
                      backgroundColor: pollData.contexts.find(c => c.id === pollData.context)?.project_color || '#6b7280' 
                    }}
                  ></div>
                  <span className="text-sm text-slate-400">
                    {pollData.contexts.find(c => c.id === pollData.context)?.project_name}
                  </span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-slate-500 italic">No active context</p>
          )}
        </div>

        {/* Progress Bar */}
        {pollData?.log_progress_active && (
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
            <h2 className="text-sm font-semibold text-slate-400 mb-3">PROGRESS</h2>
            <div className="space-y-2">
              <p className="text-sm">{pollData.log_progress || 'Processing...'}</p>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div className="bg-blue-500 h-full animate-pulse" style={{ width: '60%' }}></div>
              </div>
            </div>
          </div>
        )}

        {/* SYNTHIA Voice Command Panel */}
        <SynthiaVoicePanel />

        {/* Channel Status */}
        <ChannelStatusBar
          contexts={pollData?.contexts || []}
          operationalState={operationalState}
        />

        {/* Scheduler / Cron Panel */}
        <CronPanel tasks={pollData?.tasks || []} />

        {/* System Status Panel */}
        <SystemStatusPanel />

        {/* Recent Logs Card */}
        <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
          <h2 className="text-sm font-semibold text-slate-400 mb-3">RECENT LOGS</h2>
          <div className="space-y-2">
            {pollData?.logs && pollData.logs.length > 0 ? (
              pollData.logs.slice(-5).reverse().map((log, idx) => (
                <div key={idx} className="text-sm border-l-2 border-slate-700 pl-3 py-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs uppercase text-slate-500 font-mono">{log.type}</span>
                    {log.heading && (
                      <span className="text-slate-300 font-medium">{log.heading}</span>
                    )}
                  </div>
                  {log.content && (
                    <p className="text-slate-400 text-xs line-clamp-2">{log.content}</p>
                  )}
                </div>
              ))
            ) : (
              <p className="text-slate-500 italic text-sm">No logs yet</p>
            )}
          </div>
        </div>

        {/* Active Tasks Card */}
        <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
          <h2 className="text-sm font-semibold text-slate-400 mb-3">ACTIVE TASKS</h2>
          <div className="space-y-2">
            {pollData?.tasks && pollData.tasks.length > 0 ? (
              pollData.tasks
                .filter(t => t.state === 'running')
                .map((task, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-slate-800 rounded p-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{task.task_name}</p>
                      <p className="text-xs text-slate-400">{task.type}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
                      <span className="text-xs uppercase text-blue-500 font-semibold">
                        {task.state}
                      </span>
                    </div>
                  </div>
                ))
            ) : (
              <p className="text-slate-500 italic text-sm">No active tasks</p>
            )}
          </div>
        </div>

        {/* Notifications Card */}
        {pollData?.notifications && pollData.notifications.length > 0 && (
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
            <h2 className="text-sm font-semibold text-slate-400 mb-3">NOTIFICATIONS</h2>
            <div className="space-y-2">
              {pollData.notifications.slice(-3).reverse().map((notif, idx) => (
                <div key={idx} className={`p-2 rounded border ${
                  notif.type === 'error' ? 'bg-red-950 border-red-800' :
                  notif.type === 'warning' ? 'bg-amber-950 border-amber-800' :
                  notif.type === 'success' ? 'bg-emerald-950 border-emerald-800' :
                  'bg-blue-950 border-blue-800'
                }`}>
                  <p className="text-sm font-medium">{notif.title}</p>
                  <p className="text-xs text-slate-400 mt-1">{notif.message}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Paused State */}
        {pollData?.paused && (
          <div className="bg-purple-950 border border-purple-800 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="text-2xl">⏸️</div>
              <div>
                <h3 className="font-semibold text-purple-300">Agent Paused</h3>
                <p className="text-sm text-purple-400">All operations are suspended</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Navigation Placeholder */}
      <nav className="fixed bottom-0 left-0 right-0 bg-slate-900 border-t border-slate-800 p-2">
        <div className="flex justify-around items-center">
          <button className="flex flex-col items-center p-2 text-blue-500">
            <span className="text-xl">🎯</span>
            <span className="text-xs mt-1">Mission</span>
          </button>
          <button className="flex flex-col items-center p-2 text-slate-400">
            <span className="text-xl">💬</span>
            <span className="text-xs mt-1">Chats</span>
          </button>
          <button className="flex flex-col items-center p-2 text-slate-400">
            <span className="text-xl">📋</span>
            <span className="text-xs mt-1">Tasks</span>
          </button>
          <button className="flex flex-col items-center p-2 text-slate-400">
            <span className="text-xl">⚙️</span>
            <span className="text-xs mt-1">Settings</span>
          </button>
        </div>
      </nav>

      {/* Bottom padding for nav */}
      <div className="h-20"></div>
    </main>
  );
}
