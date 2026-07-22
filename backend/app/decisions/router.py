"""Endpoint /decisions — rejestr decyzji z wyszukiwaniem semantycznym
(SPEC.md §10.4, §9, etap 9).

Bez `q`: filtr po temacie (opcjonalny), chronologicznie. Z `q`: embedding
zapytania przez Gemini, ranking po `cosine_distance` — to ten sam operator
(`<=>`), na którym stoi indeks ivfflat z migracji 0001 (`vector_cosine_ops`).

Tak jak w /tasks (SPEC.md §6, etap 7): tylko decyzje z zatwierdzonych
spotkań — dopóki spotkanie jest w weryfikacji, jego kandydatury żyją na
ekranie /review (etap 6), nie w rejestrze.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from google.genai.errors import APIError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, require_user
from app.db import get_db
from app.meetings.gemini_client import EmbeddingError, GeminiNotConfigured, embed_text
from app.models import decision, meeting, person, topic

router = APIRouter(tags=["decisions"])

_SEARCH_LIMIT = 20

_DECISION_QUERY = select(
    decision.c.id,
    decision.c.meeting_id,
    decision.c.topic_id,
    topic.c.name.label("topic_name"),
    decision.c.statement,
    decision.c.decided_on,
    decision.c.category,
    decision.c.decided_by_raw,
    person.c.full_name.label("decided_by_name"),
    decision.c.created_at,
).select_from(
    decision.join(meeting, decision.c.meeting_id == meeting.c.id)
    .outerjoin(topic, decision.c.topic_id == topic.c.id)
    .outerjoin(person, decision.c.decided_by == person.c.id)
)


def _serialize(row) -> dict:
    return {
        "id": str(row.id),
        "meeting_id": str(row.meeting_id),
        "topic_id": str(row.topic_id) if row.topic_id else None,
        "topic_name": row.topic_name,
        "statement": row.statement,
        "decided_on": row.decided_on.isoformat(),
        "category": row.category,
        "decided_by": row.decided_by_name or row.decided_by_raw,
        "created_at": row.created_at.isoformat(),
    }


@router.get("/decisions")
def list_decisions(
    topic_id: uuid.UUID | None = None,
    q: str | None = None,
    user: CurrentUser = Depends(require_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = _DECISION_QUERY.where(meeting.c.user_id == user.id, meeting.c.status == "approved")
    if topic_id:
        query = query.where(decision.c.topic_id == topic_id)

    if q and q.strip():
        try:
            query_embedding = embed_text(q)
        except (GeminiNotConfigured, EmbeddingError, APIError) as exc:
            raise HTTPException(
                status_code=400, detail=f"Wyszukiwanie semantyczne nie powiodło się: {exc}"
            ) from exc
        query = (
            query.where(decision.c.embedding.isnot(None))
            .order_by(decision.c.embedding.cosine_distance(query_embedding))
            .limit(_SEARCH_LIMIT)
        )
    else:
        query = query.order_by(decision.c.decided_on.desc(), decision.c.created_at.desc())

    rows = db.execute(query).all()
    return [_serialize(row) for row in rows]
