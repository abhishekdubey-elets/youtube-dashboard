"""AI summarization service using OpenAI GPT-4.1 / GPT-5 models.

Produces a structured summary: executive summary, key discussion points,
important quotes, action items, keywords, tags, topics, key insights and
sentiment. Returns a plain dict ready to persist on the ``Summary`` model.
"""
from __future__ import annotations

import json
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


class SummarizationError(Exception):
    """Raised when summary generation fails."""


def is_available() -> bool:
    """True if AI summarization can run with the current configuration.

    * provider "ollama": a local LLM (no API key) — assumed available; if the
      Ollama server is down the call fails and the worker skips the summary.
    * provider "openai": requires OPENAI_API_KEY.

    The summary step is optional: with local Whisper transcription the pipeline
    completes end-to-end even when this returns False (the worker just skips it).
    """
    if settings.SUMMARIZATION_PROVIDER == "ollama":
        return True
    return bool(settings.OPENAI_API_KEY)


def _active_model() -> str:
    if settings.SUMMARIZATION_PROVIDER == "ollama":
        return settings.OLLAMA_MODEL
    return settings.OPENAI_SUMMARY_MODEL


SYSTEM_PROMPT = (
    "You are an expert media analyst for the elets YouTube channel. You read "
    "video transcripts and produce precise, structured editorial summaries. "
    "Always respond with strict JSON matching the requested schema. Never "
    "fabricate quotes — only use verbatim text present in the transcript."
)

# Truncate very long transcripts to stay within context limits (~ chars).
MAX_TRANSCRIPT_CHARS = 90_000

SCHEMA_HINT = {
    "executive_summary": "string — 2-4 sentence high-level overview",
    "key_points": ["string — main discussion points"],
    "key_insights": ["string — non-obvious takeaways"],
    "quotes": ["string — verbatim notable quotes"],
    "action_items": ["string — concrete next steps or recommendations"],
    "topics": ["string — high-level topics covered"],
    "keywords": ["string — 5-15 search keywords"],
    "tags": ["string — short categorization tags"],
    "sentiment": "one of: positive, neutral, negative, mixed",
    "sentiment_detail": {"label": "string", "rationale": "string"},
}


def _build_user_prompt(title: str, channel: str, transcript: str) -> str:
    transcript = transcript[:MAX_TRANSCRIPT_CHARS]
    return (
        f"Video title: {title}\n"
        f"Channel: {channel}\n\n"
        "Analyze the transcript below and return JSON with exactly these keys: "
        f"{json.dumps(list(SCHEMA_HINT.keys()))}.\n"
        f"Schema guidance: {json.dumps(SCHEMA_HINT)}\n\n"
        "TRANSCRIPT:\n"
        f"{transcript}"
    )


def _make_client():
    """Build an OpenAI-compatible client for the configured provider.

    Ollama exposes an OpenAI-compatible API, so the same client/code path
    serves both providers — only base_url, api_key and model differ.
    """
    from openai import OpenAI

    if settings.SUMMARIZATION_PROVIDER == "ollama":
        return OpenAI(base_url=settings.OLLAMA_BASE_URL, api_key="ollama")
    if not settings.OPENAI_API_KEY:
        raise SummarizationError("OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=settings.OPENAI_API_KEY)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20))
def _call_openai(title: str, channel: str, transcript: str) -> dict[str, Any]:
    client = _make_client()
    resp = client.chat.completions.create(
        model=_active_model(),
        temperature=settings.OPENAI_SUMMARY_TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(title, channel, transcript)},
        ],
    )
    content = resp.choices[0].message.content or "{}"
    return json.loads(content)


def generate_summary(title: str, channel: str, transcript: str) -> dict[str, Any]:
    """Generate a structured summary dict for the given transcript."""
    if not transcript.strip():
        raise SummarizationError("Cannot summarize an empty transcript.")

    try:
        data = _call_openai(title, channel or "", transcript)
    except SummarizationError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise SummarizationError(f"Summarization failed: {exc}") from exc

    # Normalize into the Summary model's field names.
    return {
        "summary": data.get("executive_summary", ""),
        "key_points": _as_list(data.get("key_points")),
        "key_insights": _as_list(data.get("key_insights")),
        "quotes": _as_list(data.get("quotes")),
        "action_items": _as_list(data.get("action_items")),
        "topics": _as_list(data.get("topics")),
        "keywords": _as_list(data.get("keywords")),
        "tags": _as_list(data.get("tags")),
        "sentiment": data.get("sentiment"),
        "sentiment_detail": data.get("sentiment_detail"),
        "model": _active_model(),
    }


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]
