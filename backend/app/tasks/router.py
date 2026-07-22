"""Endpointy /tasks — lista z filtrami i zmiana statusu/deadline'u (SPEC.md §6, §9, etap 7).

PATCH synchronizuje zmianę do Sheets, ale błąd samej synchronizacji (np.
Sheets nieskonfigurowany, token wygasł) nie blokuje zapisu w Postgresie —
to on jest źródłem prawdy (SPEC.md §0), Sheets to tylko widok eksportowy.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, require_user
from app.auth.google_oauth import NeedsReauthError
from app.auth.tokens import get_valid_access_token
from app.db import get_db
from app.models import meeting, person, task, task_raci, topic
from app.tasks.sheets_client import SheetsApiError
from app.tasks.sheets_sync import TasksSheetsNotConfigured, update_task_row

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tasks"])

_TASK_QUERY = select(
    task.c.id,
    task.c.meeting_id,
    task.c.topic_id,
    topic.c.name.label("topic_name"),
    task.c.description,
    task.c.deadline,
    task.c.status,
    task.c.done_at,
    task.c.ai_confidence,
    task.c.sheets_row,
    task.c.created_at,
).select_from(
    task.join(meeting, task.c.meeting_id == meeting.c.id).outerjoin(topic, task.c.topic_id == topic.c.id)
)


class TaskPatchIn(BaseModel):
    status: Literal["open", "done", "cancelled"] | None = None
    deadline: date | None = None


def _load_raci_names(db: Session, task_id: uuid.UUID) -> dict[str, list[str]]:
    rows = db.execute(
        select(task_raci.c.role, person.c.full_name)
        .select_from(task_raci.join(person, task_raci.c.person_id == person.c.id))
        .where(task_raci.c.task_id == task_id)
    ).all()
    names: dict[str, list[str]] = {"R": [], "A": [], "C": [], "I": []}
    for row in rows:
        names[row.role].append(row.full_name)
    return names


def _serialize_task(db: Session, row: dict) -> dict:
    names = _load_raci_names(db, row["id"])
    return {
        "id": str(row["id"]),
        "meeting_id": str(row["meeting_id"]),
        "topic_id": str(row["topic_id"]) if row["topic_id"] else None,
        "topic_name": row["topic_name"],
        "description": row["description"],
        "deadline": row["deadline"].isoformat() if row["deadline"] else None,
        "status": row["status"],
        "done_at": row["done_at"].isoformat() if row["done_at"] else None,
        "ai_confidence": row["ai_confidence"],
        "sheets_row": row["sheets_row"],
        "raci": {
            "R": names["R"][0] if names["R"] else None,
            "A": names["A"][0] if names["A"] else None,
            "C": names["C"],
            "I": names["I"],
        },
        "created_at": row["created_at"].isoformat(),
    }


def _get_owned_task(db: Session, task_id: uuid.UUID, user_id: uuid.UUID) -> dict:
    row = db.execute(_TASK_QUERY.where(task.c.id == task_id, meeting.c.user_id == user_id)).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Zadanie nie istnieje.")
    return dict(row)


@router.get("/tasks")
def list_tasks(
    status: Literal["open", "done", "cancelled"] | None = None,
    topic_id: uuid.UUID | None = None,
    overdue: bool = False,
    user: CurrentUser = Depends(require_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    # Tylko zadania z zatwierdzonych spotkań — dopóki spotkanie jest w
    # weryfikacji, jego kandydatury żyją na ekranie /review (etap 6), nie tu.
    query = _TASK_QUERY.where(meeting.c.user_id == user.id, meeting.c.status == "approved")
    if status:
        query = query.where(task.c.status == status)
    if topic_id:
        query = query.where(task.c.topic_id == topic_id)
    if overdue:
        query = query.where(task.c.status == "open", task.c.deadline < date.today())
    rows = db.execute(query.order_by(task.c.created_at)).mappings().all()
    return [_serialize_task(db, dict(row)) for row in rows]


@router.patch("/tasks/{task_id}")
def patch_task(
    task_id: uuid.UUID,
    body: TaskPatchIn,
    user: CurrentUser = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict:
    _get_owned_task(db, task_id, user.id)
    updates = body.model_dump(exclude_unset=True)

    if updates:
        values: dict = {}
        if "status" in updates:
            values["status"] = updates["status"]
            values["done_at"] = datetime.now(timezone.utc) if updates["status"] == "done" else None
        if "deadline" in updates:
            values["deadline"] = updates["deadline"]
        db.execute(update(task).where(task.c.id == task_id).values(**values))
        db.commit()

        try:
            access_token = get_valid_access_token(db, user.id)
            update_task_row(db, access_token, task_id)
            db.commit()
        except (TasksSheetsNotConfigured, SheetsApiError, NeedsReauthError) as exc:
            logger.warning("Sync zadania %s do Sheets nie powiódł się: %s", task_id, exc)

    row = _get_owned_task(db, task_id, user.id)
    return _serialize_task(db, row)
