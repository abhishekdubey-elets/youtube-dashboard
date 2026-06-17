"""Pydantic schemas for videos, transcripts, summaries, exports and stats."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.video import ProcessingStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Requests --------------------------------------------------------------
class URLRequest(BaseModel):
    url: str = Field(..., examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"])


class ValidateResponse(BaseModel):
    valid: bool
    type: Optional[str] = None  # "video" | "playlist"
    youtube_id: Optional[str] = None
    title: Optional[str] = None
    channel_name: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    item_count: Optional[int] = None
    message: Optional[str] = None


# --- Nested read models ----------------------------------------------------
class TranscriptRead(ORMModel):
    id: int
    video_id: int
    full_transcript: str
    language: Optional[str] = None
    word_count: int
    processing_time: Optional[float] = None
    provider: Optional[str] = None
    segments: Optional[list[dict[str, Any]]] = None
    created_at: datetime


class SummaryRead(ORMModel):
    id: int
    video_id: int
    summary: str
    key_points: Optional[list[str]] = None
    quotes: Optional[list[str]] = None
    keywords: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    topics: Optional[list[str]] = None
    action_items: Optional[list[str]] = None
    key_insights: Optional[list[str]] = None
    sentiment: Optional[str] = None
    sentiment_detail: Optional[dict[str, Any]] = None
    model: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SummaryUpdate(BaseModel):
    summary: Optional[str] = None
    key_points: Optional[list[str]] = None
    quotes: Optional[list[str]] = None
    keywords: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    topics: Optional[list[str]] = None
    action_items: Optional[list[str]] = None
    key_insights: Optional[list[str]] = None
    sentiment: Optional[str] = None


class ExportRead(ORMModel):
    id: int
    video_id: int
    sheet_name: Optional[str] = None
    spreadsheet_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    exported_at: datetime


class VideoRead(ORMModel):
    id: int
    youtube_video_id: str
    video_title: str
    channel_name: Optional[str] = None
    video_url: str
    playlist_name: Optional[str] = None
    upload_date: Optional[str] = None
    duration: Optional[int] = None
    thumbnail: Optional[str] = None
    status: ProcessingStatus
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime


class VideoDetail(VideoRead):
    transcript: Optional[TranscriptRead] = None
    summary: Optional[SummaryRead] = None
    exports: list[ExportRead] = []


class PaginatedVideos(BaseModel):
    items: list[VideoRead]
    total: int
    page: int
    page_size: int


class PlaylistResult(BaseModel):
    queued: int
    videos: list[VideoRead]


# --- Stats -----------------------------------------------------------------
class TimeBucket(BaseModel):
    date: str
    count: int


class StatsResponse(BaseModel):
    total_videos: int
    completed: int
    in_progress: int
    failed: int
    avg_transcript_length: float
    avg_processing_time: float
    success_rate: float
    daily: list[TimeBucket]
    monthly: list[TimeBucket]
    recent_videos: list[VideoRead]
