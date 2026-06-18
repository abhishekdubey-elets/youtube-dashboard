"""Celery tasks implementing the processing pipeline.

Pipeline (per video):
    download -> extract/normalize audio -> transcribe -> summarize
    -> persist -> (optional) export to Google Sheets -> cleanup

Each stage updates ``Video.status`` so the UI can show live progress. Failures
are retried up to ``MAX_RETRIES`` with exponential backoff; after that the
video is marked ``FAILED`` with a user-friendly ``error_message``.
"""
from __future__ import annotations

import time
from typing import Optional

from celery import shared_task
from celery.utils.log import get_task_logger

# Importing the configured app here guarantees it is created and registered as
# the default app whenever these tasks are imported (e.g. by the FastAPI
# process), so `.delay()` enqueues to Redis rather than the amqp:// default.
from app.workers import celery_app  # noqa: F401
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models import ExportRecord, ProcessingStatus, Summary, Transcript, Video
from app.models.export import ExportStatus
from app.services import google_sheets, storage, summarization, youtube
from app.services.app_settings import get_export_config
from app.services.transcription import get_transcriber

logger = get_task_logger(__name__)


# --- helpers ---------------------------------------------------------------
def _get_video(db: Session, video_id: int) -> Optional[Video]:
    return db.execute(
        select(Video)
        .options(selectinload(Video.transcript), selectinload(Video.summary))
        .where(Video.id == video_id)
    ).scalar_one_or_none()


def _set_status(db: Session, video: Video, status: ProcessingStatus) -> None:
    video.status = status
    db.add(video)
    db.commit()
    logger.info("video %s -> %s", video.id, status.value)


# --- main pipeline ---------------------------------------------------------
@shared_task(
    bind=True,
    name="app.workers.tasks.process_video",
    max_retries=settings.MAX_RETRIES,
    default_retry_delay=30,
)
def process_video(self, video_id: int) -> dict:
    """Run the full pipeline for a single video."""
    from app.core.database import session_scope

    with session_scope() as db:
        video = _get_video(db, video_id)
        if video is None:
            return {"error": "video not found", "video_id": video_id}
        if video.status == ProcessingStatus.CANCELLED:
            return {"status": "cancelled", "video_id": video_id}

        yt_id = video.youtube_video_id
        title = video.video_title
        channel = video.channel_name or ""

    try:
        # 1. Download + extract + normalize audio -----------------------------
        with session_scope() as db:
            _set_status(db, _get_video(db, video_id), ProcessingStatus.DOWNLOADING)
        audio_path = youtube.download_audio(yt_id)

        with session_scope() as db:
            _set_status(db, _get_video(db, video_id), ProcessingStatus.EXTRACTING)
        # (audio already extracted+normalized to 16kHz mono WAV by yt-dlp)

        # 2. Transcribe -------------------------------------------------------
        with session_scope() as db:
            _set_status(db, _get_video(db, video_id), ProcessingStatus.TRANSCRIBING)
        t0 = time.monotonic()
        transcriber = get_transcriber()
        result = transcriber.transcribe(audio_path)
        elapsed = round(time.monotonic() - t0, 2)

        with session_scope() as db:
            video = _get_video(db, video_id)
            transcript = video.transcript or Transcript(video_id=video.id)
            transcript.full_transcript = result.text
            transcript.language = result.language
            transcript.word_count = result.word_count
            transcript.processing_time = elapsed
            transcript.provider = result.provider
            transcript.segments = result.segments or None
            db.add(transcript)
            db.commit()

        # 3. Summarize (optional) --------------------------------------------
        # The AI summary requires an OpenAI key. Transcription can run locally
        # without one, so summarization is best-effort: if no key is configured
        # (or the call fails) we keep the transcript and still complete.
        if summarization.is_available():
            with session_scope() as db:
                _set_status(db, _get_video(db, video_id), ProcessingStatus.SUMMARIZING)
            try:
                summary_data = summarization.generate_summary(title, channel, result.text)
                with session_scope() as db:
                    video = _get_video(db, video_id)
                    summary = video.summary or Summary(video_id=video.id)
                    for key, value in summary_data.items():
                        setattr(summary, key, value)
                    db.add(summary)
                    db.commit()
            except Exception as exc:  # noqa: BLE001 — summary must not fail the pipeline
                logger.warning("summarization skipped for video %s: %s", video_id, exc)
        else:
            logger.info(
                "summarization skipped for video %s (no OPENAI_API_KEY configured)",
                video_id,
            )

        # 4. Optional auto-export --------------------------------------------
        exported = False
        if get_export_config().get("auto_export"):
            with session_scope() as db:
                _set_status(db, _get_video(db, video_id), ProcessingStatus.EXPORTING)
            export_to_sheet.delay(video_id)
            exported = True

        # 5. Complete + cleanup ----------------------------------------------
        with session_scope() as db:
            video = _get_video(db, video_id)
            video.status = ProcessingStatus.COMPLETED
            video.error_message = None
            db.add(video)
            db.commit()
        storage.cleanup_video_files(yt_id)

        return {"status": "completed", "video_id": video_id, "exported": exported}

    except Exception as exc:  # noqa: BLE001
        logger.exception("pipeline failed for video %s", video_id)
        with session_scope() as db:
            video = _get_video(db, video_id)
            if video is not None:
                video.retry_count = (video.retry_count or 0) + 1
                if self.request.retries < settings.MAX_RETRIES:
                    db.add(video)
                    db.commit()
                    storage.cleanup_video_files(yt_id)
                    raise self.retry(exc=exc, countdown=30 * (2**self.request.retries))
                video.status = ProcessingStatus.FAILED
                video.error_message = str(exc)
                db.add(video)
                db.commit()
        storage.cleanup_video_files(yt_id)
        return {"status": "failed", "video_id": video_id, "error": str(exc)}


@shared_task(name="app.workers.tasks.process_playlist_entries")
def process_playlist_entries(video_ids: list[int]) -> dict:
    """Fan-out: enqueue a pipeline task per video in a playlist."""
    for vid in video_ids:
        process_video.delay(vid)
    return {"queued": len(video_ids)}


@shared_task(name="app.workers.tasks.export_to_sheet")
def export_to_sheet(video_id: int) -> dict:
    """Export a single completed video to Google Sheets."""
    from app.core.database import session_scope

    with session_scope() as db:
        video = db.execute(
            select(Video)
            .options(selectinload(Video.transcript), selectinload(Video.summary))
            .where(Video.id == video_id)
        ).scalar_one_or_none()
        if video is None:
            return {"error": "video not found"}

        try:
            worksheet_name, spreadsheet_id = google_sheets.append_video(video)
            record = ExportRecord(
                video_id=video.id,
                sheet_name=worksheet_name,
                spreadsheet_id=spreadsheet_id,
                status=ExportStatus.SUCCESS,
            )
            db.add(record)
            if video.status == ProcessingStatus.EXPORTING:
                video.status = ProcessingStatus.COMPLETED
                db.add(video)
            db.commit()
            return {"status": "success", "video_id": video_id}
        except Exception as exc:  # noqa: BLE001
            logger.exception("export failed for video %s", video_id)
            db.add(
                ExportRecord(
                    video_id=video.id,
                    status=ExportStatus.FAILED,
                    error_message=str(exc),
                )
            )
            db.commit()
            return {"status": "failed", "video_id": video_id, "error": str(exc)}


@shared_task(name="app.workers.tasks.purge_stale_audio")
def purge_stale_audio() -> dict:
    removed = storage.purge_stale_files()
    return {"removed": removed}
