"""Local Whisper provider via faster-whisper (Option 2).

Optimized for throughput on CPU:
* ``BatchedInferencePipeline`` transcribes VAD-segmented chunks in parallel
  batches (typically 2-4x faster than sequential decoding).
* Greedy decoding (``beam_size=1``) and all CPU cores by default.

The model + pipeline are loaded lazily and cached at module level so the worker
only pays the load cost once per process.
"""
from __future__ import annotations

import os
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

# Cache keyed by model size so repeated tasks reuse the loaded weights.
_cache: dict[str, dict[str, object]] = {}


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
        self.batch_size = max(1, settings.LOCAL_WHISPER_BATCH_SIZE)
        self.beam_size = max(1, settings.LOCAL_WHISPER_BEAM_SIZE)
        bundle = self._get_bundle()
        self._model = bundle["model"]
        self._batched = bundle.get("batched")  # may be None on older versions

    def _get_bundle(self) -> dict[str, object]:
        if self.model_size in _cache:
            return _cache[self.model_size]
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover
            raise TranscriptionError(
                "faster-whisper is not installed for local transcription."
            ) from exc

        device, compute = _resolve_device()
        cpu_threads = settings.LOCAL_WHISPER_CPU_THREADS or (os.cpu_count() or 4)
        log.info(
            "loading_local_whisper",
            model=self.model_size,
            device=device,
            compute=compute,
            cpu_threads=cpu_threads,
            batch_size=self.batch_size,
        )
        model = WhisperModel(
            self.model_size,
            device=device,
            compute_type=compute,
            cpu_threads=cpu_threads,
        )

        batched: object | None = None
        if self.batch_size > 1:
            try:
                from faster_whisper import BatchedInferencePipeline

                batched = BatchedInferencePipeline(model=model)
            except Exception as exc:  # pragma: no cover - older faster-whisper
                log.warning("batched_pipeline_unavailable", error=str(exc))

        bundle = {"model": model, "batched": batched}
        _cache[self.model_size] = bundle
        return bundle

    def transcribe(
        self, audio_path: Path, language: Optional[str] = None
    ) -> TranscriptionResult:
        lang = language or settings.TRANSCRIPTION_LANGUAGE or None
        try:
            if self._batched is not None:
                segments_iter, info = self._batched.transcribe(  # type: ignore[attr-defined]
                    str(audio_path),
                    language=lang,
                    batch_size=self.batch_size,
                    beam_size=self.beam_size,
                    vad_filter=True,
                )
            else:
                segments_iter, info = self._model.transcribe(  # type: ignore[attr-defined]
                    str(audio_path),
                    language=lang,
                    beam_size=self.beam_size,
                    vad_filter=True,
                    condition_on_previous_text=False,
                )
            segments = []
            parts: list[str] = []
            for seg in segments_iter:
                parts.append(seg.text)
                segments.append({"start": seg.start, "end": seg.end, "text": seg.text})
        except Exception as exc:  # noqa: BLE001
            raise TranscriptionError(f"Local Whisper failed: {exc}") from exc

        return TranscriptionResult(
            text="".join(parts).strip(),
            language=getattr(info, "language", lang),
            segments=segments,
            provider=self.name,
        )
