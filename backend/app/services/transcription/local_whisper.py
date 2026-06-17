"""Local Whisper Large-V3 provider via faster-whisper (Option 2).

The model is loaded lazily and cached at module level so the worker only pays
the load cost once per process.
"""
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

_model_cache: dict[str, object] = {}


def _resolve_device() -> tuple[str, str]:
    device = settings.LOCAL_WHISPER_DEVICE
    compute = settings.LOCAL_WHISPER_COMPUTE_TYPE
    if device == "auto":
        try:
            import torch  # type: ignore

            device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"
    if compute == "auto":
        compute = "float16" if device == "cuda" else "int8"
    return device, compute


class LocalWhisperProvider(TranscriptionProvider):
    name = "local_whisper"

    def __init__(self) -> None:
        self.model_size = settings.LOCAL_WHISPER_MODEL
        self._model = self._get_model()

    def _get_model(self):
        if self.model_size in _model_cache:
            return _model_cache[self.model_size]
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover
            raise TranscriptionError(
                "faster-whisper is not installed for local transcription."
            ) from exc
        device, compute = _resolve_device()
        log.info("loading_local_whisper", model=self.model_size, device=device)
        model = WhisperModel(self.model_size, device=device, compute_type=compute)
        _model_cache[self.model_size] = model
        return model

    def transcribe(
        self, audio_path: Path, language: Optional[str] = None
    ) -> TranscriptionResult:
        lang = language or settings.TRANSCRIPTION_LANGUAGE or None
        try:
            segments_iter, info = self._model.transcribe(
                str(audio_path), language=lang, vad_filter=True
            )
            segments = []
            parts: list[str] = []
            for seg in segments_iter:
                parts.append(seg.text)
                segments.append(
                    {"start": seg.start, "end": seg.end, "text": seg.text}
                )
        except Exception as exc:  # noqa: BLE001
            raise TranscriptionError(f"Local Whisper failed: {exc}") from exc

        return TranscriptionResult(
            text="".join(parts).strip(),
            language=getattr(info, "language", lang),
            segments=segments,
            provider=self.name,
        )
