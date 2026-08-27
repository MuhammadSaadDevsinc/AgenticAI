'use client';

import React from 'react';
import { Search, MessageSquare, Wrench } from 'lucide-react';
import { AgentStepEvent, ToolExecutionRecord } from '@/types/chat';

interface ExecutionStepsViewProps {
  steps?: AgentStepEvent[];
  toolRecords?: ToolExecutionRecord[];
  isStreaming?: boolean;
}

export const ExecutionStepsView: React.FC<ExecutionStepsViewProps> = ({
  steps = [],
  toolRecords = [],
}) => {
  const searchTool = toolRecords.find((t) => t.tool_name === 'tavily_search');
  const slackTool = toolRecords.find((t) => t.tool_name === 'slack_post_message');

  if (!searchTool && !slackTool && steps.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5 mb-2.5 text-xs">
      <span className="flex items-center gap-1 text-[11px] font-medium text-gray-500">
        <Wrench className="w-3 h-3 text-gray-400" />
        <span>Tools:</span>
      </span>

      {searchTool && (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200/80 text-[11px] font-medium">
          <Search className="w-3 h-3 text-emerald-600" />
          <span>Tavily Search ({searchTool.result?.count || 5} sources)</span>
        </span>
      )}

      {slackTool && (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200/80 text-[11px] font-medium">
          <MessageSquare className="w-3 h-3 text-indigo-600" />
          <span>Slack DM (Mohsin Ali)</span>
        </span>
      )}
    </div>
  );
};
