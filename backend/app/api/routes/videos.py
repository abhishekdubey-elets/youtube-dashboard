"""Video processing + management routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.logging import get_logger
from app.models import ProcessingStatus, User, Video
from app.schemas.video import (
    PaginatedVideos,
    PlaylistResult,
    URLRequest,
    ValidateResponse,
    VideoDetail,
    VideoRead,
)
from app.services import youtube

router = APIRouter(prefix="/videos", tags=["videos"])
log = get_logger(__name__)


async def _get_or_create_video(db: AsyncSession, meta: youtube.VideoMeta) -> Video:
    existing = (
        await db.execute(
            select(Video).where(Video.youtube_video_id == meta.youtube_video_id)
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    video = Video(
        youtube_video_id=meta.youtube_video_id,
        video_title=meta.title,
        channel_name=meta.channel_name,
        video_url=meta.url,
        playlist_name=meta.playlist_name,
        upload_date=meta.upload_date,
        duration=meta.duration,
        thumbnail=meta.thumbnail,
        status=ProcessingStatus.QUEUED,
    )
    db.add(video)
    await db.flush()
    return video


@router.post("/validate", response_model=ValidateResponse)
async def validate_url(payload: URLRequest, _: User = Depends(get_current_user)):
    url = payload.url.strip()
    try:
        if youtube.is_playlist_url(url):
            name, items = youtube.fetch_playlist(url)
            first = items[0] if items else None
            return ValidateResponse(
                valid=True,
                type="playlist",
                title=name,
                item_count=len(items),
                thumbnail=first.thumbnail if first else None,
            )
        meta = youtube.fetch_video_metadata(url)
        return ValidateResponse(
            valid=True,
            type="video",
            youtube_id=meta.youtube_video_id,
            title=meta.title,
            channel_name=meta.channel_name,
            thumbnail=meta.thumbnail,
            duration=meta.duration,
        )
    except youtube.YouTubeError as exc:
        return ValidateResponse(valid=False, message=str(exc))


@router.post("/process-video", response_model=VideoRead, status_code=201)
async def process_single_video(
    payload: URLRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from app.workers.tasks import process_video as process_video_task

    try:
        meta = youtube.fetch_video_metadata(payload.url.strip())
    except youtube.YouTubeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    video = await _get_or_create_video(db, meta)
    await db.commit()
    process_video_task.delay(video.id)
    await db.refresh(video)
    return video


@router.post("/process-playlist", response_model=PlaylistResult, status_code=201)
async def process_playlist(
    payload: URLRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from app.workers.tasks import process_playlist_entries

    try:
        _name, metas = youtube.fetch_playlist(payload.url.strip())
    except youtube.YouTubeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not metas:
        raise HTTPException(status_code=400, detail="Playlist is empty.")

    videos: list[Video] = []
    for meta in metas:
        videos.append(await _get_or_create_video(db, meta))
    await db.commit()

    ids = [v.id for v in videos]
    process_playlist_entries.delay(ids)
    return PlaylistResult(queued=len(ids), videos=videos)


@router.get("", response_model=PaginatedVideos)
async def list_videos(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("-created_at"),
):
    stmt = select(Video)
    if status_filter:
        stmt = stmt.where(Video.status == ProcessingStatus(status_filter))
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            Video.video_title.ilike(like) | Video.channel_name.ilike(like)
        )

    # Sorting
    desc = sort.startswith("-")
    field = sort.lstrip("-")
    col = getattr(Video, field, Video.created_at)
    stmt = stmt.order_by(col.desc() if desc else col.asc())

    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    rows = (
        await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()

    return PaginatedVideos(items=rows, total=total, page=page, page_size=page_size)


@router.get("/{video_id}", response_model=VideoDetail)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    video = (
        await db.execute(
            select(Video)
            .options(
                selectinload(Video.transcript),
                selectinload(Video.summary),
                selectinload(Video.exports),
            )
            .where(Video.id == video_id)
        )
    ).scalar_one_or_none()
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.post("/{video_id}/retry", response_model=VideoRead)
async def retry_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from app.workers.tasks import process_video as process_video_task

    video = await db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    video.status = ProcessingStatus.QUEUED
    video.error_message = None
    await db.commit()
    process_video_task.delay(video.id)
    await db.refresh(video)
    return video


@router.post("/{video_id}/reprocess", response_model=VideoRead)
async def reprocess_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Re-run the entire pipeline, resetting retry count."""
    from app.workers.tasks import process_video as process_video_task

    video = await db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    video.status = ProcessingStatus.QUEUED
    video.error_message = None
    video.retry_count = 0
    await db.commit()
    process_video_task.delay(video.id)
    await db.refresh(video)
    return video


@router.post("/{video_id}/cancel", response_model=VideoRead)
async def cancel_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    video = await db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status in (ProcessingStatus.COMPLETED, ProcessingStatus.FAILED):
        raise HTTPException(status_code=400, detail="Video already finished")
    video.status = ProcessingStatus.CANCELLED
    await db.commit()
    await db.refresh(video)
    return video


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    video = await db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    await db.delete(video)
    await db.commit()
