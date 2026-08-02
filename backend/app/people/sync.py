"""Sync tabeli person z arkuszem Google „Osoby" (SPEC.md §5).

Kolumny arkusza: A Imię i nazwisko | B Email | C Aliasy (przecinkami) |
D Firma | E Aktywny. Upsert po email. Osoby nieobecne w arkuszu ->
active=false — NIE usuwane (mogą być przypisane do historycznych zadań).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.auth.service_account import ServiceAccountNotConfigured, get_service_account_access_token
from app.config import settings
from app.models import person
from app.people.sheets_client import SheetsApiError, fetch_values

logger = logging.getLogger(__name__)

_TRUTHY = {"tak", "true", "prawda", "1", "x", "yes"}


class PeopleSyncNotConfigured(RuntimeError):
    pass


@dataclass
class SyncResult:
    upserted: int
    deactivated: int


def _parse_active(raw: str) -> bool:
    value = (raw or "").strip().lower()
    if not value:
        return True
    return value in _TRUTHY


def _parse_aliases(raw: str) -> list[str]:
    return [alias.strip() for alias in (raw or "").split(",") if alias.strip()]


def sync_people_from_sheet(db: Session) -> SyncResult:
    if not settings.sheets_people_id:
        raise PeopleSyncNotConfigured("SHEETS_PEOPLE_ID nie jest ustawione w .env.")

    access_token = get_service_account_access_token()
    rows = fetch_values(access_token, settings.sheets_people_id)
    if not rows:
        # Pusty odczyt traktujemy jako podejrzany, nie jako "wszyscy usunięci" —
        # inaczej chwilowy błąd API dezaktywowałby całą tabelę person.
        raise SheetsApiError(
            "Arkusz „Osoby” zwrócił zero wierszy — sync przerwany, żeby nie "
            "dezaktywować wszystkich osób przez pomyłkę."
        )

    now = datetime.now(timezone.utc)
    seen_emails: set[str] = set()
    upserted = 0

    for row in rows:
        cells = list(row) + [""] * (5 - len(row))
        full_name, email, aliases_raw, org, active_raw = (str(c) for c in cells[:5])
        email = email.strip().lower()
        full_name = full_name.strip()
        if not email or not full_name:
            logger.warning("Pomijam wiersz arkusza „Osoby” bez email/imienia i nazwiska: %r", row)
            continue

        seen_emails.add(email)
        stmt = pg_insert(person).values(
            full_name=full_name,
            email=email,
            aliases=_parse_aliases(aliases_raw),
            org=org.strip() or None,
            active=_parse_active(active_raw),
            synced_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[person.c.email],
            set_={
                "full_name": stmt.excluded.full_name,
                "aliases": stmt.excluded.aliases,
                "org": stmt.excluded.org,
                "active": stmt.excluded.active,
                "synced_at": stmt.excluded.synced_at,
            },
        )
        db.execute(stmt)
        upserted += 1

    deactivate_stmt = (
        update(person)
        .where(person.c.email.notin_(seen_emails))
        .where(person.c.active.is_(True))
        .values(active=False, synced_at=now)
    )
    result = db.execute(deactivate_stmt)
    db.commit()

    return SyncResult(upserted=upserted, deactivated=result.rowcount or 0)


def sync_people_on_startup(db: Session, owner_id: uuid.UUID | None) -> None:
    """Wywoływane raz przy starcie backendu. Nigdy nie rzuca — tylko loguje."""
    if owner_id is None:
        logger.info("Sync osób pominięty przy starcie — nikt jeszcze nie zalogował się przez Google.")
        return

    try:
        result = sync_people_from_sheet(db)
        logger.info(
            "Sync osób przy starcie: %d upsertów, %d dezaktywacji.", result.upserted, result.deactivated
        )
    except (PeopleSyncNotConfigured, ServiceAccountNotConfigured, SheetsApiError) as exc:
        logger.warning("Sync osób przy starcie pominięty: %s", exc)
    except Exception:
        logger.exception("Sync osób przy starcie nie powiódł się.")
