"""Celery application + beat schedule."""
from __future__ import annotations

from celery import Celery

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
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=30,
    task_max_retries=settings.MAX_RETRIES,
)

# Periodic maintenance tasks
celery.conf.beat_schedule = {
    "purge-stale-audio": {
        "task": "app.workers.tasks.purge_stale_audio",
        "schedule": 3600.0,  # hourly
    },
}
