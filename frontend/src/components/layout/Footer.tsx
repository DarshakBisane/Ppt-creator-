import React from 'react';
import { Sparkles, Terminal, Shield, CheckCircle2 } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-900/40 py-8 text-xs text-slate-500 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 rounded-lg bg-indigo-600/30 flex items-center justify-center text-indigo-400">
              <Sparkles className="w-3.5 h-3.5" />
            </div>
            <p className="text-slate-400">
              PresenAI <span className="text-slate-600">|</span> Production AI Presentation Studio
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 text-slate-400">
            <span className="flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-cyan-400" />
              <span>Zero Client Secret Exposure</span>
            </span>
            <span className="flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-indigo-400" />
              <span>Deterministic Layout Engine</span>
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Phase 2 Verified</span>
            </span>
          </div>

          <p className="text-slate-500 font-mono text-[11px]">
            v0.1.0 • Phase 2 (Studio UI)
          </p>
        </div>
      </div>
    </footer>
  );
};
