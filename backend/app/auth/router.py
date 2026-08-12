"""Endpointy /auth/*: logowanie Google, callback, sesja, wylogowanie."""

from __future__ import annotations

import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.accounts import create_demo_user, store_tokens, upsert_user
from app.auth.dependencies import CurrentUser, require_user
from app.auth.google_oauth import (
    GoogleOAuthNotConfigured,
    NeedsReauthError,
    build_authorization_url,
    exchange_code,
)
from app.auth.tokens import get_valid_access_token
from app.config import settings
from app.db import get_db
from app.models import oauth_token
from app.security.csrf import get_or_create_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/csrf")
def csrf(request: Request) -> dict[str, str]:
    """Token CSRF dla frontendu. Zakłada sesję, jeśli jej jeszcze nie ma —
    inaczej pierwszy POST (np. /auth/demo-login) nie miałby czego odesłać."""
    return {"csrf_token": get_or_create_token(request)}


@router.get("/login")
def login(request: Request) -> RedirectResponse:
    try:
        state = secrets.token_urlsafe(24)
        url = build_authorization_url(state)
    except GoogleOAuthNotConfigured as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    request.session["oauth_state"] = state
    return RedirectResponse(url)


@router.get("/callback")
def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if error:
        raise HTTPException(status_code=400, detail=f"Google zwrócił błąd: {error}")

    expected_state = request.session.pop("oauth_state", None)
    if not state or not expected_state or not secrets.compare_digest(state, expected_state):
        raise HTTPException(status_code=400, detail="Nieprawidłowy stan OAuth (state mismatch).")
    if not code:
        raise HTTPException(status_code=400, detail="Brak kodu autoryzacyjnego od Google.")

    try:
        tokens, identity = exchange_code(code)
    except GoogleOAuthNotConfigured as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    user_id = upsert_user(db, identity)
    try:
        store_tokens(db, user_id, tokens)
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()

    request.session["user_id"] = str(user_id)
    return RedirectResponse(settings.frontend_origin)


@router.post("/demo-login")
def demo_login(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    """Sesja demo bez Google OAuth (patrz komentarz w accounts.create_demo_user).

    Idempotentne: jeśli sesja już ma zalogowanego użytkownika (demo albo
    prawdziwego, np. przez podwójne kliknięcie), nic nie tworzy ponownie.
    """
    if not request.session.get("user_id"):
        user_id = create_demo_user(db)
        db.commit()
        request.session["user_id"] = str(user_id)
    return {"status": "ok"}


@router.post("/logout")
def logout(request: Request) -> dict[str, str]:
    request.session.clear()
    # Świeży token po wyczyszczeniu sesji: front trzyma stary w pamięci, a bez
    # tego jego następny POST (np. ponowne demo-login) dostałby 403. Nowa
    # wartość zamiast przeniesienia starej — token sprzed wylogowania nie
    # powinien zostawać ważny.
    return {"status": "ok", "csrf_token": get_or_create_token(request)}


@router.get("/me")
def me(user: CurrentUser = Depends(require_user), db: Session = Depends(get_db)) -> dict:
    token_row = db.execute(select(oauth_token.c.user_id).where(oauth_token.c.user_id == user.id)).first()

    google_connected = False
    reauth_required = False
    access_expires_at: str | None = None

    if token_row is not None:
        try:
            get_valid_access_token(db, user.id)
            google_connected = True
        except NeedsReauthError as exc:
            logger.warning("Odświeżenie tokena nie powiodło się dla %s: %s", user.id, exc)
            reauth_required = True

        expiry = db.execute(
            select(oauth_token.c.access_expires_at).where(oauth_token.c.user_id == user.id)
        ).scalar_one_or_none()
        access_expires_at = expiry.isoformat() if expiry else None

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "google_connected": google_connected,
        "reauth_required": reauth_required,
        "access_token_expires_at": access_expires_at,
    }
