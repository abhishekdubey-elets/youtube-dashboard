"""Standalone DB/environment diagnostic for the transcript backend.

Run from the backend/ directory:

    python scripts/check_db.py

It prints which Python is in use, whether required packages import, the
resolved database URL, and the precise result of a real connection attempt.
Paste the full output when reporting an `alembic upgrade head` failure.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `app` importable when run as `python scripts/check_db.py`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

print("=" * 60)
print("Python   :", sys.executable)
print("Version  :", sys.version.split()[0])
print("=" * 60)

# 1) Required packages
for mod in ("alembic", "sqlalchemy", "psycopg2", "pydantic", "pydantic_settings"):
    try:
        m = __import__(mod)
        print(f"[ok]   import {mod:<16} {getattr(m, '__version__', '')}")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] import {mod:<16} -> {exc}")

print("-" * 60)

# 2) Settings + resolved URL
try:
    from app.core.config import settings

    url = settings.DATABASE_URL_SYNC
    print("[ok]   settings loaded")
    print("       DATABASE_URL_SYNC =", url)
except Exception as exc:  # noqa: BLE001
    print("[FAIL] could not load settings:", repr(exc))
    raise SystemExit(1)

print("-" * 60)

# 3) Real connection attempt
try:
    from sqlalchemy import create_engine, text

    engine = create_engine(url)
    with engine.connect() as conn:
        ver = conn.execute(text("SELECT version()")).scalar()
    print("[ok]   CONNECTED to PostgreSQL")
    print("       ", ver)
except Exception as exc:  # noqa: BLE001
    print("[FAIL] could not connect to the database:")
    print("       ", type(exc).__name__, "->", exc)
    print()
    print("Most likely cause based on the message above:")
    msg = str(exc).lower()
    if "translate host name" in msg or "name or service not known" in msg:
        print("  * URL still points at a Docker hostname. Use localhost in .env.")
    elif "refused" in msg or "could not connect" in msg or "timeout" in msg:
        print("  * No PostgreSQL is listening on that host:port. Start Postgres.")
    elif "authentication failed" in msg or "password" in msg:
        print("  * Wrong username/password. Match .env to your DB role.")
    elif "does not exist" in msg:
        print("  * The database or role does not exist yet. Create them.")
    else:
        print("  * See the message above.")
    raise SystemExit(1)

print("=" * 60)
print("Environment looks good. `alembic upgrade head` should now work.")
