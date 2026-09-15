import React from 'react';
import { GenerationStageItem } from '@/types';
import { Clock, Info } from 'lucide-react';

export const STAGES: GenerationStageItem[] = [
  { id: 'understanding_topic', label: 'Understanding Topic', description: 'Extracting key narrative takeaways & structure' },
  { id: 'planning_slides', label: 'Planning Slides', description: 'Designing slide progression & information density' },
  { id: 'designing_layouts', label: 'Designing Layouts', description: 'Selecting semantic visual archetypes & containers' },
  { id: 'creating_visuals', label: 'Creating Visuals', description: 'Synthesizing charts, process trees & milestone rails' },
  { id: 'building_powerpoint', label: 'Building PowerPoint', description: 'Constructing native OpenXML shapes & text runs' },
  { id: 'checking_slides', label: 'Checking Slides', description: 'Running Pillow font metrics & collision detection' },
  { id: 'fixing_layout', label: 'Fixing Layout', description: '3-pass automatic overflow & density correction' },
  { id: 'finalizing', label: 'Finalizing', description: 'Validating presentation package & preview assets' },
];

interface GenerationProgressShellProps {
  currentStageId?: string;
  isGenerating?: boolean;
}

export const GenerationProgressShell: React.FC<GenerationProgressShellProps> = () => {
  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-semibold text-white">Generation Pipeline Stages</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time deterministic progress stages (Active in Phase 4/10)
          </p>
        </div>
        <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
          8 Stages
        </span>
      </div>

      <div className="space-y-3">
        {STAGES.map((st, idx) => (
          <div
            key={st.id}
            className="flex items-center space-x-3.5 p-3 rounded-xl bg-slate-900/40 border border-slate-800/60"
          >
            <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 shrink-0 text-xs font-mono">
              {idx + 1}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs sm:text-sm font-medium text-slate-300 truncate">{st.label}</p>
              <p className="text-[11px] text-slate-500 truncate">{st.description}</p>
            </div>
            <div className="flex items-center space-x-1 text-xs text-slate-500 shrink-0">
              <Clock className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Ready</span>
            </div>
          </div>
        ))}
      </div>

      {/* Backend Integration Info Callout */}
      <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-start space-x-3 text-xs text-indigo-300">
        <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <h5 className="font-semibold text-indigo-200">Phase 2 Architecture Guarantee</h5>
          <p className="mt-0.5 leading-relaxed text-indigo-300/80">
            This stage tracker will be wired to backend SSE/polling events in Phase 10. Per project quality rules, no fake animated progress or mock generation is executed in Phase 2.
          </p>
        </div>
      </div>
    </div>
  );
};
