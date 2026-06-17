"""Video model — the central entity of the pipeline."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.export import ExportRecord
    from app.models.summary import Summary
    from app.models.transcript import Transcript


class ProcessingStatus(str, enum.Enum):
    """Pipeline status. Order mirrors the processing stages."""

    QUEUED = "queued"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    TRANSCRIBING = "transcribing"
    SUMMARIZING = "summarizing"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    youtube_video_id: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    video_title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    channel_name: Mapped[Optional[str]] = mapped_column(String(255))
    video_url: Mapped[str] = mapped_column(String(512), nullable=False)
    playlist_name: Mapped[Optional[str]] = mapped_column(String(512))
    upload_date: Mapped[Optional[str]] = mapped_column(String(32))
    duration: Mapped[Optional[int]] = mapped_column(Integer, comment="seconds")
    thumbnail: Mapped[Optional[str]] = mapped_column(String(512))

    status: Mapped[ProcessingStatus] = mapped_column(
        # Store the lowercase .value ("queued"), not the member name, to match
        # the DB enum created by the migration.
        SAEnum(
            ProcessingStatus,
            name="processing_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ProcessingStatus.QUEUED,
        index=True,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    transcript: Mapped[Optional["Transcript"]] = relationship(
        back_populates="video", uselist=False, cascade="all, delete-orphan"
    )
    summary: Mapped[Optional["Summary"]] = relationship(
        back_populates="video", uselist=False, cascade="all, delete-orphan"
    )
    exports: Mapped[list["ExportRecord"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )
