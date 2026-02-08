'use client';

import { useState } from 'react';
import { SchedulerTask, CronSchedule } from '@/types';

interface CronPanelProps {
  tasks: SchedulerTask[];
}

function formatCron(schedule?: CronSchedule): string {
  if (!schedule) return '—';
  const { minute, hour, day, month, weekday } = schedule;
  // Human-readable shortcuts
  if (minute === '0' && hour === '8' && day === '*' && month === '*' && weekday === '1-5')
    return 'Weekdays 8:00 AM';
  if (minute === '0' && hour === '*' && day === '*') return `Every hour`;
  if (minute === '*/30') return 'Every 30 min';
  if (minute === '*/15') return 'Every 15 min';
  if (minute === '0' && day === '*' && month === '*' && weekday === '*')
    return `Daily ${hour}:00`;
  return `${minute} ${hour} ${day} ${month} ${weekday}`;
}

function formatLastRun(dateStr?: string): string {
  if (!dateStr) return 'Never';
  const d = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return d.toLocaleDateString();
}

const stateColors: Record<string, string> = {
  idle: 'bg-emerald-500/20 text-emerald-400',
  running: 'bg-blue-500/20 text-blue-400',
  disabled: 'bg-slate-500/20 text-slate-400',
  error: 'bg-red-500/20 text-red-400',
};

const typeIcons: Record<string, string> = {
  adhoc: '⚡',
  scheduled: '🔄',
  planned: '📅',
};

export function CronPanel({ tasks }: CronPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [filter, setFilter] = useState<'all' | 'scheduled' | 'planned' | 'adhoc'>('all');

  const filtered = filter === 'all' ? tasks : tasks.filter(t => t.type === filter);
  const activeCount = tasks.filter(t => t.state === 'running').length;
  const scheduledCount = tasks.filter(t => t.type === 'scheduled').length;

  return (
    <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">⏱️</span>
          <div className="text-left">
            <h2 className="text-sm font-semibold text-slate-200">Scheduler</h2>
            <p className="text-xs text-slate-500">
              {scheduledCount} cron{scheduledCount !== 1 ? 's' : ''} · {activeCount} active
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {activeCount > 0 && (
            <span className="px-1.5 py-0.5 text-[10px] font-bold bg-blue-500/20 text-blue-400 rounded">
              {activeCount} RUNNING
            </span>
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
          {/* Filters */}
          <div className="p-3 flex gap-1.5">
            {(['all', 'scheduled', 'planned', 'adhoc'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-2.5 py-1 text-[11px] rounded-full capitalize transition-colors ${
                  filter === f
                    ? 'bg-accent-primary text-white'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                {f === 'all' ? `All (${tasks.length})` : `${f} (${tasks.filter(t => t.type === f).length})`}
              </button>
            ))}
          </div>

          {/* Task List */}
          <div className="max-h-64 overflow-y-auto">
            {filtered.length > 0 ? (
              filtered.map(task => (
                <div
                  key={task.uuid}
                  className="px-4 py-3 border-t border-slate-800/50 hover:bg-slate-800/30 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm">{typeIcons[task.type] || '📌'}</span>
                        <span className="text-sm font-medium text-slate-200 truncate">
                          {task.task_name}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 mt-1.5">
                        {task.type === 'scheduled' && task.schedule && (
                          <span className="text-[10px] text-slate-500 font-mono">
                            {formatCron(task.schedule)}
                          </span>
                        )}
                        <span className="text-[10px] text-slate-600">
                          Last: {formatLastRun(task.last_run)}
                        </span>
                      </div>
                    </div>
                    <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded uppercase ${
                      stateColors[task.state] || stateColors.idle
                    }`}>
                      {task.state}
                    </span>
                  </div>
                  {task.last_result && (
                    <p className="text-[10px] text-slate-500 mt-1.5 line-clamp-1 pl-6">
                      {task.last_result}
                    </p>
                  )}
                </div>
              ))
            ) : (
              <div className="px-4 py-6 text-center">
                <p className="text-slate-500 text-sm italic">No tasks found</p>
              </div>
            )}
          </div>

          {/* Footer Summary */}
          <div className="border-t border-slate-800 px-4 py-2 flex justify-between text-[10px] text-slate-600">
            <span>{tasks.filter(t => t.state === 'error').length} errors</span>
            <span>{tasks.filter(t => t.type === 'scheduled').length} cron jobs</span>
            <span>{tasks.filter(t => t.type === 'planned').length} planned</span>
          </div>
        </div>
      )}
    </div>
  );
}
