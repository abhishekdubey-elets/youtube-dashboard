"""Transcript routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Transcript, User
from app.schemas.video import TranscriptRead

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.get("/{video_id}", response_model=TranscriptRead)
async def get_transcript(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    transcript = (
        await db.execute(select(Transcript).where(Transcript.video_id == video_id))
    ).scalar_one_or_none()
    if transcript is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return transcript
