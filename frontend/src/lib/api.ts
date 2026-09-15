/**
 * Reusable HTTP API Client.
 */

import { ApiErrorResponse, HealthResponse, PresentationFormState } from '@/types';

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
 * Base HTTP request wrapper with structured error handling.
 */
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
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
    const message = err instanceof Error ? err.message : 'Network error occurred';
    throw new ApiClientError(message, 0, 'NETWORK_ERROR');
  }
}

/**
 * API Client functions.
 */
export const api = {
  /**
   * Health check endpoint.
   */
  async getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/health');
  },

  /**
   * Presentation generation boundary.
   * Note: The generation backend will be integrated in Phase 4/10.
   */
  async createGenerationJob(_data: PresentationFormState): Promise<{ jobId: string }> {
    throw new ApiClientError(
      'The presentation generation backend pipeline will be connected in future phases. No fake generation was executed.',
      501,
      'NOT_IMPLEMENTED'
    );
  },
};
