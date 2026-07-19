import logging
import secrets

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from app.auth.google_oauth import NeedsReauthError
from app.auth.router import router as auth_router
from app.config import settings
from app.db import engine

logger = logging.getLogger(__name__)

app = FastAPI(title="Analiza spotkań")

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
    same_site="lax",
    https_only=False,
)

app.include_router(auth_router)


@app.exception_handler(NeedsReauthError)
def needs_reauth_handler(request, exc: NeedsReauthError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc), "reauth_required": True})


@app.get("/health")
def health() -> dict[str, str]:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
