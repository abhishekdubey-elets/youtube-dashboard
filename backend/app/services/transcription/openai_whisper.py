"""OpenAI Whisper API transcription provider (preferred / Option 1)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from openai import OpenAI

from app.core.config import settings
from app.core.logging import get_logger
from app.services.transcription.base import (
    TranscriptionError,
    TranscriptionProvider,
    TranscriptionResult,
)

log = get_logger(__name__)


class OpenAIWhisperProvider(TranscriptionProvider):
    name = "openai_whisper"

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise TranscriptionError("OPENAI_API_KEY is not configured.")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_WHISPER_MODEL

    def transcribe(
        self, audio_path: Path, language: Optional[str] = None
    ) -> TranscriptionResult:
        lang = language or settings.TRANSCRIPTION_LANGUAGE or None
        try:
            with audio_path.open("rb") as fh:
                resp = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=fh,
                    language=lang,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors
            raise TranscriptionError(f"OpenAI Whisper failed: {exc}") from exc

        segments = []
        for seg in getattr(resp, "segments", None) or []:
            segments.append(
                {
                    "start": getattr(seg, "start", None),
                    "end": getattr(seg, "end", None),
                    "text": getattr(seg, "text", ""),
                }
            )

        return TranscriptionResult(
            text=resp.text,
            language=getattr(resp, "language", lang),
            segments=segments,
            provider=self.name,
        )
