'use client';

import { useState, useEffect } from 'react';

interface ServiceStatus {
  name: string;
  status: 'up' | 'down' | 'degraded' | 'unknown';
  latency?: number;
  detail?: string;
}

interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  containers: { total: number; running: number; stopped: number };
  uptime: string;
}

const statusColors: Record<string, string> = {
  up: 'bg-emerald-500',
  down: 'bg-red-500',
  degraded: 'bg-amber-500',
  unknown: 'bg-slate-500',
};

const statusLabels: Record<string, string> = {
  up: 'Operational',
  down: 'Down',
  degraded: 'Degraded',
  unknown: 'Unknown',
};

export function SystemStatusPanel() {
  const [expanded, setExpanded] = useState(false);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: 'Agent Zero', status: 'unknown' },
    { name: 'OpenClaw Gateway', status: 'unknown' },
    { name: 'Venice AI', status: 'unknown' },
    { name: 'ElevenLabs TTS', status: 'unknown' },
    { name: 'Docker Engine', status: 'unknown' },
    { name: 'MCP Server', status: 'unknown' },
  ]);

  // Poll health endpoint
  useEffect(() => {
    if (!expanded) return;

    const checkHealth = async () => {
      try {
        const res = await fetch('/api/az/health');
        if (res.ok) {
          const data = await res.json();
          // Update Agent Zero status
          setServices(prev =>
            prev.map(s =>
              s.name === 'Agent Zero' ? { ...s, status: 'up' as const, detail: data.status } : s
            )
          );
          if (data.metrics) {
            setMetrics({
              cpu: data.metrics.cpu || 0,
              memory: data.metrics.memory || 0,
              disk: data.metrics.disk || 0,
              containers: data.metrics.containers || { total: 0, running: 0, stopped: 0 },
              uptime: data.metrics.uptime || '—',
            });
          }
        } else {
          setServices(prev =>
            prev.map(s =>
              s.name === 'Agent Zero' ? { ...s, status: 'down' as const } : s
            )
          );
        }
      } catch {
        setServices(prev =>
          prev.map(s =>
            s.name === 'Agent Zero' ? { ...s, status: 'down' as const } : s
          )
        );
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, [expanded]);

  const overallStatus = services.some(s => s.status === 'down')
    ? 'degraded'
    : services.every(s => s.status === 'up')
    ? 'up'
    : 'unknown';

  const upCount = services.filter(s => s.status === 'up').length;

  return (
    <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">🖥️</span>
          <div className="text-left">
            <h2 className="text-sm font-semibold text-slate-200">System Status</h2>
            <p className="text-xs text-slate-500">
              {upCount}/{services.length} services operational
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${statusColors[overallStatus]}`} />
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
          {/* Resource Meters */}
          {metrics && (
            <div className="p-4 grid grid-cols-3 gap-3">
              {[
                { label: 'CPU', value: metrics.cpu, color: 'bg-cyan-500' },
                { label: 'RAM', value: metrics.memory, color: 'bg-purple-500' },
                { label: 'Disk', value: metrics.disk, color: 'bg-amber-500' },
              ].map(m => (
                <div key={m.label} className="text-center">
                  <div className="relative w-14 h-14 mx-auto">
                    <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                      <circle
                        cx="18" cy="18" r="15.5"
                        fill="none" stroke="#1e293b" strokeWidth="3"
                      />
                      <circle
                        cx="18" cy="18" r="15.5"
                        fill="none"
                        className={m.color.replace('bg-', 'stroke-')}
                        strokeWidth="3"
                        strokeDasharray={`${m.value} ${100 - m.value}`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-slate-200">
                      {m.value}%
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">{m.label}</p>
                </div>
              ))}
            </div>
          )}

          {/* Services List */}
          <div className="divide-y divide-slate-800/50">
            {services.map(svc => (
              <div key={svc.name} className="px-4 py-2.5 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className={`w-2 h-2 rounded-full ${statusColors[svc.status]} ${
                    svc.status === 'down' ? 'animate-pulse' : ''
                  }`} />
                  <span className="text-sm text-slate-300">{svc.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  {svc.latency !== undefined && (
                    <span className="text-[10px] text-slate-600 font-mono">{svc.latency}ms</span>
                  )}
                  <span className={`text-[10px] font-medium ${
                    svc.status === 'up' ? 'text-emerald-500' :
                    svc.status === 'down' ? 'text-red-500' :
                    svc.status === 'degraded' ? 'text-amber-500' :
                    'text-slate-500'
                  }`}>
                    {statusLabels[svc.status]}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Docker Containers */}
          {metrics?.containers && (
            <div className="border-t border-slate-800 px-4 py-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Docker Containers</span>
                <div className="flex items-center gap-2 text-[10px]">
                  <span className="text-emerald-500">{metrics.containers.running} running</span>
                  <span className="text-slate-600">·</span>
                  <span className="text-slate-500">{metrics.containers.stopped} stopped</span>
                </div>
              </div>
            </div>
          )}

          {/* Uptime */}
          {metrics?.uptime && (
            <div className="border-t border-slate-800 px-4 py-2 text-center">
              <span className="text-[10px] text-slate-600">Uptime: {metrics.uptime}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
