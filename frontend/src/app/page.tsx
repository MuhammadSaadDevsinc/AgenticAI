'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Globe, AlertTriangle } from 'lucide-react';
import { Header } from '@/components/Header';
import { ToolToggleBar } from '@/components/ToolToggleBar';
import { ChatMessage } from '@/components/ChatMessage';
import { EmptyState } from '@/components/EmptyState';
import { Message, ChatSettings, AgentStepEvent } from '@/types/chat';
import { sendChatMessage, checkBackendHealth } from '@/lib/api';

const DEFAULT_SETTINGS: ChatSettings = {
  enableWebSearch: true,
  enableSlack: true,
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState<string>('');
  const [activeSteps, setActiveSteps] = useState<AgentStepEvent[]>([]);
  const [settings, setSettings] = useState<ChatSettings>(DEFAULT_SETTINGS);
  const [backendOnline, setBackendOnline] = useState(false);
  const [backendError, setBackendError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Check backend health on mount
  useEffect(() => {
    const pingBackend = async () => {
      const health = await checkBackendHealth();
      if (health.status === 'healthy') {
        setBackendOnline(true);
        setBackendError(null);
      } else {
        setBackendOnline(false);
        setBackendError('FastAPI backend is unreachable at localhost:8000.');
      }
    };
    pingBackend();
    const interval = setInterval(pingBackend, 10000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll on new messages or loading steps
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeSteps, loadingStep]);

  // Adjust textarea height dynamically
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  };

  const handleResetChat = () => {
    setMessages([]);
    setActiveSteps([]);
    setLoadingStep('');
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || isLoading) return;

    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    const userMessage: Message = {
      role: 'user',
      content: query,
    };

    const newHistory = [...messages, userMessage];
    setMessages(newHistory);
    setIsLoading(true);

    const initialStep: AgentStepEvent = {
      step_id: 'step_init',
      step_type: 'thinking',
      message: 'Analyzing inquiry and planning research workflow...',
      timestamp: Date.now(),
    };
    setActiveSteps([initialStep]);
    setLoadingStep('Planning research strategy...');

    try {
      if (settings.enableWebSearch) {
        setTimeout(() => {
          if (isLoading) {
            setActiveSteps((prev) => [
              ...prev,
              {
                step_id: 'step_search',
                step_type: 'tool_executing',
                message: `Executing Tavily Search for: "${query.slice(0, 45)}..."`,
                timestamp: Date.now(),
              },
            ]);
            setLoadingStep('Searching the web with Tavily API...');
          }
        }, 500);
      }

      const response = await sendChatMessage({
        messages: newHistory.map((m) => ({
          role: m.role,
          content: m.content,
          name: m.name,
          tool_call_id: m.tool_call_id,
          tool_calls: m.tool_calls,
        })),
        enable_web_search: settings.enableWebSearch,
        enable_slack: settings.enableSlack,
        search_depth: 'basic',
        max_results: 5,
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.message.content,
        sources: response.sources,
        execution_steps: response.execution_steps,
        tool_records: response.tool_records,
        slack_deliveries: response.slack_deliveries,
        suggested_follow_ups: response.suggested_follow_ups,
        duration_ms: response.total_duration_ms,
        model_used: response.model_used,
      };

      setMessages([...newHistory, assistantMessage]);
    } catch (error: any) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: `⚠️ **Agent Error**: ${error.message || 'Failed to process request.'}`,
      };
      setMessages([...newHistory, errorMessage]);
    } finally {
      setIsLoading(false);
      setActiveSteps([]);
      setLoadingStep('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-white text-gray-900 selection:bg-indigo-100 selection:text-indigo-900">
      {/* Header */}
      <Header
        backendOnline={backendOnline}
        onResetChat={handleResetChat}
      />

      {/* Backend Disconnected Warning Banner */}
      {!backendOnline && (
        <div className="w-full bg-amber-50 border-b border-amber-200 px-4 py-2 text-xs text-amber-800 flex items-center justify-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>FastAPI backend not detected at localhost:8000.</span>
        </div>
      )}

      {/* Main Chat Content Area */}
      <main className="flex-1 flex flex-col max-w-3xl w-full mx-auto px-4 sm:px-6 pt-4 pb-36">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-2">
            {messages.map((msg, index) => (
              <ChatMessage
                key={index}
                message={msg}
              />
            ))}

            {/* In-Progress Indicator */}
            {isLoading && (
              <div className="flex items-start gap-2.5 py-3 max-w-3xl mx-auto">
                <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gray-900 text-white shrink-0 shadow-sm">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="p-3.5 rounded-2xl bg-gray-50 border border-gray-200 space-y-2">
                    <div className="flex items-center gap-2 text-xs text-gray-700 font-medium">
                      <Globe className="w-3.5 h-3.5 text-emerald-600 animate-spin" />
                      <span>{loadingStep || 'Searching & analyzing data...'}</span>
                    </div>
                    <div className="h-1 w-full bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-600 animate-pulse rounded-full w-2/3"></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      {/* Floating Input Dock */}
      <footer className="fixed bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-white via-white/95 to-transparent pt-4 pb-4 px-4 sm:px-6">
        <div className="max-w-3xl mx-auto w-full">
          {/* Tool Toggles Bar */}
          <ToolToggleBar
            settings={settings}
            onUpdateSettings={setSettings}
            disabled={isLoading}
          />

          {/* Prompt Input Box */}
          <div className="relative flex items-end gap-2 p-1.5 rounded-2xl bg-white border border-gray-300 focus-within:border-indigo-600 focus-within:ring-2 focus-within:ring-indigo-100 shadow-sm transition">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask a research inquiry (e.g. 'Research solid-state batteries in 2026 and message Mohsin Ali')..."
              rows={1}
              disabled={isLoading}
              className="w-full resize-none bg-transparent px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none max-h-40 disabled:opacity-50"
            />

            <button
              onClick={() => handleSendMessage()}
              disabled={!input.trim() || isLoading}
              className="flex items-center justify-center w-8 h-8 rounded-xl bg-gray-900 hover:bg-gray-800 text-white transition disabled:opacity-30 disabled:cursor-not-allowed shrink-0 mb-0.5"
              title="Submit research inquiry"
            >
              {isLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5" />
              )}
            </button>
          </div>

          <div className="flex items-center justify-center mt-1.5 px-1 text-[11px] text-gray-400">
            <span>Press <kbd className="px-1 py-0.5 rounded bg-gray-100 border border-gray-200 font-mono text-[10px]">Enter</kbd> to send, <kbd className="px-1 py-0.5 rounded bg-gray-100 border border-gray-200 font-mono text-[10px]">Shift+Enter</kbd> for newline</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
