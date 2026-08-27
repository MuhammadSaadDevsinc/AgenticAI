'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, Copy, Check, Link2, ExternalLink } from 'lucide-react';
import { Message } from '@/types/chat';
import { ExecutionStepsView } from './ExecutionStepsView';
import { SlackDeliveryCard } from './SlackDeliveryCard';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = () => {
    if (message.content) {
      navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isUser) {
    return (
      <div className="flex items-start justify-end gap-2.5 max-w-3xl mx-auto py-2">
        <div className="flex flex-col items-end max-w-[85%] sm:max-w-[75%] min-w-0">
          <div className="px-4 py-2.5 rounded-2xl rounded-tr-sm bg-gray-900 text-white text-sm leading-relaxed shadow-sm break-words [overflow-wrap:anywhere]">
            {message.content}
          </div>
        </div>
        <div className="flex items-center justify-center w-7 h-7 rounded-full bg-gray-100 border border-gray-200 text-gray-700 shrink-0 text-xs mt-0.5">
          <User className="w-3.5 h-3.5" />
        </div>
      </div>
    );
  }

  // Check if references are already formatted in markdown
  const hasMarkdownReferences = message.content?.toLowerCase().includes('### references') || 
                                message.content?.toLowerCase().includes('## references');

  return (
    <div className="flex items-start gap-2.5 max-w-3xl mx-auto py-3 min-w-0">
      {/* Assistant Avatar */}
      <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gray-900 text-white shrink-0 mt-1 shadow-sm">
        <Bot className="w-3.5 h-3.5" />
      </div>

      <div className="flex-1 min-w-0">
        {/* Header: Title & Copy */}
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-gray-900">Research Assistant</span>
            {message.model_used && (
              <span className="inline-flex items-center px-1.5 py-0.2 text-[10px] font-mono bg-gray-100 text-gray-600 rounded border border-gray-200">
                {message.model_used.split('/').pop()?.replace('-versatile', '')}
              </span>
            )}
          </div>

          {message.content && (
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium text-gray-600 hover:text-gray-900 bg-white hover:bg-gray-50 border border-gray-200 rounded transition shadow-2xs"
              title="Copy markdown report"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3 text-emerald-600" />
                  <span className="text-emerald-700">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3 text-gray-500" />
                  <span>Copy</span>
                </>
              )}
            </button>
          )}
        </div>

        {/* Tools Used Indicator */}
        <ExecutionStepsView
          steps={message.execution_steps}
          toolRecords={message.tool_records}
          isStreaming={message.isStreaming}
        />

        {/* Slack Delivery Note */}
        {message.slack_deliveries && message.slack_deliveries.length > 0 && (
          <div className="mb-2.5">
            {message.slack_deliveries.map((deliv, idx) => (
              <SlackDeliveryCard key={idx} delivery={deliv} />
            ))}
          </div>
        )}

        {/* Research Report Content */}
        {message.content && (
          <div className="p-5 rounded-2xl bg-white border border-gray-200 text-gray-900 text-sm leading-relaxed shadow-2xs break-words overflow-hidden [overflow-wrap:anywhere]">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => <h1 className="text-base font-bold text-gray-900 mt-1 mb-2.5 pb-1.5 border-b border-gray-200 break-words [overflow-wrap:anywhere]">{children}</h1>,
                h2: ({ children }) => <h2 className="text-sm font-semibold text-gray-900 mt-3.5 mb-1.5 break-words [overflow-wrap:anywhere]">{children}</h2>,
                h3: ({ children }) => <h3 className="text-xs font-semibold text-gray-800 mt-2.5 mb-1 break-words [overflow-wrap:anywhere]">{children}</h3>,
                p: ({ children }) => <p className="mb-2.5 text-gray-700 leading-relaxed text-xs sm:text-sm break-words [overflow-wrap:anywhere]">{children}</p>,
                ul: ({ children }) => <ul className="list-disc pl-4 mb-2.5 space-y-1 text-xs sm:text-sm text-gray-700 break-words [overflow-wrap:anywhere]">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-4 mb-2.5 space-y-1 text-xs sm:text-sm text-gray-700 break-words [overflow-wrap:anywhere]">{children}</ol>,
                li: ({ children }) => <li className="text-gray-700 break-words [overflow-wrap:anywhere]">{children}</li>,
                blockquote: ({ children }) => (
                  <blockquote className="border-l-2 border-indigo-500 pl-3 py-1 my-2 bg-indigo-50/50 text-gray-700 rounded-r text-xs break-words [overflow-wrap:anywhere]">
                    {children}
                  </blockquote>
                ),
                pre: ({ children }) => (
                  <pre className="p-3.5 rounded-xl bg-gray-900 border border-gray-800 overflow-x-auto text-xs font-mono text-gray-100 my-2.5 max-w-full">
                    {children}
                  </pre>
                ),
                code: ({ children, className }: any) => {
                  const isCodeBlock = Boolean(className?.includes('language-')) || (typeof children === 'string' && children.includes('\n'));
                  if (isCodeBlock) {
                    return (
                      <code className="font-mono text-xs text-gray-100 block whitespace-pre">
                        {children}
                      </code>
                    );
                  }
                  return (
                    <code className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-800 font-mono text-xs border border-gray-200 break-words [overflow-wrap:anywhere] max-w-full inline">
                      {children}
                    </code>
                  );
                },
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-0.5 text-indigo-600 hover:text-indigo-700 underline underline-offset-2 transition font-medium break-all"
                  >
                    <span>{children}</span>
                    <ExternalLink className="w-2.5 h-2.5 inline shrink-0 opacity-70" />
                  </a>
                ),
                table: ({ children }) => (
                  <div className="overflow-x-auto max-w-full my-2.5 border border-gray-200 rounded-lg">
                    <table className="w-full text-xs text-left text-gray-800 bg-white">{children}</table>
                  </div>
                ),
                th: ({ children }) => <th className="px-3 py-1.5 bg-gray-50 font-semibold text-gray-900 border-b border-gray-200">{children}</th>,
                td: ({ children }) => <td className="px-3 py-1.5 border-b border-gray-100">{children}</td>,
              }}
            >
              {message.content}
            </ReactMarkdown>

            {/* Clean References List if sources exist and not already in markdown */}
            {!hasMarkdownReferences && message.sources && message.sources.length > 0 && (
              <div className="mt-4 pt-3 border-t border-gray-200/90 text-xs">
                <div className="flex items-center gap-1.5 font-semibold text-gray-900 mb-2">
                  <Link2 className="w-3.5 h-3.5 text-gray-500" />
                  <span>References</span>
                </div>
                <ul className="space-y-1 text-gray-600 pl-1">
                  {message.sources.map((src, idx) => (
                    <li key={idx} className="flex items-baseline gap-2">
                      <span className="text-gray-400 font-mono text-[10px]">[{idx + 1}]</span>
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-600 hover:text-indigo-700 hover:underline truncate max-w-full font-medium"
                      >
                        {src.title || src.url}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
