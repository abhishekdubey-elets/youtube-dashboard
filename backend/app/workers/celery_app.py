"""Celery application + beat schedule."""
from __future__ import annotations

from celery import Celery
from celery.signals import worker_ready

from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

celery = Celery(
    "elets_transcripts",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.TASK_TIMEOUT_SECONDS,
    task_soft_time_limit=settings.TASK_TIMEOUT_SECONDS - 60,
    # Ack on start (not late): if the worker is killed/restarted mid-task the
    # message is NOT redelivered (avoiding duplicate work); the worker_ready
    # reconciliation below re-queues anything left in-progress instead.
    task_acks_late=False,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=30,
    task_max_retries=settings.MAX_RETRIES,
)

# Make this the current/default app so `@shared_task(...).delay()` routes to
# THIS broker (Redis) from any process that imports it — notably the FastAPI
# API process, which enqueues tasks without launching a worker. Without this,
# shared tasks fall back to Celery's default amqp:// broker and fail.
celery.set_default()

@worker_ready.connect
def _requeue_orphaned_videos(sender=None, **kwargs):
    """Re-queue videos stranded mid-pipeline by a previous crash/restart.

    On a fresh worker start nothing is actively processing, so any video left
    in a non-terminal 'processing' state has no running task. Reset those to
    QUEUED and re-enqueue them so they resume automatically.
    """
    from sqlalchemy import select

    from app.core.database import session_scope
    from app.models import ProcessingStatus, Video

    in_progress = (
        ProcessingStatus.DOWNLOADING,
        ProcessingStatus.EXTRACTING,
        ProcessingStatus.TRANSCRIBING,
        ProcessingStatus.SUMMARIZING,
        ProcessingStatus.EXPORTING,
    )
    try:
        with session_scope() as db:
            rows = (
                db.execute(select(Video).where(Video.status.in_(in_progress)))
                .scalars()
                .all()
            )
            ids = [v.id for v in rows]
            for v in rows:
                v.status = ProcessingStatus.QUEUED
                db.add(v)
        for vid in ids:
            celery.send_task("app.workers.tasks.process_video", args=[vid])
        if ids:
            import logging

            logging.getLogger(__name__).warning("requeued orphaned videos: %s", ids)
    except Exception as exc:  # noqa: BLE001 — never block worker startup
        import logging

        logging.getLogger(__name__).warning("orphan requeue skipped: %s", exc)


# Periodic maintenance tasks
celery.conf.beat_schedule = {
    "purge-stale-audio": {
        "task": "app.workers.tasks.purge_stale_audio",
        "schedule": 3600.0,  # hourly
    },
}
