# elets YouTube Transcript Automation Dashboard

A production-grade web application that turns YouTube videos (single or whole
playlists) into accurate transcripts and structured AI summaries, stores
everything in PostgreSQL, and exports each record to Google Sheets — fully
automated after a single URL submission.

Built for the **elets YouTube channel**.

```
URL ▶ validate ▶ fetch metadata ▶ download audio ▶ extract/normalize
    ▶ transcribe ▶ AI summary ▶ store (Postgres) ▶ export (Sheets) ▶ cleanup
```

---

## ✨ Features

- **Submit** a single video URL or an entire playlist; metadata is fetched automatically.
- **Background pipeline** on Celery + Redis — the API never blocks on long jobs.
- **Pluggable transcription**: OpenAI Whisper API (default), local Whisper Large‑V3 (faster‑whisper), or Deepgram — switch with one env var.
- **AI summaries** via OpenAI GPT‑4.1 / GPT‑5: executive summary, key points, quotes, action items, keywords, tags, topics, sentiment.
- **Google Sheets export** (manual or automatic) with a fixed column schema.
- **Live dashboard**: stat cards, daily/monthly charts, success-rate donut, recent activity.
- **Processing queue** with animated, per-stage progress and retry/cancel.
- **Transcript viewer** (embedded player, search, copy, download, speaker timestamps) and **AI summary** views.
- **Database explorer**: search, filter, sort, paginate, edit summary, reprocess, delete.
- **JWT auth** with a bootstrap admin; role model ready for multiple users.
- **Dark/light mode**, responsive SaaS UI, toasts, skeletons.
- **Docker Compose** one-command stack, Alembic migrations, structured logging, retries (×3), unit tests.

---

## 🧱 Tech Stack

| Layer        | Technology |
|--------------|------------|
| Frontend     | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, shadcn-style UI, React Query, Recharts |
| Backend      | FastAPI, SQLAlchemy 2 (async), Pydantic v2 |
| Workers      | Celery, Redis |
| Database     | PostgreSQL 16 |
| Speech‑to‑Text | OpenAI Whisper API · faster‑whisper (local) · Deepgram |
| Summaries    | OpenAI GPT‑4.1 / GPT‑5 |
| Export       | Google Sheets API (gspread + service account) |
| Media        | yt‑dlp + ffmpeg |

---

## 📁 Project Structure

```
exhibitor/
├── docker-compose.yml          # full stack: db, redis, api, worker, beat, flower, web
├── .env.example                # copy to .env
├── README.md
├── docs/
│   ├── INSTALL.md              # detailed setup + Google Sheets guide
│   └── API.md                  # REST API reference
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/                # migrations
│   ├── tests/                  # pytest unit tests
│   └── app/
│       ├── main.py             # FastAPI entrypoint
│       ├── bootstrap.py        # first-admin creation
│       ├── core/               # config, db, security, logging
│       ├── models/             # SQLAlchemy models
│       ├── schemas/            # Pydantic schemas
│       ├── api/routes/         # auth, videos, transcripts, summaries, exports, stats
│       ├── services/           # youtube, transcription/*, summarization, google_sheets, storage
│       └── workers/            # celery_app, tasks (the pipeline)
└── frontend/
    ├── Dockerfile
    ├── app/                    # App Router pages (dashboard group + login)
    ├── components/             # ui primitives + layout + status badge
    └── lib/                    # api client, react-query hooks, types, utils
```

---

## 🚀 Quick Start (Docker)

```bash
git clone <repo> exhibitor && cd exhibitor
cp .env.example .env
# edit .env — set SECRET_KEY, OPENAI_API_KEY, admin creds, etc.

docker compose up --build
```

Then open:

| Service        | URL |
|----------------|-----|
| Dashboard      | http://localhost:3000 |
| API + Swagger  | http://localhost:8000/docs |
| Flower (opt.)  | http://localhost:5555 (`docker compose --profile monitoring up`) |

Log in with `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` from your `.env`.

Migrations run automatically on backend startup (`alembic upgrade head`).

See **[docs/INSTALL.md](docs/INSTALL.md)** for local (non-Docker) setup, choosing a
transcription provider, and configuring Google Sheets.

---

## 🔌 REST API (v1)

Base path: `/api/v1`. All endpoints except `/auth/login` require
`Authorization: Bearer <token>`.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | Obtain JWT |
| POST | `/videos/process-video` | Queue a single video |
| POST | `/videos/process-playlist` | Queue an entire playlist |
| POST | `/videos/validate` | Validate + preview a URL |
| GET  | `/videos` | List (search/filter/sort/paginate) |
| GET  | `/videos/{id}` | Detail (transcript + summary + exports) |
| POST | `/videos/{id}/retry` | Retry a failed video |
| POST | `/videos/{id}/reprocess` | Re-run the whole pipeline |
| POST | `/videos/{id}/cancel` | Cancel an in-flight video |
| DELETE | `/videos/{id}` | Delete a video + children |
| GET  | `/transcripts/{video_id}` | Transcript |
| GET  | `/summaries/{video_id}` | Summary |
| PATCH | `/summaries/{video_id}` | Edit summary |
| GET/PUT | `/exports/config` | Sheets config |
| POST | `/exports/credentials` | Upload service-account JSON |
| POST | `/exports/google-sheet` | Manual export |
| GET  | `/exports` | Export history |
| GET  | `/stats` | Dashboard metrics |

Full reference: **[docs/API.md](docs/API.md)**.

---

## 🗄️ Data Model

`videos` ─┬─< `transcripts` (1:1)
          ├─< `summaries`   (1:1)
          └─< `exports`     (1:N)
`users`   (auth)

See [backend/app/models](backend/app/models) and the initial migration in
[backend/alembic/versions](backend/alembic/versions).

---

## 🔁 Transcription Providers

Set `TRANSCRIPTION_PROVIDER` in `.env`:

- `openai_whisper` *(default)* — needs `OPENAI_API_KEY`.
- `local_whisper` — runs Whisper Large‑V3 locally via faster‑whisper (GPU recommended).
- `deepgram` — needs `DEEPGRAM_API_KEY` (includes speaker diarization).

Add a new provider by subclassing `TranscriptionProvider` and registering it in
[`services/transcription/factory.py`](backend/app/services/transcription/factory.py).

---

## 🧪 Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

---

## 🧭 Future-ready Architecture

The service/worker separation makes future AI modules drop-in: speaker ID,
topic classification, blog/LinkedIn/tweet generation, PDF/Word export, meeting
minutes, translation, and a RAG "chat with transcript" layer (vector DB +
semantic search) can be added as new services + Celery tasks without touching
the core pipeline.

---

## 📝 License

Internal project for the elets YouTube channel.
