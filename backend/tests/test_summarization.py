"""Unit tests for the summarization normalization layer (no network)."""
import pytest

from app.services import summarization


def test_as_list_normalizes_scalar_and_none():
    assert summarization._as_list(None) == []
    assert summarization._as_list("a") == ["a"]
    assert summarization._as_list(["a", "b"]) == ["a", "b"]
    assert summarization._as_list([1, 2]) == ["1", "2"]


def test_generate_summary_maps_fields(monkeypatch):
    fake = {
        "executive_summary": "An overview.",
        "key_points": ["p1", "p2"],
        "key_insights": ["i1"],
        "quotes": ["q1"],
        "action_items": ["do x"],
        "topics": ["t1"],
        "keywords": ["k1", "k2"],
        "tags": ["tag1"],
        "sentiment": "positive",
        "sentiment_detail": {"label": "positive", "rationale": "upbeat"},
    }
    monkeypatch.setattr(summarization, "_call_openai", lambda *a, **k: fake)

    out = summarization.generate_summary("Title", "Channel", "some transcript text")
    assert out["summary"] == "An overview."
    assert out["key_points"] == ["p1", "p2"]
    assert out["quotes"] == ["q1"]
    assert out["sentiment"] == "positive"
    assert "model" in out


def test_generate_summary_rejects_empty_transcript():
    with pytest.raises(summarization.SummarizationError):
        summarization.generate_summary("t", "c", "   ")
