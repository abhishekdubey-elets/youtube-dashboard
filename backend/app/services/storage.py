"""Local file storage helpers for downloaded/extracted audio."""
from __future__ import annotations

import os
import time
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


def storage_root() -> Path:
    root = Path(settings.STORAGE_DIR)
    root.mkdir(parents=True, exist_ok=True)
    return root


def video_dir(youtube_video_id: str) -> Path:
    d = storage_root() / youtube_video_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def cleanup_video_files(youtube_video_id: str) -> None:
    """Delete all temporary audio files for a video after processing."""
    if not settings.DELETE_AUDIO_AFTER_PROCESSING:
        return
    d = storage_root() / youtube_video_id
    if not d.exists():
        return
    for f in d.glob("*"):
        try:
            f.unlink()
        except OSError as exc:  # pragma: no cover - best effort
            log.warning("cleanup_failed", file=str(f), error=str(exc))
    try:
        d.rmdir()
    except OSError:
        pass
    log.info("cleaned_up_audio", youtube_video_id=youtube_video_id)


def purge_stale_files() -> int:
    """Remove audio older than ``MAX_AUDIO_AGE_HOURS``. Returns files removed."""
    cutoff = time.time() - settings.MAX_AUDIO_AGE_HOURS * 3600
    removed = 0
    for f in storage_root().rglob("*"):
        if f.is_file() and f.stat().st_mtime < cutoff:
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass
    return removed
