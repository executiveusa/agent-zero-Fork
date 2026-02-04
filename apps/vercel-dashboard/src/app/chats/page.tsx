import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Chats - Agent Zero',
};

export default function ChatsPage() {
  return (
    <main className="min-h-screen bg-slate-950 pb-20">
      <header className="bg-slate-900 border-b border-slate-800 p-4">
        <h1 className="text-2xl font-bold">Chats</h1>
      </header>
      <div className="p-4">
        <div className="text-center py-12 text-slate-400">
          <p>No chats yet</p>
        </div>
      </div>
    </main>
  );
}
