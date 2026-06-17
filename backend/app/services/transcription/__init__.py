"""Pluggable transcription providers."""
from app.services.transcription.base import (
    TranscriptionError,
    TranscriptionResult,
    TranscriptionProvider,
)
from app.services.transcription.factory import get_transcriber

__all__ = [
    "TranscriptionError",
    "TranscriptionResult",
    "TranscriptionProvider",
    "get_transcriber",
]
