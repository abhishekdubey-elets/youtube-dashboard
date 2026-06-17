"""Google Sheets export routes: config, credentials upload, manual export, history."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, require_admin
from app.core.config import settings
from app.core.database import get_db
from app.models import ExportRecord, ProcessingStatus, User, Video
from app.schemas.export import (
    ExportConfig,
    ExportConfigUpdate,
    ExportResult,
    ManualExportRequest,
)
from app.schemas.video import ExportRead
from app.services import google_sheets
from app.services.app_settings import get_export_config, update_export_config

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/config", response_model=ExportConfig)
async def read_config(_: User = Depends(get_current_user)):
    return ExportConfig(**get_export_config())


@router.put("/config", response_model=ExportConfig)
async def write_config(
    payload: ExportConfigUpdate, _: User = Depends(require_admin)
):
    cfg = update_export_config(**payload.model_dump(exclude_unset=True))
    return ExportConfig(**cfg)


@router.post("/credentials", response_model=ExportConfig)
async def upload_credentials(
    file: UploadFile = File(...), _: User = Depends(require_admin)
):
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Expected a service-account .json")
    dest = Path(settings.GOOGLE_CREDENTIALS_FILE)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(await file.read())
    return ExportConfig(**get_export_config())


@router.post("/google-sheet", response_model=ExportResult)
async def manual_export(
    payload: ManualExportRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = (
        select(Video)
        .options(selectinload(Video.transcript), selectinload(Video.summary))
        .where(Video.status == ProcessingStatus.COMPLETED)
    )
    if payload.video_ids:
        stmt = stmt.where(Video.id.in_(payload.video_ids))
    videos = (await db.execute(stmt)).scalars().all()

    exported, failed, errors = 0, 0, []
    for video in videos:
        try:
            worksheet_name, spreadsheet_id = google_sheets.append_video(video)
            db.add(
                ExportRecord(
                    video_id=video.id,
                    sheet_name=worksheet_name,
                    spreadsheet_id=spreadsheet_id,
                )
            )
            exported += 1
        except google_sheets.GoogleSheetsError as exc:
            failed += 1
            errors.append(f"{video.youtube_video_id}: {exc}")
    await db.commit()
    return ExportResult(exported=exported, failed=failed, errors=errors)


@router.get("", response_model=dict)
async def export_history(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    total = (await db.execute(select(func.count(ExportRecord.id)))).scalar_one()
    rows = (
        await db.execute(
            select(ExportRecord)
            .order_by(ExportRecord.exported_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return {
        "items": [ExportRead.model_validate(r).model_dump() for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
