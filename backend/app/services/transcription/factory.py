"""Factory that resolves the configured transcription provider.

Switching providers is a single env var (``TRANSCRIPTION_PROVIDER``); add a new
backend by subclassing ``TranscriptionProvider`` and registering it here.
"""
from __future__ import annotations

from typing import Optional

from app.core.config import settings
from app.services.transcription.base import TranscriptionError, TranscriptionProvider


def get_transcriber(provider: Optional[str] = None) -> TranscriptionProvider:
    name = (provider or settings.TRANSCRIPTION_PROVIDER).lower()

    if name == "openai_whisper":
        from app.services.transcription.openai_whisper import OpenAIWhisperProvider

        return OpenAIWhisperProvider()
    if name == "local_whisper":
        from app.services.transcription.local_whisper import LocalWhisperProvider

        return LocalWhisperProvider()
    if name == "deepgram":
        from app.services.transcription.deepgram import DeepgramProvider

        return DeepgramProvider()

    raise TranscriptionError(f"Unknown transcription provider: {name}")
