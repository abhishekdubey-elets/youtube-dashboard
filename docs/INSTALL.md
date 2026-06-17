# Installation & Setup Guide

This guide covers Docker and local (non-Docker) setup, transcription provider
selection, and Google Sheets configuration.

---

## 1. Prerequisites

- **Docker** + **Docker Compose** (recommended path), **or**
- For local dev: **Python 3.12**, **Node.js 20+**, **PostgreSQL 16**, **Redis 7**, and **ffmpeg** on your PATH.
- An **OpenAI API key** (for Whisper API + GPT summaries) — or a Deepgram key / local GPU.
- A **Google service account** JSON if you want Sheets export.

---

## 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

| Variable | Notes |
|----------|-------|
| `SECRET_KEY` | `openssl rand -hex 32` |
| `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` | dashboard login |
| `OPENAI_API_KEY` | required for default transcription + summaries |
| `TRANSCRIPTION_PROVIDER` | `openai_whisper` \| `local_whisper` \| `deepgram` |
| `OPENAI_SUMMARY_MODEL` | e.g. `gpt-4.1` or `gpt-5` |

The frontend reads `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000/api/v1`).

---

## 3. Run with Docker (recommended)

```bash
docker compose up --build
```

This starts: `postgres`, `redis`, `backend` (API, runs migrations on boot),
`worker` (Celery), `beat` (periodic cleanup), and `frontend`.

Optional monitoring (Flower):

```bash
docker compose --profile monitoring up
```

- Dashboard → http://localhost:3000
- API docs → http://localhost:8000/docs

---

## 4. Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Point DB/Redis URLs in .env at localhost, then:
alembic upgrade head
uvicorn app.main:app --reload
```

In separate terminals (same venv):

```bash
celery -A app.workers.celery_app.celery worker --loglevel=info
celery -A app.workers.celery_app.celery beat   --loglevel=info
```

> **ffmpeg** must be installed and on PATH (`ffmpeg -version`).

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL if not default
npm run dev
```

---

## 5. Choosing a transcription provider

| Provider | `TRANSCRIPTION_PROVIDER` | Requirements |
|----------|--------------------------|--------------|
| OpenAI Whisper API *(default)* | `openai_whisper` | `OPENAI_API_KEY` |
| Local Whisper Large‑V3 | `local_whisper` | `faster-whisper`; GPU strongly recommended (`LOCAL_WHISPER_DEVICE=cuda`) |
| Deepgram | `deepgram` | `DEEPGRAM_API_KEY` (adds speaker diarization) |

No code changes are needed — just set the env var and restart the workers.

---

## 6. Google Sheets export setup

1. In the [Google Cloud Console](https://console.cloud.google.com/), create a
   project and enable the **Google Sheets API** and **Google Drive API**.
2. Create a **Service Account** and download its **JSON key**.
3. Create (or pick) a Google Sheet. **Share** it with the service account's
   `client_email` (inside the JSON) as **Editor**.
4. Copy the spreadsheet ID from its URL:
   `https://docs.google.com/spreadsheets/d/`**`<SPREADSHEET_ID>`**`/edit`.
5. In the dashboard → **Google Sheets** page:
   - Upload the service-account JSON.
   - Enter the Spreadsheet ID and worksheet name.
   - Toggle **Auto Export** to append automatically on completion, or use
     **Export all completed now** for a manual push.

The header row and column order are managed automatically (see
[`services/google_sheets.py`](../backend/app/services/google_sheets.py)).

---

## 7. Common issues

| Symptom | Fix |
|---------|-----|
| `ffmpeg not found` | Install ffmpeg and ensure it's on PATH. |
| Age-restricted / members-only videos fail | Set `YTDLP_COOKIES_FILE` to an exported cookies.txt. |
| Sheets export 403 | Share the spreadsheet with the service-account email as Editor. |
| Workers idle | Confirm `CELERY_BROKER_URL`/`REDIS_URL` point at a reachable Redis. |
| Local Whisper OOM | Use a smaller model or set `LOCAL_WHISPER_COMPUTE_TYPE=int8`. |

---

## 8. Database migrations

```bash
cd backend
alembic upgrade head                       # apply
alembic revision --autogenerate -m "msg"   # create new
alembic downgrade -1                        # roll back one
```
