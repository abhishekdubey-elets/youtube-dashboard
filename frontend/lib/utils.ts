import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { VideoStatus } from './types';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const PIPELINE_STAGES: VideoStatus[] = [
  'queued',
  'downloading',
  'extracting',
  'transcribing',
  'summarizing',
  'exporting',
  'completed',
];

export function stageProgress(status: VideoStatus): number {
  if (status === 'failed') return 100;
  const idx = PIPELINE_STAGES.indexOf(status);
  if (idx === -1) return 0;
  return Math.round((idx / (PIPELINE_STAGES.length - 1)) * 100);
}

export function formatDate(value?: string | null): string {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(value?: string | null): string {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatNumber(value?: number | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) return '0';
  return new Intl.NumberFormat().format(Math.round(value));
}

export function formatSeconds(seconds?: number | null): string {
  if (!seconds || Number.isNaN(seconds)) return '0s';
  const s = Math.round(seconds);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  if (m < 60) return `${m}m ${rem}s`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}m`;
}

export function statusLabel(status: VideoStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

const ID_REGEX = /(?:v=|\/embed\/|\.be\/|\/shorts\/)([A-Za-z0-9_-]{11})/;

export function extractYouTubeId(input?: string | null): string | null {
  if (!input) return null;
  if (/^[A-Za-z0-9_-]{11}$/.test(input)) return input;
  const m = input.match(ID_REGEX);
  return m ? m[1] : null;
}

export function youtubeThumbnail(videoId?: string | null): string | undefined {
  if (!videoId) return undefined;
  return `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`;
}

export function downloadTextFile(filename: string, text: string) {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
