'use client';

import {
  useMutation,
  useQuery,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query';
import * as apiClient from './api';
import type {
  ExportConfig,
  Summary,
  VideoQueryParams,
} from './types';

export const queryKeys = {
  stats: ['stats'] as const,
  videos: (params: VideoQueryParams) => ['videos', params] as const,
  video: (id: number | string) => ['video', String(id)] as const,
  transcript: (id: number | string) => ['transcript', String(id)] as const,
  summary: (id: number | string) => ['summary', String(id)] as const,
  exports: (page: number, pageSize: number) => ['exports', page, pageSize] as const,
  exportConfig: ['export-config'] as const,
};

// ---- Stats ----
export function useStats() {
  return useQuery({
    queryKey: queryKeys.stats,
    queryFn: apiClient.getStats,
    refetchInterval: 30_000,
  });
}

// ---- Videos ----
export function useVideos(params: VideoQueryParams, options?: { refetchInterval?: number }) {
  return useQuery({
    queryKey: queryKeys.videos(params),
    queryFn: () => apiClient.getVideos(params),
    placeholderData: keepPreviousData,
    refetchInterval: options?.refetchInterval,
  });
}

export function useVideo(id: number | string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.video(id),
    queryFn: () => apiClient.getVideo(id),
    enabled: enabled && id !== undefined && id !== null && id !== '',
  });
}

export function useTranscript(videoId: number | string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.transcript(videoId),
    queryFn: () => apiClient.getTranscript(videoId),
    enabled,
  });
}

export function useSummary(videoId: number | string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.summary(videoId),
    queryFn: () => apiClient.getSummary(videoId),
    enabled,
  });
}

// ---- Mutations ----
export function useProcessVideo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (url: string) => apiClient.processVideo(url),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['videos'] });
      qc.invalidateQueries({ queryKey: queryKeys.stats });
    },
  });
}

export function useProcessPlaylist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (url: string) => apiClient.processPlaylist(url),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['videos'] });
      qc.invalidateQueries({ queryKey: queryKeys.stats });
    },
  });
}

export function useValidateUrl() {
  return useMutation({
    mutationFn: (url: string) => apiClient.validateUrl(url),
  });
}

export function useRetryVideo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.retryVideo(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['videos'] });
      qc.invalidateQueries({ queryKey: queryKeys.stats });
    },
  });
}

export function useReprocessVideo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.reprocessVideo(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['videos'] });
      qc.invalidateQueries({ queryKey: queryKeys.stats });
    },
  });
}

export function useCancelVideo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.cancelVideo(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['videos'] });
      qc.invalidateQueries({ queryKey: queryKeys.stats });
    },
  });
}

export function useDeleteVideo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.deleteVideo(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['videos'] });
      qc.invalidateQueries({ queryKey: queryKeys.stats });
    },
  });
}

export function useUpdateSummary(videoId: number | string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Summary>) => apiClient.updateSummary(videoId, payload),
    onSuccess: (data) => {
      qc.setQueryData(queryKeys.summary(videoId), data);
      qc.invalidateQueries({ queryKey: queryKeys.summary(videoId) });
    },
  });
}

// ---- Exports ----
export function useExports(page: number, pageSize: number) {
  return useQuery({
    queryKey: queryKeys.exports(page, pageSize),
    queryFn: () => apiClient.getExports(page, pageSize),
    placeholderData: keepPreviousData,
  });
}

export function useExportConfig() {
  return useQuery({
    queryKey: queryKeys.exportConfig,
    queryFn: apiClient.getExportConfig,
  });
}

export function useUpdateExportConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExportConfig) => apiClient.updateExportConfig(payload),
    onSuccess: (data) => {
      qc.setQueryData(queryKeys.exportConfig, data);
    },
  });
}

export function useUploadCredentials() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => apiClient.uploadCredentials(file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.exportConfig });
    },
  });
}

export function useExportToSheet() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (videoIds?: number[]) => apiClient.exportToSheet(videoIds),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['exports'] });
    },
  });
}
