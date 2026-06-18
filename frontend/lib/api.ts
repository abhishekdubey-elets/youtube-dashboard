import axios, { AxiosError, type AxiosInstance } from 'axios';
import type {
  AuthResponse,
  ExportConfig,
  ExportRecord,
  ExportResult,
  PaginatedExports,
  PaginatedVideos,
  ProcessPlaylistResult,
  Stats,
  Summary,
  Transcript,
  ValidateResult,
  Video,
  VideoQueryParams,
} from './types';

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const TOKEN_KEY = 'elets_yt_token';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(TOKEN_KEY);
}

export const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      clearToken();
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export function apiErrorMessage(error: unknown, fallback = 'Something went wrong'): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { detail?: unknown; message?: unknown } | undefined;
    const detail = data?.detail ?? data?.message;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length && typeof detail[0] === 'object') {
      const first = detail[0] as { msg?: string };
      if (first.msg) return first.msg;
    }
    if (error.message) return error.message;
  }
  if (error instanceof Error) return error.message;
  return fallback;
}

// ---- Auth ----
export async function login(email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/login', { email, password });
  return data;
}

// ---- Videos ----
export async function processVideo(url: string): Promise<Video> {
  const { data } = await api.post<Video>('/videos/process-video', { url });
  return data;
}

export async function processPlaylist(url: string): Promise<ProcessPlaylistResult> {
  const { data } = await api.post<ProcessPlaylistResult>('/videos/process-playlist', { url });
  return data;
}

export async function validateUrl(url: string): Promise<ValidateResult> {
  const { data } = await api.post<ValidateResult>('/videos/validate', { url });
  return data;
}

export async function getVideos(params: VideoQueryParams = {}): Promise<PaginatedVideos> {
  const { data } = await api.get<PaginatedVideos>('/videos', { params });
  return data;
}

export async function getVideo(id: number | string): Promise<Video> {
  const { data } = await api.get<Video>(`/videos/${id}`);
  return data;
}

export async function retryVideo(id: number): Promise<Video> {
  const { data } = await api.post<Video>(`/videos/${id}/retry`);
  return data;
}

export async function reprocessVideo(id: number): Promise<Video> {
  const { data } = await api.post<Video>(`/videos/${id}/reprocess`);
  return data;
}

export async function cancelVideo(id: number): Promise<Video> {
  const { data } = await api.post<Video>(`/videos/${id}/cancel`);
  return data;
}

export async function deleteVideo(id: number): Promise<void> {
  await api.delete(`/videos/${id}`);
}

// ---- Transcripts & Summaries ----
export async function getTranscript(videoId: number | string): Promise<Transcript> {
  const { data } = await api.get<Transcript>(`/transcripts/${videoId}`);
  return data;
}

export async function getSummary(videoId: number | string): Promise<Summary> {
  const { data } = await api.get<Summary>(`/summaries/${videoId}`);
  return data;
}

export async function updateSummary(
  videoId: number | string,
  payload: Partial<Summary>
): Promise<Summary> {
  const { data } = await api.patch<Summary>(`/summaries/${videoId}`, payload);
  return data;
}

// ---- Exports ----
export async function exportToSheet(videoIds?: number[]): Promise<ExportResult> {
  const { data } = await api.post<ExportResult>('/exports/google-sheet', {
    video_ids: videoIds,
  });
  return data;
}

export async function downloadExcel(videoIds?: number[]): Promise<void> {
  const params = videoIds && videoIds.length ? { video_ids: videoIds.join(',') } : {};
  const res = await api.get('/exports/excel', { params, responseType: 'blob' });
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'elets_transcripts.xlsx';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function getExports(page = 1, pageSize = 20): Promise<PaginatedExports> {
  const { data } = await api.get<PaginatedExports>('/exports', {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function getExportConfig(): Promise<ExportConfig> {
  const { data } = await api.get<ExportConfig>('/exports/config');
  return data;
}

export async function updateExportConfig(payload: ExportConfig): Promise<ExportConfig> {
  const { data } = await api.put<ExportConfig>('/exports/config', payload);
  return data;
}

export async function uploadCredentials(file: File): Promise<ExportRecord | { success: boolean }> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post('/exports/credentials', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

// ---- Stats ----
export async function getStats(): Promise<Stats> {
  const { data } = await api.get<Stats>('/stats');
  return data;
}
