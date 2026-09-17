import React, { useState, useEffect } from 'react';
import { Sparkles, RotateCcw, Info, Loader2 } from 'lucide-react';
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
  JobStatusResponse,
} from '@/types';
import { createGenerationJob, getJobStatus, getDownloadUrl } from '@/lib/api';

interface StudioPageProps {
  initialMode?: CreationMode;
}

const STORAGE_KEY = 'active_presentation_job_id';

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
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [activeBottomTab, setActiveBottomTab] = useState<'preview' | 'pipeline' | 'diagnostics'>('preview');

  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const pollTimerRef = React.useRef<ReturnType<typeof setInterval> | null>(null);
  const consecutiveErrorsRef = React.useRef<number>(0);

  const isJobActive = jobStatus
    ? !['completed', 'failed'].includes(jobStatus.state)
    : isSubmitting;

  const stopPolling = () => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  };

  // Restore active job from localStorage on initial mount
  useEffect(() => {
    const storedJobId = localStorage.getItem(STORAGE_KEY);
    if (storedJobId) {
      setActiveJobId(storedJobId);
      getJobStatus(storedJobId)
        .then((status) => {
          setJobStatus(status);
          if (status.state === 'completed') {
            setActiveBottomTab('preview');
          } else if (status.state === 'failed') {
            setGenerationError(status.error?.message || 'Previous generation failed.');
            localStorage.removeItem(STORAGE_KEY);
          } else {
            setActiveBottomTab('pipeline');
          }
        })
        .catch(() => {
          localStorage.removeItem(STORAGE_KEY);
          setActiveJobId(null);
        });
    }

    return () => stopPolling();
  }, []);

  // Poll backend status while job is running with bounded retry backoff
  useEffect(() => {
    stopPolling();
    consecutiveErrorsRef.current = 0;

    if (!activeJobId) return;

    const isTerminal = jobStatus?.state === 'completed' || jobStatus?.state === 'failed';
    if (isTerminal) return;

    pollTimerRef.current = setInterval(async () => {
      try {
        const status = await getJobStatus(activeJobId);
        consecutiveErrorsRef.current = 0;
        setJobStatus(status);

        if (status.state === 'completed') {
          stopPolling();
          setActiveBottomTab('preview');
        } else if (status.state === 'failed') {
          stopPolling();
          setGenerationError(status.error?.message || 'Presentation generation failed.');
        }
      } catch (err: any) {
        consecutiveErrorsRef.current += 1;
        // Allow up to 3 consecutive transient polling failures before giving up
        if (consecutiveErrorsRef.current >= 3 || err.status === 404) {
          stopPolling();
          setGenerationError(err.message || 'Lost connection to presentation generation job. Please check status or try again.');
        }
      }
    }, 1000);

    return () => stopPolling();
  }, [activeJobId, jobStatus?.state]);


  const handleModeChange = (mode: CreationMode) => {
    setFormState((prev) => ({ ...prev, mode }));
    setValidationError(null);
    setGenerationError(null);
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
    setGenerationError(null);
    setActiveJobId(null);
    setJobStatus(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  const handleGenerateClick = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setGenerationError(null);

    // 1. Validation check
    if (!formState.topic.trim()) {
      setValidationError('Please enter a presentation topic to proceed.');
      return;
    }

    if (formState.mode === 'reference' && !formState.referenceFile) {
      setValidationError('Please upload a reference PowerPoint (.pptx) file.');
      return;
    }

    // 2. Prevent duplicate submission
    if (isJobActive || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await createGenerationJob(formState);
      setActiveJobId(res.job_id);
      localStorage.setItem(STORAGE_KEY, res.job_id);
      setJobStatus({
        job_id: res.job_id,
        state: 'queued',
        progress: 0,
        stage: 'planning_slides',
        message: 'Job queued...',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        artifact: null,
        error: null,
      });
      setActiveBottomTab('pipeline');
    } catch (err: any) {
      setGenerationError(err.message || 'Failed to submit presentation generation request.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = () => {
    if (!isJobActive && !isSubmitting) {
      const fakeEvent = { preventDefault: () => {} } as React.FormEvent;
      handleGenerateClick(fakeEvent);
    }
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

      {generationError && (
        <ErrorAlert
          title="Generation Error"
          message={generationError}
          actionLabel="Retry Generation"
          onAction={handleRetry}
          onDismiss={() => setGenerationError(null)}
        />
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
                disabled={isJobActive || isSubmitting}
                className={`flex-1 py-3.5 px-6 rounded-xl text-sm font-semibold transition-all shadow-xl flex items-center justify-center space-x-2 ${
                  isJobActive || isSubmitting
                    ? 'bg-indigo-900/50 text-indigo-300 border border-indigo-500/30 cursor-not-allowed opacity-80'
                    : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/25 cursor-pointer'
                }`}
              >
                {isJobActive || isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-indigo-300" />
                    <span>Generating Presentation...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Generate Presentation</span>
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleReset}
                disabled={isJobActive}
                className={`p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 transition-colors ${
                  isJobActive
                    ? 'cursor-not-allowed opacity-50'
                    : 'hover:bg-slate-800 hover:text-white cursor-pointer'
                }`}
                title="Reset Form"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-center space-x-2 text-[11px] text-slate-500">
              <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span>Native PowerPoint (.pptx) output • Deterministic layout</span>
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

        {activeBottomTab === 'preview' && (
          <SlideGalleryShell
            hasResult={jobStatus?.state === 'completed' && !!jobStatus.artifact}
            downloadUrl={jobStatus?.job_id ? getDownloadUrl(jobStatus.job_id) : null}
            filename={jobStatus?.artifact?.filename || 'Presentation.pptx'}
            slideCount={0}
          />
        )}
        {activeBottomTab === 'pipeline' && (
          <GenerationProgressShell
            currentStageId={jobStatus?.stage || 'idle'}
            progressPercent={jobStatus?.progress || 0}
            message={jobStatus?.message || 'Ready to generate presentation'}
            isGenerating={isJobActive}
            isCompleted={jobStatus?.state === 'completed'}
            isFailed={jobStatus?.state === 'failed'}
          />
        )}
        {activeBottomTab === 'diagnostics' && (
          <DiagnosticsInspectorShell hasDiagnostics={jobStatus?.state === 'completed'} />
        )}
      </div>
    </div>
  );
};

