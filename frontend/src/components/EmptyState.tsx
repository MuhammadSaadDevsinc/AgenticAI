'use client';

import React from 'react';
import { Search } from 'lucide-react';

export const EmptyState: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center max-w-2xl mx-auto py-16 px-4 text-center">
      {/* Icon Badge */}
      <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gray-900 text-white mb-4 shadow-sm">
        <Search className="w-6 h-6" />
      </div>

      <h2 className="text-xl sm:text-2xl font-bold text-gray-900 tracking-tight mb-2">
        Autonomous Research Assistant
      </h2>
      <p className="text-xs sm:text-sm text-gray-500 max-w-md mb-8 leading-relaxed">
        Ask any inquiry. The assistant analyzes your prompt, retrieves web data if needed, and synthesizes accurate responses.
      </p>
    </div>
  );
};
