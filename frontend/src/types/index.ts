/**
 * Global frontend types and API contracts.
 */

export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
  version: string;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  request_id?: string;
  details?: Array<Record<string, unknown>>;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

// ----------------------------------------------------------------------
// Creation Modes & Settings
// ----------------------------------------------------------------------

export type CreationMode = 'topic' | 'reference';

export type AudienceOption =
  | 'general'
  | 'executives'
  | 'developers'
  | 'students'
  | 'investors'
  | 'sales_clients';

export type PurposeOption =
  | 'business'
  | 'pitch'
  | 'academic'
  | 'technical'
  | 'training'
  | 'case_study';

export type SlideCountOption = 'auto' | '5' | '8' | '10' | '12' | '15' | '20';

export type StyleOption =
  | 'professional'
  | 'minimal'
  | 'modern_dark'
  | 'corporate'
  | 'creative';

export interface PresentationFormState {
  mode: CreationMode;
  topic: string;
  referenceFile: File | null;
  referenceFileName: string | null;
  referenceFileSize: number | null;
  audience: AudienceOption;
  purpose: PurposeOption;
  slideCount: SlideCountOption;
  style: StyleOption;
}

// ----------------------------------------------------------------------
// Generation Pipeline Stages & Diagnostics (Future Shells)
// ----------------------------------------------------------------------

export type GenerationStageId =
  | 'understanding_topic'
  | 'planning_slides'
  | 'designing_layouts'
  | 'creating_visuals'
  | 'building_powerpoint'
  | 'checking_slides'
  | 'fixing_layout'
  | 'finalizing';

export interface GenerationStageItem {
  id: GenerationStageId;
  label: string;
  description: string;
}

export type GenerationStatus =
  | 'idle'
  | 'validating'
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed';

export interface SlidePreviewItem {
  index: number;
  title: string;
  archetype: string;
  elementsCount: number;
}

export interface DiagnosticsSummary {
  boundsCheck: 'pass' | 'fail' | 'pending';
  overflowCheck: 'pass' | 'fail' | 'pending';
  spacingConsistency: 'pass' | 'fail' | 'pending';
  collisionCheck: 'pass' | 'fail' | 'pending';
  correctionsCount: number;
}

export type Theme = 'dark' | 'light';
export type ActiveTab = 'landing' | 'studio';

// ----------------------------------------------------------------------
// Phase 10 API Contracts
// ----------------------------------------------------------------------

export interface ArtifactInfo {
  filename: string;
  download_url: string;
  size_bytes: number;
  slide_count: number;
}

export interface JobErrorResponse {
  code: string;
  message: string;
  retryable: boolean;
}

export interface JobStatusResponse {
  job_id: string;
  state: string;
  progress: number;
  stage: string;
  message: string;
  created_at: string;
  updated_at: string;
  artifact: ArtifactInfo | null;
  error: JobErrorResponse | null;
}

export interface GenerationJobResponse {
  job_id: string;
  state: string;
  status_url: string;
}

