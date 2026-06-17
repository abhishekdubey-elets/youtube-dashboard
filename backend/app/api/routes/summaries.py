"""AI summary routes (read + edit)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Summary, User
from app.schemas.video import SummaryRead, SummaryUpdate

router = APIRouter(prefix="/summaries", tags=["summaries"])


async def _get_summary(db: AsyncSession, video_id: int) -> Summary:
    summary = (
        await db.execute(select(Summary).where(Summary.video_id == video_id))
    ).scalar_one_or_none()
    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary


@router.get("/{video_id}", response_model=SummaryRead)
async def get_summary(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await _get_summary(db, video_id)


@router.patch("/{video_id}", response_model=SummaryRead)
async def update_summary(
    video_id: int,
    payload: SummaryUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    summary = await _get_summary(db, video_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(summary, key, value)
    await db.commit()
    await db.refresh(summary)
    return summary
