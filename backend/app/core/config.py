"""Application configuration loaded from environment variables.

Uses pydantic-settings so every value is typed, validated and documented in
one place. Import the singleton ``settings`` everywhere instead of reading
``os.environ`` directly.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

TranscriptionProvider = Literal["openai_whisper", "local_whisper", "deepgram"]

# Resolve .env locations absolutely so settings load no matter the working
# directory (repo root or backend/). config.py lives at backend/app/core/.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_ROOT_DIR = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Later files win; check backend/.env first, then the repo-root .env.
        env_file=(str(_BACKEND_DIR / ".env"), str(_ROOT_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- General -----------------------------------------------------------
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "elets Transcript Dashboard"
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    # --- Security ----------------------------------------------------------
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_ALGORITHM: str = "HS256"
    FIRST_ADMIN_EMAIL: str = "admin@elets.in"
    FIRST_ADMIN_PASSWORD: str = "ChangeMe123!"

    # --- Database ----------------------------------------------------------
    DATABASE_URL: str = (
        "postgresql+asyncpg://elets:elets_password@localhost:5432/elets_transcripts"
    )
    DATABASE_URL_SYNC: str = (
        "postgresql+psycopg2://elets:elets_password@localhost:5432/elets_transcripts"
    )

    # --- Redis / Celery ----------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # --- Storage -----------------------------------------------------------
    STORAGE_DIR: str = "/data/storage"
    DELETE_AUDIO_AFTER_PROCESSING: bool = True
    MAX_AUDIO_AGE_HOURS: int = 24

    # --- YouTube -----------------------------------------------------------
    YTDLP_COOKIES_FILE: str = ""
    YTDLP_MAX_PLAYLIST_ITEMS: int = 200

    # --- Transcription -----------------------------------------------------
    TRANSCRIPTION_PROVIDER: TranscriptionProvider = "openai_whisper"
    TRANSCRIPTION_LANGUAGE: str = ""

    OPENAI_API_KEY: str = ""
    OPENAI_WHISPER_MODEL: str = "whisper-1"
    OPENAI_SUMMARY_MODEL: str = "gpt-4.1"
    OPENAI_SUMMARY_TEMPERATURE: float = 0.2

    LOCAL_WHISPER_MODEL: str = "large-v3"
    LOCAL_WHISPER_DEVICE: str = "auto"
    LOCAL_WHISPER_COMPUTE_TYPE: str = "auto"

    DEEPGRAM_API_KEY: str = ""
    DEEPGRAM_MODEL: str = "nova-2"

    # --- Google Sheets -----------------------------------------------------
    GOOGLE_CREDENTIALS_FILE: str = "/data/secrets/google-credentials.json"
    GOOGLE_SHEET_ID: str = ""
    GOOGLE_WORKSHEET_NAME: str = "Transcripts"
    GOOGLE_SHEETS_AUTO_EXPORT: bool = False

    # --- Processing --------------------------------------------------------
    MAX_RETRIES: int = 3
    TASK_TIMEOUT_SECONDS: int = 3600

    @field_validator("BACKEND_CORS_ORIGINS")
    @classmethod
    def _strip_origins(cls, v: str) -> str:
        return v.strip()

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
