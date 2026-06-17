"""Unit tests for YouTube URL parsing helpers."""
import pytest

from app.services import youtube


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/abc12345678", "abc12345678"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("not a url", None),
    ],
)
def test_extract_video_id(url, expected):
    assert youtube.extract_video_id(url) == expected


@pytest.mark.parametrize(
    "url,is_pl",
    [
        ("https://www.youtube.com/playlist?list=PLabc", True),
        ("https://www.youtube.com/watch?v=abc&list=PLxyz", False),
        ("https://youtu.be/abc", False),
    ],
)
def test_is_playlist_url(url, is_pl):
    assert youtube.is_playlist_url(url) is is_pl
