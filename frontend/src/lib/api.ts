/**
 * Reusable HTTP API Client.
 */

import {
  ApiErrorResponse,
  GenerationJobResponse,
  HealthResponse,
  JobStatusResponse,
  PresentationFormState,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export class ApiClientError extends Error {
  public code: string;
  public status: number;
  public requestId?: string;
  public details?: Array<Record<string, unknown>>;

  constructor(
    message: string,
    status: number,
    code: string = 'UNKNOWN_ERROR',
    requestId?: string,
    details?: Array<Record<string, unknown>>
  ) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = code;
    this.requestId = requestId;
    this.details = details;
  }
}

/**
 * Base HTTP request wrapper with structured error handling and finite timeout.
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs: number = 30000
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: options.signal || controller.signal,
    });

    const requestId = response.headers.get('X-Request-ID') || undefined;

    if (!response.ok) {
      let errorData: ApiErrorResponse | null = null;
      try {
        errorData = await response.json();
      } catch {
        // Response was not JSON
      }

      const code = errorData?.error?.code || `HTTP_${response.status}`;
      const message = errorData?.error?.message || `Request failed with status ${response.status}`;
      const reqId = errorData?.error?.request_id || requestId;
      const details = errorData?.error?.details;

      throw new ApiClientError(message, response.status, code, reqId, details);
    }

    // Return JSON if present
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return (await response.json()) as T;
    }

    return {} as T;
  } catch (err) {
    if (err instanceof ApiClientError) {
      throw err;
    }
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiClientError('Request timed out. Please check your connection and try again.', 408, 'REQUEST_TIMEOUT');
    }
    const message = err instanceof Error ? err.message : 'Network error occurred';
    throw new ApiClientError(message, 0, 'NETWORK_ERROR');
  } finally {
    clearTimeout(timeoutId);
  }
}


/**
 * API Client functions.
 */
export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

export async function createGenerationJob(data: PresentationFormState): Promise<GenerationJobResponse> {
  const slideCountNum = data.slideCount === 'auto' ? 8 : parseInt(data.slideCount, 10) || 8;

  if (data.mode === 'reference' && data.referenceFile) {
    const formData = new FormData();
    formData.append('mode', 'reference');
    formData.append('topic', data.topic);
    formData.append('audience', data.audience);
    formData.append('purpose', data.purpose);
    formData.append('slide_count', String(slideCountNum));
    formData.append('style', data.style);
    formData.append('reference_file', data.referenceFile);

    return request<GenerationJobResponse>('/api/generate', {
      method: 'POST',
      body: formData,
    });
  }

  return request<GenerationJobResponse>('/api/generate', {
    method: 'POST',
    body: JSON.stringify({
      mode: data.mode,
      topic: data.topic,
      audience: data.audience,
      purpose: data.purpose,
      slide_count: slideCountNum,
      style: data.style,
    }),
  });
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  return request<JobStatusResponse>(`/api/jobs/${jobId}`);
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE_URL}/api/download/${jobId}`;
}

export const api = {
  getHealth,
  createGenerationJob,
  getJobStatus,
  getDownloadUrl,
};


