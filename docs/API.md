# REST API Reference (v1)

Base URL: `http://localhost:8000/api/v1`
Interactive docs (Swagger UI): `http://localhost:8000/docs` · ReDoc: `/redoc`

All endpoints except `POST /auth/login` require a bearer token:

```
Authorization: Bearer <access_token>
```

---

## Auth

### `POST /auth/login`
```json
{ "email": "admin@elets.in", "password": "ChangeMe123!" }
```
**200**
```json
{ "access_token": "eyJ…", "token_type": "bearer" }
```

### `GET /auth/me`
Returns the current user `{ id, email, full_name, role, is_active }`.

---

## Videos

### `POST /videos/validate`
```json
{ "url": "https://www.youtube.com/watch?v=…" }
```
**200**
```json
{
  "valid": true,
  "type": "video",
  "youtube_id": "dQw4w9WgXcQ",
  "title": "…",
  "channel_name": "…",
  "thumbnail": "…",
  "duration": 212
}
```
For a playlist URL, `type` is `"playlist"` and `item_count` is returned.
Invalid URLs return `{ "valid": false, "message": "…" }`.

### `POST /videos/process-video`
Body `{ "url": "…" }` → **201** `Video`. Creates (or reuses) the video and
enqueues the pipeline.

### `POST /videos/process-playlist`
Body `{ "url": "…" }` → **201**
```json
{ "queued": 12, "videos": [ { …Video } ] }
```

### `GET /videos`
Query params: `status`, `search`, `page` (default 1), `page_size` (default 20,
max 100), `sort` (e.g. `-created_at`, `video_title`).
**200**
```json
{ "items": [ {…Video} ], "total": 42, "page": 1, "page_size": 20 }
```

### `GET /videos/{id}`
**200** `Video` with nested `transcript`, `summary`, `exports`.

### `POST /videos/{id}/retry` · `POST /videos/{id}/reprocess`
Re-queue a failed/cancelled video (`reprocess` also resets retry count). → `Video`.

### `POST /videos/{id}/cancel`
Marks an in-flight video cancelled. → `Video`.

### `DELETE /videos/{id}`
**204**. Cascades to transcript, summary and export rows.

---

## Transcripts & Summaries

### `GET /transcripts/{video_id}`
```json
{
  "id": 1, "video_id": 1,
  "full_transcript": "…",
  "language": "en", "word_count": 1820,
  "processing_time": 41.2, "provider": "openai_whisper",
  "segments": [ { "start": 0.0, "end": 4.1, "speaker": 0, "text": "…" } ],
  "created_at": "…"
}
```

### `GET /summaries/{video_id}`
```json
{
  "id": 1, "video_id": 1,
  "summary": "Executive overview…",
  "key_points": ["…"], "key_insights": ["…"],
  "quotes": ["…"], "action_items": ["…"],
  "topics": ["…"], "keywords": ["…"], "tags": ["…"],
  "sentiment": "positive",
  "sentiment_detail": { "label": "positive", "rationale": "…" },
  "model": "gpt-4.1"
}
```

### `PATCH /summaries/{video_id}`
Partial update — send any subset of summary fields. → updated `Summary`.

---

## Exports (Google Sheets)

### `GET /exports/config` · `PUT /exports/config`
```json
{ "spreadsheet_id": "1AbC…", "worksheet_name": "Transcripts", "auto_export": false, "credentials_uploaded": true }
```

### `POST /exports/credentials`
`multipart/form-data` with a `file` field — the service-account JSON.

### `POST /exports/google-sheet`
```json
{ "video_ids": [1, 2, 3] }   // optional; omit to export all completed
```
**200** `{ "exported": 3, "failed": 0, "errors": [] }`

### `GET /exports`
Query `page`, `page_size`. Returns paginated export history.

**Sheet columns (fixed order):** Video URL · Video ID · Video Title · Channel
Name · Playlist Name · Upload Date · Duration · Transcript · Summary · Keywords
· Sentiment · Processing Time · Processed Date · Status.

---

## Stats

### `GET /stats`
```json
{
  "total_videos": 42, "completed": 30, "in_progress": 8, "failed": 4,
  "avg_transcript_length": 1640.5, "avg_processing_time": 38.7,
  "success_rate": 71.4,
  "daily":  [ { "date": "2026-06-10", "count": 5 } ],
  "monthly":[ { "date": "2026-06",   "count": 40 } ],
  "recent_videos": [ {…Video} ]
}
```

---

## Status values

`Video.status` ∈ `queued · downloading · extracting · transcribing ·
summarizing · exporting · completed · failed · cancelled`.

## Error format

Errors use FastAPI's shape:
```json
{ "detail": "Human-readable message" }
```
Validation errors return `422` with a `detail` array.
