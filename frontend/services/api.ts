import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig } from "axios";
import type { ApiError } from "@/types";

// =============================================================================
// API Client Configuration
// =============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_TIMEOUT = Number(process.env.NEXT_PUBLIC_API_TIMEOUT ?? 30_000);

// ---------------------------------------------------------------------------
// Token store — holds the access token in memory (never localStorage)
// This is set by AuthProvider after login/register/refresh.
// ---------------------------------------------------------------------------

let _accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  _accessToken = token;
}

export function getAccessToken(): string | null {
  return _accessToken;
}

// ---------------------------------------------------------------------------
// Interceptor-based token refresh
// ---------------------------------------------------------------------------

let _isRefreshing = false;
let _pendingRequests: Array<{
  resolve: (token: string | null) => void;
  reject: (err: unknown) => void;
}> = [];

// ---------------------------------------------------------------------------
// ApiClient class
// ---------------------------------------------------------------------------

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      withCredentials: true, // send httpOnly refresh cookie on all requests
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // --- Request interceptor: attach Bearer token ---
    this.client.interceptors.request.use(
      (config) => {
        if (_accessToken && config.headers) {
          config.headers.Authorization = `Bearer ${_accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // --- Response interceptor: error handling + auto-refresh on 401 ---
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiError>) => {
        const originalRequest = error.config as AxiosRequestConfig & {
          _retry?: boolean;
        };

        // If 401, has a token, and hasn't been retried yet — try refresh
        if (
          error.response?.status === 401 &&
          _accessToken &&
          !originalRequest._retry &&
          !originalRequest.url?.includes("/auth/refresh") &&
          !originalRequest.url?.includes("/auth/login") &&
          !originalRequest.url?.includes("/auth/register")
        ) {
          if (_isRefreshing) {
            // Queue this request until the refresh completes
            return new Promise((resolve, reject) => {
              _pendingRequests.push({ resolve, reject });
            }).then((token) => {
              if (originalRequest.headers) {
                (originalRequest.headers as Record<string, string>)[
                  "Authorization"
                ] = `Bearer ${token}`;
              }
              return this.client(originalRequest);
            });
          }

          originalRequest._retry = true;
          _isRefreshing = true;

          try {
            const response = await axios.post(
              `${API_BASE_URL}/auth/refresh`,
              null,
              { withCredentials: true }
            );
            const newToken: string = response.data.access_token;
            _accessToken = newToken;

            // Process queued requests
            _pendingRequests.forEach((p) => p.resolve(newToken));
            _pendingRequests = [];

            // Retry the original request
            if (originalRequest.headers) {
              (originalRequest.headers as Record<string, string>)[
                "Authorization"
              ] = `Bearer ${newToken}`;
            }
            return this.client(originalRequest);
          } catch (refreshError) {
            _pendingRequests.forEach((p) => p.reject(refreshError));
            _pendingRequests = [];
            _accessToken = null;
            // Dispatch a custom event so AuthProvider can react
            if (typeof window !== "undefined") {
              window.dispatchEvent(new CustomEvent("auth:expired"));
            }
            return Promise.reject(
              formatError(error)
            );
          } finally {
            _isRefreshing = false;
          }
        }

        return Promise.reject(formatError(error));
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async patch<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  async uploadFile<T>(
    url: string,
    formData: FormData,
    onProgress?: (progress: number) => void
  ): Promise<T> {
    const response = await this.client.post<T>(url, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percent);
        }
      },
    });
    return response.data;
  }

  get baseURL(): string {
    return API_BASE_URL;
  }

  /**
   * Direct access to the underlying axios instance (for special cases).
   */
  get instance(): AxiosInstance {
    return this.client;
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatError(error: AxiosError<ApiError>): ApiError {
  if (error.response) {
    return {
      detail:
        (error.response.data as { detail?: string })?.detail ??
        "An unexpected error occurred",
      status_code: error.response.status,
    };
  }

  if (error.request) {
    return {
      detail: "Unable to connect to the server. Please check your connection.",
      status_code: 0,
    };
  }

  return {
    detail: error.message,
    status_code: 0,
  };
}

export const apiClient = new ApiClient();
export default apiClient;
