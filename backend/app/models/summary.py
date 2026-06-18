"""AI summary model."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.video import Video


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), unique=True, index=True
    )

    # Executive / narrative summary
    summary: Mapped[str] = mapped_column(Text, default="")
    # Structured fields stored as JSON arrays for flexibility
    key_points: Mapped[Optional[list[str]]] = mapped_column(JSONB)
    quotes: Mapped[Optional[list[str]]] = mapped_column(JSONB)
    keywords: Mapped[Optional[list[str]]] = mapped_column(JSONB)
    tags: Mapped[Optional[list[str]]] = mapped_column(JSONB)
    topics: Mapped[Optional[list[str]]] = mapped_column(JSONB)
    action_items: Mapped[Optional[list[str]]] = mapped_column(JSONB)
    key_insights: Mapped[Optional[list[str]]] = mapped_column(JSONB)

    sentiment: Mapped[Optional[str]] = mapped_column(String(32))
    sentiment_detail: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)

    # Main guest / speaker of the episode (LLM-extracted, title fallback).
    speaker: Mapped[Optional[str]] = mapped_column(String(255))

    model: Mapped[Optional[str]] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    video: Mapped["Video"] = relationship(back_populates="summary")
