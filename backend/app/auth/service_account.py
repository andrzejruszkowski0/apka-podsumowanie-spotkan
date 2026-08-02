"""Token dostępu Google Sheets przez Service Account — niezależny od logowania usera.

Sheets (w odróżnieniu od Gmaila) nie musi być czytany/zapisywany jako
konkretny człowiek — service account, któremu udostępniono arkusze jak
zwykłemu kontu Google, omija status weryfikacji ekranu zgody OAuth
(Testing/Production) i 7-dniowe wygasanie refresh tokena test usera
(patrz notatka pamięci google-account-external-testing).
"""

from __future__ import annotations

import json

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account

from app.config import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class ServiceAccountNotConfigured(RuntimeError):
    pass


_credentials: service_account.Credentials | None = None


def _load_credentials() -> service_account.Credentials:
    global _credentials
    if _credentials is None:
        if not settings.google_service_account_json:
            raise ServiceAccountNotConfigured(
                "GOOGLE_SERVICE_ACCOUNT_JSON nie jest ustawione w .env."
            )
        info = json.loads(settings.google_service_account_json)
        _credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return _credentials


def get_service_account_access_token() -> str:
    creds = _load_credentials()
    if not creds.valid:
        creds.refresh(GoogleAuthRequest())
    return creds.token
