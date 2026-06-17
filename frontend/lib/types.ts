export type VideoStatus =
  | 'queued'
  | 'downloading'
  | 'extracting'
  | 'transcribing'
  | 'summarizing'
  | 'exporting'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface Video {
  id: number;
  youtube_video_id: string;
  video_title: string;
  channel_name?: string | null;
  video_url: string;
  playlist_name?: string | null;
  upload_date?: string | null;
  duration?: number | null; // seconds
  thumbnail?: string | null;
  status: VideoStatus;
  error_message?: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
  transcript?: Transcript | null;
  summary?: Summary | null;
  exports?: ExportRecord[] | null;
}

export interface TranscriptSegment {
  start?: number | null;
  end?: number | null;
  speaker?: string | number | null;
  text: string;
}

export interface Transcript {
  id: number;
  video_id: number;
  full_transcript: string;
  language?: string | null;
  word_count: number;
  processing_time?: number | null;
  provider?: string | null;
  segments?: TranscriptSegment[] | null;
  created_at?: string;
}

export interface Summary {
  id: number;
  video_id: number;
  summary: string; // executive summary
  key_points?: string[] | null;
  quotes?: string[] | null;
  keywords?: string[] | null;
  tags?: string[] | null;
  topics?: string[] | null;
  action_items?: string[] | null;
  key_insights?: string[] | null;
  sentiment?: 'positive' | 'neutral' | 'negative' | 'mixed' | string | null;
  sentiment_detail?: Record<string, unknown> | null;
  model?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedVideos {
  items: Video[];
  total: number;
  page: number;
  page_size: number;
}

export interface ValidateResult {
  valid: boolean;
  type?: 'video' | 'playlist';
  youtube_id?: string;
  title?: string;
  thumbnail?: string;
  channel_name?: string;
  duration?: number;
  item_count?: number;
  message?: string;
}

export interface ProcessPlaylistResult {
  queued: number;
  videos: Video[];
}

export interface TimeBucket {
  date: string;
  count: number;
}

export interface Stats {
  total_videos: number;
  completed: number;
  in_progress: number;
  failed: number;
  avg_transcript_length: number;
  avg_processing_time: number;
  daily: TimeBucket[];
  monthly: TimeBucket[];
  success_rate: number;
  recent_videos: Video[];
}

export interface ExportRecord {
  id: number;
  video_id?: number | null;
  sheet_name?: string | null;
  spreadsheet_id?: string | null;
  status: string;
  error_message?: string | null;
  exported_at: string;
}

export interface ExportResult {
  exported: number;
  failed: number;
  errors: string[];
}

export interface PaginatedExports {
  items: ExportRecord[];
  total: number;
  page: number;
  page_size: number;
}

export interface ExportConfig {
  spreadsheet_id: string;
  worksheet_name: string;
  auto_export: boolean;
  credentials_uploaded?: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface VideoQueryParams {
  status?: string;
  search?: string;
  page?: number;
  page_size?: number;
  sort?: string;
}
