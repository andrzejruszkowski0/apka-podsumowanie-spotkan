"""Endpointy /topics — dostawcy/tematy, oś grupująca decyzje i briefingi (SPEC.md §9)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, require_user
from app.db import get_db
from app.models import topic

router = APIRouter(prefix="/topics", tags=["topics"])


class TopicIn(BaseModel):
    name: str
    kind: Literal["supplier", "project", "internal"]
    notes: str | None = None


def _serialize(row) -> dict:
    return {
        "id": str(row["id"]),
        "name": row["name"],
        "kind": row["kind"],
        "notes": row["notes"],
    }


@router.get("")
def list_topics(
    user: CurrentUser = Depends(require_user), db: Session = Depends(get_db)
) -> list[dict]:
    rows = db.execute(select(topic).order_by(topic.c.name)).mappings().all()
    return [_serialize(row) for row in rows]


@router.post("")
def create_topic(
    body: TopicIn, user: CurrentUser = Depends(require_user), db: Session = Depends(get_db)
) -> dict:
    try:
        result = db.execute(
            topic.insert().values(name=body.name, kind=body.kind, notes=body.notes).returning(topic)
        )
        row = result.mappings().one()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Temat o tej nazwie już istnieje.") from exc
    return _serialize(row)
