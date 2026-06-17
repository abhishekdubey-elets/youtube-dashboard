"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.routes import auth, exports, stats, summaries, transcripts, videos
from app.bootstrap import ensure_first_admin
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("starting_up", env=settings.ENVIRONMENT, version=__version__)
    await ensure_first_admin()
    yield
    log.info("shutting_down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=__version__,
    description=(
        "Automated YouTube → transcript → AI summary → Google Sheets pipeline "
        "for the elets YouTube channel."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.exception("unhandled_exception", path=request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": __version__}


# Mount v1 API
api = settings.API_V1_PREFIX
for module in (auth, videos, transcripts, summaries, exports, stats):
    app.include_router(module.router, prefix=api)
