import React, { useRef, useState } from 'react';
import { UploadCloud, FileText, Trash2, AlertCircle, Info } from 'lucide-react';

interface ReferenceUploaderProps {
  file: File | null;
  onFileSelect: (file: File | null) => void;
  topic: string;
  onTopicChange: (topic: string) => void;
  fileError?: string | null;
  topicError?: string | null;
}

const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB

export const ReferenceUploader: React.FC<ReferenceUploaderProps> = ({
  file,
  onFileSelect,
  topic,
  onTopicChange,
  fileError,
  topicError,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const validateAndSetFile = (selectedFile: File) => {
    setValidationError(null);

    // Validate extension
    const isPptx =
      selectedFile.name.toLowerCase().endsWith('.pptx') ||
      selectedFile.type ===
        'application/vnd.openxmlformats-officedocument.presentationml.presentation';

    if (!isPptx) {
      setValidationError('Only PowerPoint .pptx files are supported.');
      return;
    }

    // Validate file size (25 MB max)
    if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
      setValidationError('File size exceeds the 25 MB limit.');
      return;
    }

    onFileSelect(selectedFile);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const activeError = fileError || validationError;

  return (
    <div className="space-y-6">
      {/* PPTX File Upload Zone */}
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-slate-200">
          Upload Reference PowerPoint (.pptx) <span className="text-rose-400">*</span>
        </label>

        {!file ? (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 sm:p-10 text-center transition-all cursor-pointer ${
              isDragging
                ? 'border-indigo-500 bg-indigo-500/10'
                : activeError
                ? 'border-rose-500/80 bg-rose-500/5'
                : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 hover:bg-slate-900/70'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pptx,application/vnd.openxmlformats-officedocument.presentationml.presentation"
              onChange={handleFileInputChange}
              className="hidden"
            />
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto mb-3">
              <UploadCloud className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-white">
              Drag & drop your reference presentation here
            </h4>
            <p className="text-xs text-slate-400 mt-1.5">
              or <span className="text-indigo-400 font-medium underline">browse files</span> from your computer
            </p>
            <p className="text-[11px] text-slate-500 mt-3 font-mono">
              Accepts .pptx only • Max file size: 25 MB
            </p>
          </div>
        ) : (
          <div className="rounded-2xl bg-slate-900/90 border border-slate-800 p-4 flex items-center justify-between gap-4">
            <div className="flex items-center space-x-3 overflow-hidden">
              <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shrink-0">
                <FileText className="w-6 h-6" />
              </div>
              <div className="overflow-hidden">
                <p className="text-sm font-medium text-white truncate">{file.name}</p>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  {formatFileSize(file.size)} • Ready for design extraction
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onFileSelect(null)}
              className="p-2.5 rounded-xl bg-slate-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 transition-colors shrink-0 cursor-pointer"
              title="Remove reference file"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}

        {activeError && (
          <div className="flex items-center space-x-1.5 text-xs text-rose-400 font-medium pt-1">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>{activeError}</span>
          </div>
        )}
      </div>

      {/* New Topic Input for Reference Mode */}
      <div className="space-y-2">
        <label htmlFor="ref-topic-input" className="block text-sm font-semibold text-slate-200">
          New Presentation Topic <span className="text-rose-400">*</span>
        </label>
        <textarea
          id="ref-topic-input"
          value={topic}
          onChange={(e) => onTopicChange(e.target.value)}
          placeholder="What should the new presentation be about? (e.g. 'Next-Generation Renewable Energy Grid Integration')"
          rows={3}
          className={`w-full rounded-2xl bg-slate-900/90 border px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all resize-y ${
            topicError ? 'border-rose-500/80 ring-1 ring-rose-500/50' : 'border-slate-800 hover:border-slate-700'
          }`}
        />
        {topicError && (
          <p className="text-xs text-rose-400 font-medium">{topicError}</p>
        )}

        {/* Adaptive Style Transfer Explanatory Notice */}
        <div className="p-3.5 rounded-xl bg-indigo-500/5 border border-indigo-500/15 flex items-start space-x-2.5 text-xs text-indigo-300/90">
          <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="font-semibold text-indigo-200">Adaptive Design Transfer:</strong> Your reference presentation influences color hierarchy, typography, and card styling. Its original content will not be reused.
          </p>
        </div>
      </div>
    </div>
  );
};
