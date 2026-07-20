"""Upsert konta app_user i tokenów oauth_token po udanym OAuth callback."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.auth.google_oauth import GoogleIdentity, TokenSet
from app.models import app_user, oauth_token
from app.security.crypto import encrypt


def get_owner_id(db: Session) -> uuid.UUID | None:
    """Jedyny właściciel aplikacji (SPEC.md §0: jedna osoba) — None, jeśli nikt się jeszcze nie zalogował."""
    return db.execute(select(app_user.c.id).order_by(app_user.c.created_at).limit(1)).scalar_one_or_none()


def upsert_user(db: Session, identity: GoogleIdentity) -> uuid.UUID:
    stmt = pg_insert(app_user).values(
        google_sub=identity.sub,
        email=identity.email,
        display_name=identity.display_name,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[app_user.c.google_sub],
        set_={"email": stmt.excluded.email, "display_name": stmt.excluded.display_name},
    ).returning(app_user.c.id)
    return db.execute(stmt).scalar_one()


def store_tokens(db: Session, user_id: uuid.UUID, tokens: TokenSet) -> None:
    """Zapisuje zaszyfrowane tokeny. Nie commituje — wywołujący zarządza transakcją."""
    if tokens.refresh_token is None:
        # Google nie zwraca refresh_token, gdy zgoda już była udzielona bez
        # prompt=consent. My zawsze wysyłamy prompt=consent, więc to nie
        # powinno się zdarzyć — ale gdyby się zdarzyło, zachowaj istniejący.
        existing = db.execute(
            select(oauth_token.c.refresh_token_enc).where(oauth_token.c.user_id == user_id)
        ).scalar_one_or_none()
        if existing is None:
            raise RuntimeError(
                "Google nie zwrócił refresh_token, a w bazie nie ma wcześniejszego. "
                "Cofnij dostęp aplikacji na https://myaccount.google.com/permissions "
                "i zaloguj się ponownie."
            )
        refresh_token_enc = existing
    else:
        refresh_token_enc = encrypt(tokens.refresh_token)

    stmt = pg_insert(oauth_token).values(
        user_id=user_id,
        refresh_token_enc=refresh_token_enc,
        access_token_enc=encrypt(tokens.access_token),
        access_expires_at=tokens.access_expires_at,
        scopes=tokens.scopes,
        updated_at=datetime.now(timezone.utc),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[oauth_token.c.user_id],
        set_={
            "refresh_token_enc": stmt.excluded.refresh_token_enc,
            "access_token_enc": stmt.excluded.access_token_enc,
            "access_expires_at": stmt.excluded.access_expires_at,
            "scopes": stmt.excluded.scopes,
            "updated_at": stmt.excluded.updated_at,
        },
    )
    db.execute(stmt)
