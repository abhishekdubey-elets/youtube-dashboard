"""Export configuration + request schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ExportConfig(BaseModel):
    spreadsheet_id: str = ""
    worksheet_name: str = "Transcripts"
    auto_export: bool = False
    credentials_uploaded: bool = False


class ExportConfigUpdate(BaseModel):
    spreadsheet_id: Optional[str] = None
    worksheet_name: Optional[str] = None
    auto_export: Optional[bool] = None


class ManualExportRequest(BaseModel):
    # When omitted, export all completed-but-unexported videos
    video_ids: Optional[list[int]] = None


class ExportResult(BaseModel):
    exported: int
    failed: int
    errors: list[str] = []
