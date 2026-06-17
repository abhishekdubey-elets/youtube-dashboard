"""Deepgram transcription provider (Option 3)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services.transcription.base import (
    TranscriptionError,
    TranscriptionProvider,
    TranscriptionResult,
)

log = get_logger(__name__)


class DeepgramProvider(TranscriptionProvider):
    name = "deepgram"

    def __init__(self) -> None:
        if not settings.DEEPGRAM_API_KEY:
            raise TranscriptionError("DEEPGRAM_API_KEY is not configured.")
        try:
            from deepgram import DeepgramClient

            self._DeepgramClient = DeepgramClient
        except ImportError as exc:  # pragma: no cover
            raise TranscriptionError("deepgram-sdk is not installed.") from exc
        self.client = self._DeepgramClient(settings.DEEPGRAM_API_KEY)
        self.model = settings.DEEPGRAM_MODEL

    def transcribe(
        self, audio_path: Path, language: Optional[str] = None
    ) -> TranscriptionResult:
        from deepgram import PrerecordedOptions

        options = PrerecordedOptions(
            model=self.model,
            smart_format=True,
            punctuate=True,
            diarize=True,  # speaker labels when available
            language=language or settings.TRANSCRIPTION_LANGUAGE or None,
        )
        try:
            with audio_path.open("rb") as fh:
                payload = {"buffer": fh.read()}
            resp = self.client.listen.rest.v("1").transcribe_file(payload, options)
            result = resp.results.channels[0].alternatives[0]
            text = result.transcript

            segments = []
            for word in getattr(result, "words", None) or []:
                segments.append(
                    {
                        "start": getattr(word, "start", None),
                        "end": getattr(word, "end", None),
                        "speaker": getattr(word, "speaker", None),
                        "text": getattr(word, "punctuated_word", None)
                        or getattr(word, "word", ""),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            raise TranscriptionError(f"Deepgram failed: {exc}") from exc

        return TranscriptionResult(
            text=text,
            language=options.language,
            segments=segments,
            provider=self.name,
        )
