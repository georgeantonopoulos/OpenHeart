/**
 * API Client Configuration.
 *
 * Provides authenticated fetch wrapper for backend API calls.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ApiError {
  detail: string;
  status: number;
}

/**
 * Custom error class for API errors.
 */
export class ApiClientError extends Error {
  status: number;
  detail: string;

  constructor(message: string, status: number, detail: string) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Authenticated fetch wrapper.
 *
 * Adds Authorization header and handles common error cases.
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  accessToken?: string
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (accessToken) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = 'An error occurred';
    try {
      const errorData = await response.json();
      detail = errorData.detail || detail;
    } catch {
      // Ignore JSON parse errors
    }

    throw new ApiClientError(
      `API Error: ${response.status}`,
      response.status,
      detail
    );
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

/**
 * Convenience API client with HTTP method helpers.
 */
export const apiClient = {
  async get<T>(endpoint: string, accessToken?: string): Promise<T> {
    return apiFetch<T>(endpoint, {}, accessToken);
  },
  async post<T>(endpoint: string, body?: unknown, accessToken?: string): Promise<T> {
    return apiFetch<T>(endpoint, {
      method: 'POST',
      ...(body ? { body: JSON.stringify(body) } : {}),
    }, accessToken);
  },
  async put<T>(endpoint: string, body?: unknown, accessToken?: string): Promise<T> {
    return apiFetch<T>(endpoint, {
      method: 'PUT',
      ...(body ? { body: JSON.stringify(body) } : {}),
    }, accessToken);
  },
  async delete<T>(endpoint: string, accessToken?: string): Promise<T> {
    return apiFetch<T>(endpoint, { method: 'DELETE' }, accessToken);
  },
};

/**
 * Build query string from params object.
 */
export function buildQueryString(
  params: Record<string, string | number | boolean | undefined | null>
): string {
  const filtered = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);

  return filtered.length > 0 ? `?${filtered.join('&')}` : '';
}
