import React from 'react';
import { Presentation, Download, Eye } from 'lucide-react';
import { EmptyState } from '@/components/common/EmptyState';

interface SlideGalleryShellProps {
  hasResult?: boolean;
}

export const SlideGalleryShell: React.FC<SlideGalleryShellProps> = ({ hasResult = false }) => {
  if (!hasResult) {
    return (
      <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-2.5">
            <Presentation className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-semibold text-white">Presentation Preview Stage</h3>
          </div>
          <button
            disabled
            className="flex items-center space-x-2 px-3.5 py-1.5 rounded-xl bg-slate-800 text-slate-500 text-xs font-semibold cursor-not-allowed opacity-60 border border-slate-700/50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download .PPTX</span>
          </button>
        </div>

        <EmptyState
          icon={Presentation}
          title="No Presentation Generated Yet"
          description="Fill out the topic and presentation settings in the workspace above to prepare your presentation."
        />
      </div>
    );
  }

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-2.5">
          <Presentation className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-semibold text-white">Generated Slides Preview</h3>
        </div>
        <button
          disabled
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 opacity-50 cursor-not-allowed"
        >
          <Download className="w-4 h-4" />
          <span>Download .PPTX</span>
        </button>
      </div>

      {/* Slide Preview Stage Shell */}
      <div className="aspect-[16/9] w-full rounded-2xl bg-slate-900 border border-slate-800 flex flex-col items-center justify-center p-8 text-center relative overflow-hidden">
        <div className="p-4 rounded-2xl bg-indigo-500/10 text-indigo-400 mb-3 border border-indigo-500/20">
          <Eye className="w-8 h-8" />
        </div>
        <h4 className="text-base font-semibold text-white">Interactive 16:9 Canvas Stage</h4>
        <p className="text-xs text-slate-400 max-w-md mt-1">
          High-resolution vector slide preview rendered by backend layout engine.
        </p>
      </div>
    </div>
  );
};
