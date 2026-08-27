'use client';

import React from 'react';
import { Globe, MessageSquare } from 'lucide-react';
import { ChatSettings } from '@/types/chat';

interface ToolToggleBarProps {
  settings: ChatSettings;
  onUpdateSettings: (updater: (prev: ChatSettings) => ChatSettings) => void;
  disabled?: boolean;
}

export const ToolToggleBar: React.FC<ToolToggleBarProps> = ({
  settings,
  onUpdateSettings,
  disabled = false,
}) => {
  const toggleWebSearch = () => {
    onUpdateSettings((prev) => ({
      ...prev,
      enableWebSearch: !prev.enableWebSearch,
    }));
  };

  const toggleSlack = () => {
    onUpdateSettings((prev) => ({
      ...prev,
      enableSlack: !prev.enableSlack,
    }));
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 bg-gray-50/90 border border-gray-200/90 rounded-xl text-xs mb-2 shadow-2xs">
      <div className="flex flex-wrap items-center gap-2">
        {/* Web search toggle button */}
        <button
          type="button"
          disabled={disabled}
          onClick={toggleWebSearch}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
            settings.enableWebSearch
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-300/80 shadow-2xs'
              : 'bg-white text-gray-500 border border-gray-200 hover:text-gray-700'
          }`}
        >
          <Globe className={`w-3.5 h-3.5 ${settings.enableWebSearch ? 'text-emerald-600' : 'text-gray-400'}`} />
          <span>Web Search: {settings.enableWebSearch ? 'ON' : 'OFF'}</span>
        </button>

        {/* Slack toggle button */}
        <button
          type="button"
          disabled={disabled}
          onClick={toggleSlack}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
            settings.enableSlack
              ? 'bg-indigo-50 text-indigo-700 border border-indigo-300/80 shadow-2xs'
              : 'bg-white text-gray-500 border border-gray-200 hover:text-gray-700'
          }`}
          title="Direct Slack messaging to Mohsin Ali (U0B9C2GPEDC)"
        >
          <MessageSquare className={`w-3.5 h-3.5 ${settings.enableSlack ? 'text-indigo-600' : 'text-gray-400'}`} />
          <span>Slack (Mohsin Ali): {settings.enableSlack ? 'Active' : 'Muted'}</span>
        </button>
      </div>

      <span className="text-[11px] text-gray-400 hidden sm:inline">
        Autonomous Tool-Calling
      </span>
    </div>
  );
};
