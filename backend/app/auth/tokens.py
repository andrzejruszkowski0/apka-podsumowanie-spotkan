"""Serwis dostarczania ważnego access tokena Google — auto-refresh w razie potrzeby.

Do użytku przez przyszłe wywołania Gmail/Sheets API (poza zakresem etapu 2).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth.google_oauth import NeedsReauthError, TokenSet, refresh_access_token
from app.models import oauth_token
from app.security.crypto import decrypt, encrypt

# Odśwież nieco przed faktycznym wygaśnięciem, żeby uniknąć wyścigu z Google.
_EXPIRY_SAFETY_MARGIN = timedelta(seconds=60)


def get_valid_access_token(db: Session, user_id: uuid.UUID) -> str:
    row = db.execute(
        select(
            oauth_token.c.access_token_enc,
            oauth_token.c.access_expires_at,
            oauth_token.c.refresh_token_enc,
            oauth_token.c.scopes,
        ).where(oauth_token.c.user_id == user_id)
    ).mappings().first()

    if row is None:
        raise NeedsReauthError("Brak zapisanych tokenów Google — wymagane logowanie (/auth/login).")

    now = datetime.now(timezone.utc)
    expires_at = row["access_expires_at"]
    if row["access_token_enc"] and expires_at and expires_at > now + _EXPIRY_SAFETY_MARGIN:
        return decrypt(row["access_token_enc"])

    refresh_token = decrypt(row["refresh_token_enc"])
    tokens = refresh_access_token(refresh_token, list(row["scopes"]))
    _store_refreshed(db, user_id, tokens)
    return tokens.access_token


def _store_refreshed(db: Session, user_id: uuid.UUID, tokens: TokenSet) -> None:
    db.execute(
        update(oauth_token)
        .where(oauth_token.c.user_id == user_id)
        .values(
            access_token_enc=encrypt(tokens.access_token),
            access_expires_at=tokens.access_expires_at,
            updated_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
