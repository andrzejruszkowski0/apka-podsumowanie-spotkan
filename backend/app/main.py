import logging
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from app.auth.accounts import get_owner_id
from app.auth.google_oauth import NeedsReauthError
from app.auth.router import router as auth_router
from app.briefing.router import router as briefing_router
from app.config import settings
from app.db import SessionLocal, engine
from app.decisions.router import router as decisions_router
from app.meetings.router import router as meetings_router
from app.notifications.reminders import catch_up_if_needed, run_daily_reminders
from app.people.router import router as people_router
from app.people.sync import sync_people_on_startup
from app.security.csrf import CsrfMiddleware
from app.tasks.router import router as tasks_router
from app.topics import router as topics_router

# Bez tego komunikaty logger.info(...) (np. catch-up schedulera, SPEC.md §7)
# są domyślnie wyciszane — Python bez konfiguracji pokazuje tylko WARNING+.
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone=settings.timezone)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db = SessionLocal()
    try:
        sync_people_on_startup(db, get_owner_id(db))
    finally:
        db.close()

    if settings.scheduler_enabled:
        # Nadrabia dzisiejszy przebieg, jeśli backend był wyłączony o REMINDER_HOUR
        # (hosting lokalny — SPEC.md §7).
        catch_up_if_needed()
        scheduler.add_job(
            run_daily_reminders,
            trigger="cron",
            hour=settings.reminder_hour,
            minute=0,
            id="daily_reminders",
            replace_existing=True,
        )
        scheduler.start()

    yield

    if settings.scheduler_enabled and scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Analiza spotkań", lifespan=lifespan)

# Kolejność ma znaczenie: add_middleware dokłada na zewnątrz, więc dodany jako
# pierwszy CsrfMiddleware jest najbardziej wewnętrzny. Dzięki temu preflight
# OPTIONS obsługuje CORS przed nim, a sesja (SessionMiddleware, dodany na
# końcu) jest już wczytana, gdy sprawdzamy token.
app.add_middleware(CsrfMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_session_secret = settings.session_secret
if not _session_secret:
    logger.warning(
        "SESSION_SECRET nie jest ustawiony w .env — używam tymczasowego klucza. "
        "Sesje (zalogowanie) nie przetrwają restartu backendu, dopóki nie ustawisz stałej wartości."
    )
    _session_secret = secrets.token_urlsafe(32)

app.add_middleware(
    SessionMiddleware,
    secret_key=_session_secret,
    session_cookie="session",
    same_site="none" if settings.session_cookie_secure else "lax",
    https_only=settings.session_cookie_secure,
)

app.include_router(auth_router)
app.include_router(people_router)
app.include_router(topics_router)
app.include_router(meetings_router)
app.include_router(tasks_router)
app.include_router(decisions_router)
app.include_router(briefing_router)


@app.exception_handler(NeedsReauthError)
def needs_reauth_handler(request, exc: NeedsReauthError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc), "reauth_required": True})


@app.get("/health")
def health() -> dict[str, str]:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "deploy_check": "cicd-pipeline-test-2026-08-01"}
