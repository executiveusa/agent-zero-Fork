'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Mic, Send, Settings, Volume2, VolumeX, Zap, Brain } from 'lucide-react';

interface AgentMessage {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
  agent?: string;
  status?: 'sent' | 'delivered' | 'read';
}

interface AgentStatus {
  name: string;
  status: 'idle' | 'processing' | 'executing';
  role: string;
  icon: string;
}

export default function AgentControlPanel() {
  const [messages, setMessages] = useState<AgentMessage[]>([
    {
      id: '1',
      role: 'agent',
      content: 'Hello! I\'m Agent Zero. I can help you with code, design, DevOps, and automation tasks. How can I assist you today?',
      timestamp: new Date(),
      agent: 'Agent Zero',
      status: 'delivered',
    },
  ]);
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [agentStatus, setAgentStatus] = useState<AgentStatus[]>([
    { name: 'ClaudeCode', status: 'idle', role: 'Development', icon: '💻' },
    { name: 'Cynthia', status: 'idle', role: 'Design', icon: '🎨' },
    { name: 'Switchblade', status: 'idle', role: 'DevOps', icon: '⚙️' },
  ]);
  const [isSpeechEnabled, setIsSpeechEnabled] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [theme, setTheme] = useState('dark');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  // Initialize Speech Recognition
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onstart = () => setIsListening(true);
      recognitionRef.current.onend = () => setIsListening(false);

      recognitionRef.current.onresult = (event: any) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }

        if (finalTranscript) {
          setInput(prev => (prev + ' ' + finalTranscript).trim());
        } else if (interimTranscript) {
          setInput(prev => (prev.replace(/\s*\S*$/, '') + ' ' + interimTranscript).trim());
        }
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech Recognition Error:', event.error);
        setIsListening(false);
      };
    }
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleVoiceInput = () => {
    if (!recognitionRef.current) {
      alert('Speech Recognition not supported in this browser');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: AgentMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
      status: 'sent',
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // First try Docker backend
      let response = await fetch('http://localhost:3000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          timestamp: userMessage.timestamp,
        }),
      }).catch(() => null);

      let agentReply = '';
      let agentName = 'Agent Zero';

      if (response?.ok) {
        const data = await response.json();
        agentReply = data.response || 'Processing completed.';
        agentName = data.agent || 'Agent Zero';
      } else {
        // Fallback response
        agentReply = `I received your message: "${userMessage.content}". I'm currently training. To use me fully, make sure the Docker backend is running with: docker-compose up -d`;
        agentName = 'Agent Zero (Demo Mode)';
      }

      const agentMessage: AgentMessage = {
        id: `agent-${Date.now()}`,
        role: 'agent',
        content: agentReply,
        timestamp: new Date(),
        agent: agentName,
        status: 'delivered',
      };

      setMessages(prev => [...prev, agentMessage]);

      // Text-to-speech
      if (isSpeechEnabled && typeof window !== 'undefined' && 'speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(agentReply);
        utterance.rate = 0.95;
        utterance.pitch = 1;
        utterance.volume = 1;
        window.speechSynthesis.speak(utterance);
      }

      // Update agent status randomly to simulate activity
      const agentIndex = Math.floor(Math.random() * agentStatus.length);
      setAgentStatus(prev =>
        prev.map((a, i) =>
          i === agentIndex ? { ...a, status: 'idle' as const } : a
        )
      );
    } catch (err) {
      const errorMessage: AgentMessage = {
        id: `error-${Date.now()}`,
        role: 'agent',
        content: 'Connection error. Please ensure Docker containers are running.',
        timestamp: new Date(),
        agent: 'System',
        status: 'delivered',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'executing':
        return 'from-amber-400 to-amber-600';
      case 'processing':
        return 'from-blue-400 to-blue-600';
      case 'idle':
      default:
        return 'from-green-400 to-green-600';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'executing':
        return 'bg-amber-500/20 border-amber-500/30';
      case 'processing':
        return 'bg-blue-500/20 border-blue-500/30';
      case 'idle':
      default:
        return 'bg-green-500/20 border-green-500/30';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      {/* Main Container */}
      <div className="relative z-10 max-w-7xl mx-auto h-screen p-6 flex flex-col">
        {/* Header */}
        <div className="mb-6 pb-6 border-b border-slate-700/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl">
                <Brain size={28} />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
                  Agent Zero
                </h1>
                <p className="text-sm text-slate-400">AI-Powered Autonomous Agent Platform</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-green-400">● Live</p>
              <p className="text-xs text-slate-400">Docker Connected</p>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-0">
          {/* Chat Area - Main */}
          <div className="lg:col-span-3 flex flex-col space-y-4">
            {/* Messages Container */}
            <div className="flex-1 bg-slate-900/50 backdrop-blur-xl border border-slate-700/30 rounded-2xl p-6 overflow-y-auto space-y-4 min-h-0">
              {messages.map(msg => (
                <div
                  key={msg.id}
                  className={`flex gap-4 animate-in fade-in slide-in-from-bottom-2 ${
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {msg.role === 'agent' && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center flex-shrink-0 text-sm font-bold">
                      AI
                    </div>
                  )}
                  <div
                    className={`max-w-xs lg:max-w-md px-5 py-3 rounded-2xl backdrop-blur-sm transition-all ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-blue-600 to-blue-700 rounded-br-none shadow-lg shadow-blue-500/20'
                        : 'bg-slate-800/80 border border-slate-700/50 rounded-bl-none'
                    }`}
                  >
                    {msg.agent && msg.role === 'agent' && (
                      <p className="text-xs font-semibold text-cyan-300 mb-1 uppercase tracking-wide">
                        {msg.agent}
                      </p>
                    )}
                    <p className="text-sm leading-relaxed break-words">{msg.content}</p>
                    <p className="text-xs text-slate-400 mt-2 opacity-70">
                      {msg.timestamp.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0 text-sm font-bold">
                      U
                    </div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-4 justify-start">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center flex-shrink-0">
                    <Zap size={16} />
                  </div>
                  <div className="bg-slate-800/80 border border-slate-700/50 px-5 py-3 rounded-2xl rounded-bl-none">
                    <div className="flex gap-2">
                      <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" />
                      <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce delay-100" />
                      <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce delay-200" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="space-y-3">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Type or use voice... (e.g., 'Create a React component', 'Generate UI design')"
                  className="flex-1 bg-slate-800/50 border border-slate-600/50 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400/50 focus:ring-2 focus:ring-cyan-400/20 transition-all backdrop-blur-sm"
                />
                <button
                  onClick={handleVoiceInput}
                  className={`px-4 py-3 rounded-xl font-semibold transition-all flex items-center gap-2 ${
                    isListening
                      ? 'bg-red-600/80 hover:bg-red-700 shadow-lg shadow-red-500/50'
                      : 'bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/50'
                  }`}
                  title="Click to start/stop voice input"
                >
                  <Mic size={18} />
                  {isListening && <span className="text-xs">Listening...</span>}
                </button>
                <button
                  onClick={handleSendMessage}
                  disabled={isLoading || !input.trim()}
                  className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-xl font-semibold hover:from-cyan-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2 shadow-lg shadow-cyan-500/30 hover:shadow-cyan-500/50"
                >
                  <Send size={18} />
                  Send
                </button>
              </div>

              {/* Controls */}
              <div className="flex gap-3 flex-wrap">
                <button
                  onClick={() => setIsSpeechEnabled(!isSpeechEnabled)}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/50 rounded-lg transition-all text-sm font-medium"
                  title="Toggle audio responses"
                >
                  {isSpeechEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
                  {isSpeechEnabled ? 'Audio On' : 'Audio Off'}
                </button>
                <button
                  onClick={() => setMessages([messages[0]])}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/50 rounded-lg transition-all text-sm font-medium"
                  title="Clear chat history"
                >
                  Clear Chat
                </button>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="flex flex-col gap-4">
            {/* Agent Status */}
            <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/30 rounded-2xl p-5">
              <h2 className="text-sm font-bold text-cyan-400 mb-4 uppercase tracking-wider">Active Agents</h2>
              <div className="space-y-3">
                {agentStatus.map(agent => (
                  <div
                    key={agent.name}
                    className={`p-3 rounded-xl border transition-all ${getStatusBg(agent.status)}`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-semibold text-sm">{agent.icon} {agent.name}</p>
                        <p className="text-xs text-slate-400 mt-1">{agent.role}</p>
                      </div>
                      <div className={`w-2.5 h-2.5 rounded-full bg-gradient-to-r ${getStatusColor(agent.status)} animate-pulse`} />
                    </div>
                    <div className="mt-2 text-xs text-slate-400 capitalize">
                      {agent.status === 'idle' && '◌ Idle'}
                      {agent.status === 'processing' && '◔ Processing'}
                      {agent.status === 'executing' && '◕ Executing'}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* System Info */}
            <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/30 rounded-2xl p-5">
              <h2 className="text-sm font-bold text-cyan-400 mb-4 uppercase tracking-wider">System</h2>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Backend</span>
                  <span className="text-green-400 font-semibold">Connected</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Docker</span>
                  <span className="text-green-400 font-semibold">Running</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Memory</span>
                  <span className="text-green-400 font-semibold">Active</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Voice</span>
                  <span className={isSpeechEnabled ? 'text-green-400 font-semibold' : 'text-slate-500'}>
                    {isSpeechEnabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/30 rounded-2xl p-5">
              <h2 className="text-sm font-bold text-cyan-400 mb-4 uppercase tracking-wider">Tips</h2>
              <ul className="space-y-2 text-xs text-slate-300">
                <li>• Say "code" for development tasks</li>
                <li>• Say "design" for UI/UX creation</li>
                <li>• Say "deploy" for DevOps help</li>
                <li>• Press Enter to send messages</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
