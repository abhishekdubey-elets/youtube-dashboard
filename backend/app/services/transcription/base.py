"""Transcription provider interface + shared result type."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


class TranscriptionError(Exception):
    """Raised when a transcription provider fails."""


@dataclass
class TranscriptionResult:
    text: str
    language: Optional[str] = None
    segments: list[dict[str, Any]] = field(default_factory=list)
    provider: str = ""

    @property
    def word_count(self) -> int:
        return len(self.text.split())


class TranscriptionProvider(ABC):
    """Common interface for every speech-to-text backend."""

    name: str = "base"

    @abstractmethod
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe an audio file into a ``TranscriptionResult``."""
        raise NotImplementedError
