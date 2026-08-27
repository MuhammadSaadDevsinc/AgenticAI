'use client';

import React from 'react';
import { MessageSquare, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import { SlackDeliveryRecord } from '@/types/chat';

interface SlackDeliveryCardProps {
  delivery: SlackDeliveryRecord;
}

export const SlackDeliveryCard: React.FC<SlackDeliveryCardProps> = ({ delivery }) => {
  const isSuccess = delivery.status === 'success';
  const isSimulated = delivery.status === 'simulated';
  const isError = delivery.status === 'error';

  return (
    <div className="flex flex-col p-3 rounded-xl bg-white border border-gray-200 shadow-2xs text-xs mb-3">
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-6 h-6 rounded-md bg-indigo-50 text-indigo-700 font-semibold border border-indigo-100">
            <MessageSquare className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="font-semibold text-gray-900 flex items-center gap-1.5">
              <span>{delivery.recipient}</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-gray-100 text-gray-600 border border-gray-200/60">
                {delivery.channel}
              </span>
            </div>
            <p className="text-[10px] text-gray-400">Direct Slack Delivery</p>
          </div>
        </div>

        <div>
          {isSuccess && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Delivered
            </span>
          )}
          {isSimulated && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
              <Clock className="w-3 h-3 text-amber-600" /> Test Mode
            </span>
          )}
          {isError && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-rose-50 text-rose-700 border border-rose-200">
              <AlertCircle className="w-3 h-3 text-rose-600" /> Notice
            </span>
          )}
        </div>
      </div>

      {/* Message Preview */}
      <div className="p-2.5 rounded-lg bg-gray-50 border border-gray-200/80 font-mono text-[11px] text-gray-700 whitespace-pre-wrap leading-relaxed">
        <p className="line-clamp-4">{delivery.message_preview}</p>
      </div>

      {delivery.error && (
        <div className="mt-1.5 text-[10px] text-rose-600 flex items-center gap-1">
          <AlertCircle className="w-3 h-3 shrink-0" />
          <span>{delivery.error}</span>
        </div>
      )}
    </div>
  );
};
