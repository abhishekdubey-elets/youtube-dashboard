"""Transcript model."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.video import Video


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), unique=True, index=True
    )

    full_transcript: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[Optional[str]] = mapped_column(String(16))
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_time: Mapped[Optional[float]] = mapped_column(
        Float, comment="seconds spent transcribing"
    )
    provider: Mapped[Optional[str]] = mapped_column(String(32))
    # List of {start, end, speaker?, text} segments when available
    segments: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    video: Mapped["Video"] = relationship(back_populates="transcript")
