"""YouTube interaction layer built on yt-dlp.

Responsibilities:
* Parse/validate single-video and playlist URLs.
* Fetch metadata without downloading.
* Download + extract normalized audio to local storage.

All network/format errors are normalized into ``YouTubeError`` so the worker
can map them to user-friendly failure messages.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError

from app.core.config import settings
from app.core.logging import get_logger
from app.services.storage import video_dir

log = get_logger(__name__)

_VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})")
_PLAYLIST_ID_RE = re.compile(r"[?&]list=([A-Za-z0-9_-]+)")


class YouTubeError(Exception):
    """Normalized, user-presentable YouTube error."""


@dataclass
class VideoMeta:
    youtube_video_id: str
    title: str
    channel_name: Optional[str]
    url: str
    duration: Optional[int]
    thumbnail: Optional[str]
    upload_date: Optional[str]
    playlist_name: Optional[str] = None


def _base_opts() -> dict[str, Any]:
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": False,
        "ignoreerrors": False,
        "extract_flat": False,
    }
    if settings.YTDLP_COOKIES_FILE:
        opts["cookiefile"] = settings.YTDLP_COOKIES_FILE
    return opts


def extract_video_id(url: str) -> Optional[str]:
    m = _VIDEO_ID_RE.search(url)
    if m:
        return m.group(1)
    # Bare 11-char id
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url.strip()):
        return url.strip()
    return None


def is_playlist_url(url: str) -> bool:
    return "list=" in url and "watch?v=" not in url or "/playlist?" in url


def _map_error(exc: Exception) -> YouTubeError:
    msg = str(exc).lower()
    if "private" in msg:
        return YouTubeError("This video is private.")
    if "deleted" in msg or "removed" in msg or "unavailable" in msg:
        return YouTubeError("This video has been deleted or is unavailable.")
    if "age" in msg and "restrict" in msg:
        return YouTubeError("This video is age-restricted; cookies are required.")
    if "members-only" in msg or "join this channel" in msg:
        return YouTubeError("This video is members-only.")
    return YouTubeError(f"YouTube error: {exc}")


def _to_meta(info: dict[str, Any], playlist_name: Optional[str] = None) -> VideoMeta:
    return VideoMeta(
        youtube_video_id=info["id"],
        title=info.get("title") or "Untitled",
        channel_name=info.get("channel") or info.get("uploader"),
        url=info.get("webpage_url") or f"https://www.youtube.com/watch?v={info['id']}",
        duration=info.get("duration"),
        thumbnail=info.get("thumbnail"),
        upload_date=info.get("upload_date"),
        playlist_name=playlist_name,
    )


def fetch_video_metadata(url: str) -> VideoMeta:
    """Fetch metadata for a single video without downloading."""
    opts = _base_opts() | {"noplaylist": True, "skip_download": True}
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if info is None:
            raise YouTubeError("Could not read video metadata.")
        return _to_meta(info)
    except (DownloadError, ExtractorError) as exc:
        raise _map_error(exc) from exc


def fetch_playlist(url: str) -> tuple[str, list[VideoMeta]]:
    """Return (playlist_title, [VideoMeta]) using a flat (fast) extraction."""
    opts = _base_opts() | {
        "extract_flat": "in_playlist",
        "skip_download": True,
        "playlistend": settings.YTDLP_MAX_PLAYLIST_ITEMS,
    }
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except (DownloadError, ExtractorError) as exc:
        raise _map_error(exc) from exc

    if info is None or "entries" not in info:
        raise YouTubeError("Could not read playlist or it is empty.")

    playlist_name = info.get("title") or "Playlist"
    metas: list[VideoMeta] = []
    for entry in info["entries"]:
        if not entry:
            continue
        vid = entry.get("id")
        if not vid:
            continue
        metas.append(
            VideoMeta(
                youtube_video_id=vid,
                title=entry.get("title") or "Untitled",
                channel_name=entry.get("channel") or entry.get("uploader"),
                url=entry.get("url") or f"https://www.youtube.com/watch?v={vid}",
                duration=entry.get("duration"),
                thumbnail=entry.get("thumbnails", [{}])[-1].get("url")
                if entry.get("thumbnails")
                else f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                upload_date=entry.get("upload_date"),
                playlist_name=playlist_name,
            )
        )
    return playlist_name, metas


def download_audio(youtube_video_id: str) -> Path:
    """Download + extract a normalized 16kHz mono WAV for transcription.

    Returns the path to the produced audio file. Raises ``YouTubeError``.
    """
    url = f"https://www.youtube.com/watch?v={youtube_video_id}"
    out_dir = video_dir(youtube_video_id)
    out_template = str(out_dir / "%(id)s.%(ext)s")

    opts = _base_opts() | {
        "noplaylist": True,
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }
        ],
        # Normalize to 16kHz mono — ideal for Whisper/Deepgram
        "postprocessor_args": ["-ac", "1", "-ar", "16000"],
    }

    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([url])
    except (DownloadError, ExtractorError) as exc:
        raise _map_error(exc) from exc

    wav = out_dir / f"{youtube_video_id}.wav"
    if not wav.exists():
        candidates = list(out_dir.glob(f"{youtube_video_id}.*"))
        if not candidates:
            raise YouTubeError("Audio download produced no file.")
        return candidates[0]
    return wav
