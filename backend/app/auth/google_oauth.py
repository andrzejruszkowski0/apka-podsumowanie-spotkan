"""Klient OAuth Google: URL logowania, wymiana kodu, odświeżanie access tokena.

Jeden flow obsługuje logowanie (openid/email/profile) i uprawnienia do Gmaila
(gmail.send) — patrz SPEC.md §3. Sheets nie jest tu już objęty: czytany/
zapisywany jest przez osobne konto serwisowe, patrz app.auth.service_account.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.config import settings

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.send",
]

TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"


class GoogleOAuthNotConfigured(RuntimeError):
    pass


class NeedsReauthError(RuntimeError):
    """Refresh token nie działa — użytkownik musi przejść /auth/login ponownie."""


@dataclass
class GoogleIdentity:
    sub: str
    email: str
    display_name: str | None


@dataclass
class TokenSet:
    access_token: str
    refresh_token: str | None
    access_expires_at: datetime
    scopes: list[str]


def _require_config() -> tuple[str, str, str]:
    if not (settings.google_client_id and settings.google_client_secret and settings.google_redirect_uri):
        raise GoogleOAuthNotConfigured(
            "GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REDIRECT_URI nie są ustawione w .env."
        )
    return settings.google_client_id, settings.google_client_secret, settings.google_redirect_uri


def _client_config() -> dict:
    client_id, client_secret, redirect_uri = _require_config()
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": AUTH_URI,
            "token_uri": TOKEN_URI,
            "redirect_uris": [redirect_uri],
        }
    }


def _as_aware_utc(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc) + timedelta(hours=1)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def build_authorization_url(state: str) -> str:
    """access_type=offline + prompt=consent: zawsze wymuś refresh_token."""
    _, _, redirect_uri = _require_config()
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES, redirect_uri=redirect_uri)
    url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
        state=state,
    )
    return url


def exchange_code(code: str) -> tuple[TokenSet, GoogleIdentity]:
    client_id, _, redirect_uri = _require_config()
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES, redirect_uri=redirect_uri)
    flow.fetch_token(code=code)
    creds = flow.credentials

    if not creds.id_token:
        raise GoogleOAuthNotConfigured("Google nie zwrócił id_token (brak scope openid?).")

    # Weryfikacja podpisu i audience id_tokena — nie ufamy claimom bez tego.
    claims = google_id_token.verify_oauth2_token(creds.id_token, GoogleAuthRequest(), client_id)

    identity = GoogleIdentity(
        sub=claims["sub"],
        email=claims["email"],
        display_name=claims.get("name"),
    )
    tokens = TokenSet(
        access_token=creds.token,
        refresh_token=creds.refresh_token,
        access_expires_at=_as_aware_utc(creds.expiry),
        scopes=list(creds.scopes or SCOPES),
    )
    return tokens, identity


def refresh_access_token(refresh_token: str, scopes: list[str]) -> TokenSet:
    client_id, client_secret, _ = _require_config()
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )
    try:
        creds.refresh(GoogleAuthRequest())
    except RefreshError as exc:
        raise NeedsReauthError(
            "Odświeżenie tokena Google nie powiodło się — konieczna ponowna zgoda (/auth/login)."
        ) from exc

    return TokenSet(
        access_token=creds.token,
        refresh_token=refresh_token,
        access_expires_at=_as_aware_utc(creds.expiry),
        scopes=scopes,
    )
