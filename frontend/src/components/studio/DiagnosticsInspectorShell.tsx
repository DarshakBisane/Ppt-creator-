import React from 'react';
import { ShieldCheck, CheckCircle2 } from 'lucide-react';
import { EmptyState } from '@/components/common/EmptyState';

interface DiagnosticsInspectorShellProps {
  hasDiagnostics?: boolean;
}

export const DiagnosticsInspectorShell: React.FC<DiagnosticsInspectorShellProps> = ({
  hasDiagnostics = false,
}) => {
  if (!hasDiagnostics) {
    return (
      <div className="glass-panel rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h4 className="text-sm font-semibold text-white">Visual QA & Diagnostics</h4>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-800 text-slate-400">
            Phase 9 Ready
          </span>
        </div>

        <EmptyState
          icon={ShieldCheck}
          title="No QA Diagnostics Available"
          description="Slide bounding box containment, text overflow, and collision checks will run during generation."
        />
      </div>
    );
  }

  const checks = [
    { label: 'Slide Boundary Containment', status: 'pass', desc: 'All shapes within 1920x1080 bounds' },
    { label: 'Typography Overflow Check', status: 'pass', desc: 'Font metric fitting within containers' },
    { label: 'Spacing & Gap Consistency', status: 'pass', desc: 'Equal row padding & column margins' },
    { label: 'Object Collision Matrix', status: 'pass', desc: 'Zero forbidden AABB intersections' },
  ];

  return (
    <div className="glass-panel rounded-2xl p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <h4 className="text-sm font-semibold text-white">Visual QA Diagnostics</h4>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          All Checks Passed
        </span>
      </div>

      <div className="space-y-2.5">
        {checks.map((c, i) => (
          <div
            key={i}
            className="flex items-start justify-between p-2.5 rounded-xl bg-slate-900/50 border border-slate-800 text-xs"
          >
            <div>
              <p className="font-medium text-slate-200">{c.label}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">{c.desc}</p>
            </div>
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          </div>
        ))}
      </div>
    </div>
  );
};
