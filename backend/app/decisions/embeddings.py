"""Embeddingi decyzji do wyszukiwania semantycznego (SPEC.md §10.4, etap 9).

Generowane przy zatwierdzeniu spotkania (`generate_missing_embeddings`, wołane
z app.meetings.router.approve_meeting) — best-effort: błąd Gemini jest
logowany, ale nigdy nie blokuje zatwierdzenia. Embedding to funkcja
wyszukiwania w rejestrze decyzji, nie integralność danych zadań/Sheets, więc
nie zasługuje na te same twarde gwarancje co eksport do arkusza (SPEC.md §6).

`backfill_missing_embeddings` to ten sam mechanizm użyty przez skrypt
jednorazowy (scripts/backfill_decision_embeddings.py, ETAPY.md etap 9 pkt 3)
dla decyzji zapisanych przed włączeniem tego etapu.
"""

from __future__ import annotations

import logging
import uuid

from google.genai.errors import APIError
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.meetings.gemini_client import EmbeddingError, GeminiNotConfigured, embed_text
from app.models import decision

logger = logging.getLogger(__name__)

_EMBEDDING_ERRORS = (GeminiNotConfigured, EmbeddingError, APIError)


def _embed_rows(db: Session, rows) -> int:
    count = 0
    for row in rows:
        try:
            values = embed_text(row.statement)
        except _EMBEDDING_ERRORS as exc:
            logger.warning("Nie udało się wygenerować embeddingu decyzji %s: %s", row.id, exc)
            continue
        db.execute(update(decision).where(decision.c.id == row.id).values(embedding=values))
        count += 1
    db.commit()
    return count


def generate_missing_embeddings(db: Session, meeting_id: uuid.UUID) -> int:
    rows = db.execute(
        select(decision.c.id, decision.c.statement).where(
            decision.c.meeting_id == meeting_id, decision.c.embedding.is_(None)
        )
    ).all()
    return _embed_rows(db, rows)


def backfill_missing_embeddings(db: Session) -> int:
    rows = db.execute(
        select(decision.c.id, decision.c.statement).where(decision.c.embedding.is_(None))
    ).all()
    return _embed_rows(db, rows)
