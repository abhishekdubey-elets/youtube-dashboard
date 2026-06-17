"""Google Sheets export record."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.video import Video


class ExportStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"


class ExportRecord(Base):
    __tablename__ = "exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), index=True
    )

    sheet_name: Mapped[Optional[str]] = mapped_column(String(255))
    spreadsheet_id: Mapped[Optional[str]] = mapped_column(String(128))
    status: Mapped[ExportStatus] = mapped_column(
        SAEnum(ExportStatus, name="export_status"), default=ExportStatus.SUCCESS
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    exported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    video: Mapped["Video"] = relationship(back_populates="exports")
