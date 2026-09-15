import React, { useState } from 'react';
import { Sparkles, RotateCcw, Info, CheckCircle2 } from 'lucide-react';
import { ModeSelector } from '@/components/studio/ModeSelector';
import { TopicForm } from '@/components/studio/TopicForm';
import { ReferenceUploader } from '@/components/studio/ReferenceUploader';
import { PresentationSettings } from '@/components/studio/PresentationSettings';
import { GenerationProgressShell } from '@/components/studio/GenerationProgressShell';
import { SlideGalleryShell } from '@/components/studio/SlideGalleryShell';
import { DiagnosticsInspectorShell } from '@/components/studio/DiagnosticsInspectorShell';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import {
  AudienceOption,
  CreationMode,
  PresentationFormState,
  PurposeOption,
  SlideCountOption,
  StyleOption,
} from '@/types';

interface StudioPageProps {
  initialMode?: CreationMode;
}

export const StudioPage: React.FC<StudioPageProps> = ({ initialMode = 'topic' }) => {
  const [formState, setFormState] = useState<PresentationFormState>({
    mode: initialMode,
    topic: '',
    referenceFile: null,
    referenceFileName: null,
    referenceFileSize: null,
    audience: 'general',
    purpose: 'business',
    slideCount: 'auto',
    style: 'professional',
  });

  const [validationError, setValidationError] = useState<string | null>(null);
  const [generationNotice, setGenerationNotice] = useState<string | null>(null);
  const [activeBottomTab, setActiveBottomTab] = useState<'preview' | 'pipeline' | 'diagnostics'>('preview');

  const handleModeChange = (mode: CreationMode) => {
    setFormState((prev) => ({ ...prev, mode }));
    setValidationError(null);
    setGenerationNotice(null);
  };

  const handleTopicChange = (topic: string) => {
    setFormState((prev) => ({ ...prev, topic }));
    if (validationError) setValidationError(null);
  };

  const handleFileSelect = (file: File | null) => {
    setFormState((prev) => ({
      ...prev,
      referenceFile: file,
      referenceFileName: file ? file.name : null,
      referenceFileSize: file ? file.size : null,
    }));
    if (validationError) setValidationError(null);
  };

  const handleReset = () => {
    setFormState({
      mode: 'topic',
      topic: '',
      referenceFile: null,
      referenceFileName: null,
      referenceFileSize: null,
      audience: 'general',
      purpose: 'business',
      slideCount: 'auto',
      style: 'professional',
    });
    setValidationError(null);
    setGenerationNotice(null);
  };

  const handleGenerateClick = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setGenerationNotice(null);

    // 1. Validation check
    if (!formState.topic.trim()) {
      setValidationError('Please enter a presentation topic to proceed.');
      return;
    }

    if (formState.mode === 'reference' && !formState.referenceFile) {
      setValidationError('Please upload a reference PowerPoint (.pptx) file.');
      return;
    }

    // 2. Verified form state notification (no fake completion)
    setGenerationNotice(
      `Form inputs validated successfully for ${
        formState.mode === 'topic' ? 'Topic Creation' : 'Reference Style Transfer'
      }. The AI Orchestrator and Deterministic PPTX rendering backend will be wired in subsequent phases.`
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Studio Header & Mode Segment */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Presentation Studio
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Configure your topic, visual archetype intent, and design parameters.
          </p>
        </div>

        <ModeSelector mode={formState.mode} onChange={handleModeChange} />
      </div>

      {/* Error & Validation Banner */}
      {validationError && (
        <ErrorAlert
          title="Incomplete Configuration"
          message={validationError}
          onDismiss={() => setValidationError(null)}
        />
      )}

      {/* Pipeline Status Notice */}
      {generationNotice && (
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 flex items-start space-x-3 text-sm animate-in fade-in duration-200">
          <CheckCircle2 className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h5 className="font-semibold text-indigo-200">Inputs Validated</h5>
            <p className="text-xs sm:text-sm text-indigo-300/90 mt-0.5 leading-relaxed">
              {generationNotice}
            </p>
          </div>
        </div>
      )}

      {/* Main Two-Column Workspace */}
      <form onSubmit={handleGenerateClick} className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Topic or Reference Uploader (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl">
            {formState.mode === 'topic' ? (
              <TopicForm
                topic={formState.topic}
                onChange={handleTopicChange}
                error={validationError && !formState.topic ? validationError : null}
              />
            ) : (
              <ReferenceUploader
                file={formState.referenceFile}
                onFileSelect={handleFileSelect}
                topic={formState.topic}
                onTopicChange={handleTopicChange}
                fileError={
                  validationError && formState.mode === 'reference' && !formState.referenceFile
                    ? 'Reference .pptx is required in Reference Mode'
                    : null
                }
                topicError={validationError && !formState.topic ? validationError : null}
              />
            )}
          </div>
        </div>

        {/* Right Column: Settings & Action Bar (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="glass-panel rounded-2xl p-6 sm:p-8 shadow-xl space-y-6">
            <PresentationSettings
              audience={formState.audience}
              onAudienceChange={(audience: AudienceOption) =>
                setFormState((p) => ({ ...p, audience }))
              }
              purpose={formState.purpose}
              onPurposeChange={(purpose: PurposeOption) =>
                setFormState((p) => ({ ...p, purpose }))
              }
              slideCount={formState.slideCount}
              onSlideCountChange={(slideCount: SlideCountOption) =>
                setFormState((p) => ({ ...p, slideCount }))
              }
              style={formState.style}
              onStyleChange={(style: StyleOption) => setFormState((p) => ({ ...p, style }))}
            />

            {/* Action Bar */}
            <div className="pt-4 border-t border-slate-800/80 flex items-center gap-3">
              <button
                type="submit"
                className="flex-1 py-3.5 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all shadow-xl shadow-indigo-600/25 flex items-center justify-center space-x-2 cursor-pointer"
              >
                <Sparkles className="w-4 h-4" />
                <span>Generate Presentation</span>
              </button>

              <button
                type="button"
                onClick={handleReset}
                className="p-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
                title="Reset Form"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-center space-x-2 text-[11px] text-slate-500">
              <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span>Native PowerPoint (.pptx) output • No token limits</span>
            </div>
          </div>
        </div>
      </form>

      {/* Lower Shell Section: Preview Stage, Pipeline, and Diagnostics */}
      <div className="pt-6 space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
          <button
            onClick={() => setActiveBottomTab('preview')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeBottomTab === 'preview'
                ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Preview Canvas Stage
          </button>
          <button
            onClick={() => setActiveBottomTab('pipeline')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeBottomTab === 'pipeline'
                ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Generation Pipeline
          </button>
          <button
            onClick={() => setActiveBottomTab('diagnostics')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeBottomTab === 'diagnostics'
                ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Visual QA Inspector
          </button>
        </div>

        {activeBottomTab === 'preview' && <SlideGalleryShell hasResult={false} />}
        {activeBottomTab === 'pipeline' && <GenerationProgressShell />}
        {activeBottomTab === 'diagnostics' && <DiagnosticsInspectorShell hasDiagnostics={false} />}
      </div>
    </div>
  );
};
