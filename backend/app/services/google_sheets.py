"""Google Sheets export service using a service-account via gspread."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from app.core.config import settings
from app.core.logging import get_logger
from app.services.app_settings import get_export_config

log = get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

HEADER = [
    "Video URL",
    "Video ID",
    "Video Title",
    "Channel Name",
    "Playlist Name",
    "Upload Date",
    "Duration",
    "Transcript",
    "Summary",
    "Keywords",
    "Sentiment",
    "Processing Time",
    "Processed Date",
    "Status",
]


class GoogleSheetsError(Exception):
    """Raised when a Sheets operation fails."""


def _client() -> gspread.Client:
    cred_path = Path(settings.GOOGLE_CREDENTIALS_FILE)
    if not cred_path.exists():
        raise GoogleSheetsError(
            "Google service-account credentials not uploaded/configured."
        )
    try:
        creds = Credentials.from_service_account_file(str(cred_path), scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as exc:  # noqa: BLE001
        raise GoogleSheetsError(f"Failed to authenticate with Google: {exc}") from exc


def _worksheet():
    cfg = get_export_config()
    spreadsheet_id = cfg["spreadsheet_id"]
    worksheet_name = cfg["worksheet_name"] or "Transcripts"
    if not spreadsheet_id:
        raise GoogleSheetsError("No spreadsheet_id configured.")

    gc = _client()
    try:
        sh = gc.open_by_key(spreadsheet_id)
    except Exception as exc:  # noqa: BLE001
        raise GoogleSheetsError(f"Cannot open spreadsheet {spreadsheet_id}: {exc}") from exc

    try:
        ws = sh.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=worksheet_name, rows=1000, cols=len(HEADER))

    # Ensure header row exists. (gspread 6.x uses update(values, range_name).)
    existing = ws.row_values(1)
    if existing != HEADER:
        ws.update(values=[HEADER], range_name="A1")
    return ws, worksheet_name, spreadsheet_id


def build_row(video: Any) -> list[str]:
    """Map a Video ORM object (with transcript/summary) to a sheet row."""
    transcript = video.transcript
    summary = video.summary
    keywords = ", ".join(summary.keywords) if summary and summary.keywords else ""
    return [
        video.video_url or "",
        video.youtube_video_id or "",
        video.video_title or "",
        video.channel_name or "",
        video.playlist_name or "",
        video.upload_date or "",
        str(video.duration or ""),
        (transcript.full_transcript if transcript else "")[:48000],
        (summary.summary if summary else "")[:20000],
        keywords,
        (summary.sentiment if summary else "") or "",
        str(transcript.processing_time if transcript else "") or "",
        video.updated_at.isoformat() if video.updated_at else "",
        video.status.value if hasattr(video.status, "value") else str(video.status),
    ]


def append_video(video: Any) -> tuple[str, str]:
    """Append a single video row. Returns (worksheet_name, spreadsheet_id)."""
    ws, worksheet_name, spreadsheet_id = _worksheet()
    try:
        ws.append_row(build_row(video), value_input_option="RAW")
    except Exception as exc:  # noqa: BLE001
        raise GoogleSheetsError(f"Failed to append row: {exc}") from exc
    log.info("exported_to_sheet", youtube_video_id=video.youtube_video_id)
    return worksheet_name, spreadsheet_id
