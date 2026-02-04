import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Settings - Agent Zero',
};

export default function SettingsPage() {
  return (
    <main className="min-h-screen bg-slate-950 pb-20">
      <header className="bg-slate-900 border-b border-slate-800 p-4">
        <h1 className="text-2xl font-bold">Settings</h1>
      </header>
      <div className="p-4">
        <div className="space-y-4">
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
            <h2 className="font-semibold mb-2">Backend Configuration</h2>
            <p className="text-sm text-slate-400">Configure connection to Agent Zero backend</p>
          </div>
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
            <h2 className="font-semibold mb-2">Dashboard Preferences</h2>
            <p className="text-sm text-slate-400">Customize dashboard appearance and behavior</p>
          </div>
        </div>
      </div>
    </main>
  );
}
