'use client';

import React from 'react';
import { Bot, RefreshCw } from 'lucide-react';

interface HeaderProps {
  backendOnline: boolean;
  onResetChat: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  backendOnline,
  onResetChat
}) => {
  return (
    <header className="sticky top-0 z-30 w-full border-b border-gray-200 bg-white/95 backdrop-blur-sm px-4 sm:px-8 py-3.5 flex items-center justify-between shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gray-900 text-white font-medium shadow-sm">
          <Bot className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-semibold text-gray-900 tracking-tight">Autonomous Research Assistant</h1>
            <span className="flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-medium text-gray-600 bg-gray-100 rounded-full border border-gray-200/80">
              <span className={`w-1.5 h-1.5 rounded-full ${backendOnline ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
              {backendOnline ? 'Ready' : 'Connecting'}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onResetChat}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 hover:text-gray-900 bg-white hover:bg-gray-50 border border-gray-200 hover:border-gray-300 rounded-lg transition-colors shadow-2xs"
          title="Start a new research session"
        >
          <RefreshCw className="w-3.5 h-3.5 text-gray-500" />
          <span>New Session</span>
        </button>
      </div>
    </header>
  );
};
