import React from 'react';
import { Presentation, Download, CheckCircle2, FileText, Layers } from 'lucide-react';
import { EmptyState } from '@/components/common/EmptyState';

interface SlideGalleryShellProps {
  hasResult?: boolean;
  downloadUrl?: string | null;
  filename?: string | null;
  slideCount?: number;
  onDownload?: () => void;
}

export const SlideGalleryShell: React.FC<SlideGalleryShellProps> = ({
  hasResult = false,
  downloadUrl = null,
  filename = 'Presentation.pptx',
  slideCount = 0,
  onDownload,
}) => {
  if (!hasResult || !downloadUrl) {
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
          description="Enter a topic in the workspace above and click 'Generate Presentation' to run the pipeline."
        />
      </div>
    );
  }

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-2.5">
          <Presentation className="w-5 h-5 text-indigo-400" />
          <div>
            <h3 className="text-base font-semibold text-white">Generated Presentation</h3>
            <p className="text-xs text-slate-400">{filename}</p>
          </div>
        </div>
        <a
          href={downloadUrl}
          download={filename || 'Presentation.pptx'}
          onClick={onDownload}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 transition-all cursor-pointer"
        >
          <Download className="w-4 h-4" />
          <span>Download .PPTX</span>
        </a>
      </div>

      {/* Slide Completion Showcase */}
      <div className="aspect-[16/9] w-full rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col items-center justify-center p-8 text-center relative overflow-hidden space-y-4">
        <div className="p-4 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-10 h-10" />
        </div>
        <div className="space-y-1">
          <h4 className="text-lg font-bold text-white">PowerPoint Presentation Ready</h4>
          <p className="text-xs text-slate-400 max-w-md">
            Rendered with editable native PowerPoint shapes, typography hierarchies, tables, and charts.
          </p>
        </div>

        <div className="flex items-center space-x-4 pt-2">
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/50 text-xs text-slate-300">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>{slideCount > 0 ? `${slideCount} Slides` : 'Complete Deck'}</span>
          </div>
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/50 text-xs text-slate-300">
            <FileText className="w-3.5 h-3.5 text-emerald-400" />
            <span>100% Native OpenXML</span>
          </div>
        </div>

        <div className="pt-2">
          <a
            href={downloadUrl}
            download={filename || 'Presentation.pptx'}
            onClick={onDownload}
            className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-xl shadow-indigo-600/30 transition-all cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Download {filename}</span>
          </a>
        </div>
      </div>
    </div>
  );
};
