import React from 'react';
import { Sparkles, FileUp } from 'lucide-react';
import { CreationMode } from '@/types';

interface ModeSelectorProps {
  mode: CreationMode;
  onChange: (mode: CreationMode) => void;
}

export const ModeSelector: React.FC<ModeSelectorProps> = ({ mode, onChange }) => {
  return (
    <div className="flex p-1 bg-slate-900/90 rounded-2xl border border-slate-800 max-w-md mx-auto sm:mx-0 shadow-inner">
      <button
        type="button"
        onClick={() => onChange('topic')}
        className={`flex-1 flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer select-none ${
          mode === 'topic'
            ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
            : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
        }`}
      >
        <Sparkles className="w-4 h-4" />
        <span>Create from Topic</span>
      </button>

      <button
        type="button"
        onClick={() => onChange('reference')}
        className={`flex-1 flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer select-none ${
          mode === 'reference'
            ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
            : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
        }`}
      >
        <FileUp className="w-4 h-4" />
        <span>From Reference PPT</span>
      </button>
    </div>
  );
};
