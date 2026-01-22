import AgentControlPanel from '@/components/AgentControlPanel';

export const metadata = {
  title: 'Agent Zero - AI Agent Platform',
  description: 'Autonomous AI Agent Platform with Voice Control',
};

export default function Home() {
  return (
    <main className="w-full h-screen">
      <AgentControlPanel />
    </main>
  );
}
