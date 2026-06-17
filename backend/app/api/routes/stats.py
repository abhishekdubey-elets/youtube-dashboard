"""Dashboard statistics route."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import ProcessingStatus, Transcript, User, Video
from app.schemas.video import StatsResponse, TimeBucket, VideoRead

router = APIRouter(tags=["stats"])

IN_PROGRESS = (
    ProcessingStatus.QUEUED,
    ProcessingStatus.DOWNLOADING,
    ProcessingStatus.EXTRACTING,
    ProcessingStatus.TRANSCRIBING,
    ProcessingStatus.SUMMARIZING,
    ProcessingStatus.EXPORTING,
)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    total = (await db.execute(select(func.count(Video.id)))).scalar_one()
    completed = (
        await db.execute(
            select(func.count(Video.id)).where(
                Video.status == ProcessingStatus.COMPLETED
            )
        )
    ).scalar_one()
    failed = (
        await db.execute(
            select(func.count(Video.id)).where(Video.status == ProcessingStatus.FAILED)
        )
    ).scalar_one()
    in_progress = (
        await db.execute(
            select(func.count(Video.id)).where(Video.status.in_(IN_PROGRESS))
        )
    ).scalar_one()

    avg_words = (
        await db.execute(select(func.coalesce(func.avg(Transcript.word_count), 0)))
    ).scalar_one()
    avg_time = (
        await db.execute(
            select(func.coalesce(func.avg(Transcript.processing_time), 0))
        )
    ).scalar_one()

    success_rate = round((completed / total) * 100, 1) if total else 0.0

    # Daily buckets (last 14 days)
    since = datetime.now(timezone.utc) - timedelta(days=14)
    daily_rows = (
        await db.execute(
            select(
                func.date(Video.created_at).label("d"), func.count(Video.id)
            )
            .where(Video.created_at >= since)
            .group_by("d")
            .order_by("d")
        )
    ).all()
    daily = [TimeBucket(date=str(d), count=c) for d, c in daily_rows]

    # Monthly buckets (last 12 months)
    monthly_rows = (
        await db.execute(
            select(
                func.to_char(func.date_trunc("month", Video.created_at), "YYYY-MM").label("m"),
                func.count(Video.id),
            )
            .group_by("m")
            .order_by("m")
        )
    ).all()
    monthly = [TimeBucket(date=str(m), count=c) for m, c in monthly_rows]

    recent = (
        await db.execute(select(Video).order_by(Video.created_at.desc()).limit(8))
    ).scalars().all()

    return StatsResponse(
        total_videos=total,
        completed=completed,
        in_progress=in_progress,
        failed=failed,
        avg_transcript_length=round(float(avg_words), 1),
        avg_processing_time=round(float(avg_time), 1),
        success_rate=success_rate,
        daily=daily,
        monthly=monthly,
        recent_videos=[VideoRead.model_validate(v) for v in recent],
    )
