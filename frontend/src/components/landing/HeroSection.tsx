import React from 'react';
import { Sparkles, FileUp, ArrowRight, Layers, ShieldCheck, Box, RefreshCw } from 'lucide-react';
import { CreationMode } from '@/types';

interface HeroSectionProps {
  onStartCreation: (mode: CreationMode) => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onStartCreation }) => {
  return (
    <section className="relative pt-12 pb-16 lg:pt-20 lg:pb-24 overflow-hidden text-center">
      {/* Subtle Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-indigo-500/15 via-violet-500/10 to-cyan-500/10 blur-[120px] rounded-full pointer-events-none -z-10" />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        {/* Release Tag */}
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold tracking-wide uppercase shadow-sm">
          <Sparkles className="w-3.5 h-3.5 animate-pulse" />
          <span>Next-Generation PowerPoint Engine</span>
        </div>

        {/* Main Headline */}
        <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-[1.15]">
          Create better presentations <br className="hidden sm:inline" />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-violet-400 to-cyan-400">
            with genuine visual intelligence.
          </span>
        </h1>

        {/* Supporting Message */}
        <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
          Generate high-fidelity, completely editable PowerPoint decks from a topic or transfer the design language of your existing reference presentation.
        </p>

        {/* Dual CTAs */}
        <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={() => onStartCreation('topic')}
            className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all shadow-xl shadow-indigo-600/25 flex items-center justify-center space-x-2.5 group cursor-pointer"
          >
            <Sparkles className="w-4 h-4 text-indigo-200 group-hover:scale-110 transition-transform" />
            <span>Create from Topic</span>
            <ArrowRight className="w-4 h-4 text-indigo-300 group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            onClick={() => onStartCreation('reference')}
            className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-200 hover:text-white border border-slate-700/80 text-sm font-semibold transition-all flex items-center justify-center space-x-2.5 group cursor-pointer"
          >
            <FileUp className="w-4 h-4 text-slate-400 group-hover:text-indigo-400 group-hover:-translate-y-0.5 transition-all" />
            <span>Use Reference PPT</span>
          </button>
        </div>

        {/* Feature Badges */}
        <div className="pt-8 flex flex-wrap items-center justify-center gap-3 sm:gap-6 text-xs text-slate-400 font-medium">
          <span className="flex items-center gap-1.5 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800/80">
            <Box className="w-3.5 h-3.5 text-indigo-400" />
            Native Editable Objects
          </span>
          <span className="flex items-center gap-1.5 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800/80">
            <Layers className="w-3.5 h-3.5 text-violet-400" />
            Semantic Visual Layouts
          </span>
          <span className="flex items-center gap-1.5 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800/80">
            <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
            Adaptive Design Transfer
          </span>
          <span className="flex items-center gap-1.5 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800/80">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Automated Visual QA
          </span>
        </div>
      </div>
    </section>
  );
};
