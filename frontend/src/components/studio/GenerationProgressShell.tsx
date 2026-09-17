import React from 'react';
import { CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { GenerationStageItem } from '@/types';

export const STAGES: GenerationStageItem[] = [
  { id: 'planning_slides', label: 'Planning Presentation', description: 'Extracting key narrative takeaways & structure' },
  { id: 'designing_layouts', label: 'Designing Tokens & Hierarchy', description: 'Extracting design system and slide containers' },
  { id: 'creating_visuals', label: 'Selecting Visual Archetypes', description: 'Synthesizing charts, process trees & milestone rails' },
  { id: 'checking_slides', label: 'Visual QA & Auto-Correction', description: 'Validating boundary constraints and 3-pass repair' },
  { id: 'building_powerpoint', label: 'Rendering Native PowerPoint', description: 'Constructing native OpenXML shapes & text runs' },
  { id: 'finalizing', label: 'Finalizing & Storage', description: 'Validating presentation package & download readiness' },
];

interface GenerationProgressShellProps {
  currentStageId?: string;
  progressPercent?: number;
  message?: string;
  isGenerating?: boolean;
  isCompleted?: boolean;
  isFailed?: boolean;
}

export const GenerationProgressShell: React.FC<GenerationProgressShellProps> = ({
  currentStageId = 'idle',
  progressPercent = 0,
  message = 'Ready to generate presentation',
  isGenerating = false,
  isCompleted = false,
  isFailed = false,
}) => {
  // Find index of current stage
  const currentStageIndex = STAGES.findIndex((s) => s.id === currentStageId);

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-6">
      {/* Header & Progress Bar */}
      <div className="space-y-3 border-b border-slate-800 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">Generation Pipeline</h3>
            <p className="text-xs text-slate-400 mt-0.5">{message}</p>
          </div>
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold">
            {isCompleted ? '100%' : `${progressPercent}%`}
          </span>
        </div>

        {/* Real Progress Bar */}
        <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden relative">
          <div
            className={`h-full transition-all duration-500 rounded-full ${
              isFailed
                ? 'bg-rose-500'
                : isCompleted
                ? 'bg-emerald-500'
                : 'bg-indigo-500 shadow-lg shadow-indigo-500/50'
            }`}
            style={{ width: `${Math.max(0, Math.min(100, isCompleted ? 100 : progressPercent))}%` }}
          />
        </div>
      </div>

      {/* Stage Progression Checklist */}
      <div className="space-y-3">
        {STAGES.map((st, idx) => {
          let status: 'completed' | 'active' | 'pending' | 'failed' = 'pending';

          if (isCompleted) {
            status = 'completed';
          } else if (isFailed && st.id === currentStageId) {
            status = 'failed';
          } else if (currentStageIndex > idx) {
            status = 'completed';
          } else if (currentStageIndex === idx && isGenerating) {
            status = 'active';
          }

          return (
            <div
              key={st.id}
              className={`flex items-center space-x-3.5 p-3 rounded-xl border transition-all ${
                status === 'active'
                  ? 'bg-indigo-950/40 border-indigo-500/40 shadow-sm shadow-indigo-500/10'
                  : status === 'completed'
                  ? 'bg-slate-900/40 border-slate-800/60'
                  : status === 'failed'
                  ? 'bg-rose-950/30 border-rose-800/40'
                  : 'bg-slate-900/20 border-slate-800/30 opacity-60'
              }`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-mono shrink-0 ${
                  status === 'completed'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : status === 'active'
                    ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/40'
                    : status === 'failed'
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                    : 'bg-slate-800 text-slate-500'
                }`}
              >
                {status === 'completed' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : status === 'active' ? (
                  <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
                ) : status === 'failed' ? (
                  <AlertCircle className="w-4 h-4 text-rose-400" />
                ) : (
                  idx + 1
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p
                  className={`text-xs sm:text-sm font-medium truncate ${
                    status === 'active'
                      ? 'text-indigo-200 font-semibold'
                      : status === 'completed'
                      ? 'text-slate-200'
                      : status === 'failed'
                      ? 'text-rose-200'
                      : 'text-slate-400'
                  }`}
                >
                  {st.label}
                </p>
                <p className="text-[11px] text-slate-500 truncate">{st.description}</p>
              </div>

              <div className="flex items-center space-x-1 text-xs shrink-0">
                {status === 'completed' ? (
                  <span className="text-emerald-400 text-xs font-medium">Done</span>
                ) : status === 'active' ? (
                  <span className="text-indigo-400 text-xs font-medium">Processing...</span>
                ) : status === 'failed' ? (
                  <span className="text-rose-400 text-xs font-medium">Error</span>
                ) : (
                  <span className="text-slate-500 text-xs">Waiting</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
