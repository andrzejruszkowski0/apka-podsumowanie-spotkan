"""Zbieranie kontekstu i generowanie briefingu przed spotkaniem
(SPEC.md §10.4, etap 9).

Guardrail jak w reszcie aplikacji (§0, §8, §10.5): `generate_preview` tylko
generuje treść przez Gemini, nic nie wysyła. `send_briefing` wysyła DOKŁADNIE
to, co wywołujący przekaże (czyli to, co właściciel zobaczył na podglądzie w
panelu) — nie regeneruje treści, bo Gemini nie jest deterministyczne i to, co
poszłoby na skrzynkę, mogłoby się różnić od tego, co zostało przeczytane.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.briefing.prompts import TaskContext, build_briefing_prompt
from app.meetings.gemini_client import generate_briefing
from app.models import decision, meeting, notification_log, person, task, task_raci, topic
from app.notifications.gmail_client import send_message

logger = logging.getLogger(__name__)

_KIND = "briefing"
_RECENT_DECISIONS_LIMIT = 10

# Join wspólny dla otwartych i zamkniętych zadań: dokładnie jedna osoba z rolą
# R na zadanie (indeks częściowy task_single_r, SPEC.md §2) — outerjoin, żeby
# zadanie bez ustalonego R nie znikało z briefingu, tylko pokazywało "brak".
_TASK_WITH_R = task.outerjoin(
    task_raci, (task_raci.c.task_id == task.c.id) & (task_raci.c.role == "R")
).outerjoin(person, task_raci.c.person_id == person.c.id)


class TopicNotFound(RuntimeError):
    pass


def _get_topic(db: Session, topic_id: uuid.UUID):
    row = db.execute(select(topic).where(topic.c.id == topic_id)).mappings().first()
    if row is None:
        raise TopicNotFound(f"Temat {topic_id} nie istnieje.")
    return row


def _last_meeting_cutoff(db: Session, topic_id: uuid.UUID) -> datetime | None:
    """Kiedy odbyło się ostatnie (zatwierdzone) spotkanie dla tego tematu —
    podstawa do wyliczenia zadań "zamkniętych od ostatniego spotkania"."""
    return db.execute(
        select(meeting.c.created_at)
        .where(meeting.c.topic_id == topic_id, meeting.c.status == "approved")
        .order_by(meeting.c.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def _recent_decisions(db: Session, topic_id: uuid.UUID) -> list[tuple[str, date]]:
    rows = db.execute(
        select(decision.c.statement, decision.c.decided_on)
        .where(decision.c.topic_id == topic_id)
        .order_by(decision.c.decided_on.desc(), decision.c.created_at.desc())
        .limit(_RECENT_DECISIONS_LIMIT)
    ).all()
    # Zapytania wróciły najnowsze najpierw (limit bierze właściwe "ostatnie N"),
    # ale prompt (§10.4) chce je chronologicznie — stąd odwrócenie kolejności.
    return list(reversed([(r.statement, r.decided_on) for r in rows]))


def _open_tasks(db: Session, topic_id: uuid.UUID, today: date) -> list[TaskContext]:
    rows = db.execute(
        select(task.c.description, task.c.deadline, person.c.full_name.label("r_name"))
        .select_from(_TASK_WITH_R)
        .where(task.c.topic_id == topic_id, task.c.status == "open")
        .order_by(task.c.deadline.asc().nulls_last())
    ).all()
    return [
        TaskContext(
            description=r.description,
            deadline=r.deadline,
            r_name=r.r_name,
            overdue=bool(r.deadline and r.deadline < today),
        )
        for r in rows
    ]


def _closed_tasks_since(db: Session, topic_id: uuid.UUID, cutoff: datetime | None) -> list[TaskContext]:
    if cutoff is None:
        return []
    rows = db.execute(
        select(task.c.description, person.c.full_name.label("r_name"))
        .select_from(_TASK_WITH_R)
        .where(task.c.topic_id == topic_id, task.c.status == "done", task.c.done_at > cutoff)
        .order_by(task.c.done_at.asc())
    ).all()
    return [TaskContext(description=r.description, deadline=None, r_name=r.r_name, overdue=False) for r in rows]


def generate_preview(db: Session, topic_id: uuid.UUID) -> dict:
    topic_row = _get_topic(db, topic_id)
    today = date.today()
    prompt = build_briefing_prompt(
        topic_name=topic_row["name"],
        decisions=_recent_decisions(db, topic_id),
        open_tasks=_open_tasks(db, topic_id, today),
        closed_tasks=_closed_tasks_since(db, topic_id, _last_meeting_cutoff(db, topic_id)),
    )
    body = generate_briefing(prompt)
    return {
        "topic_id": str(topic_id),
        "topic_name": topic_row["name"],
        "subject": f"Briefing: {topic_row['name']}",
        "body": body,
    }


def send_briefing(
    db: Session, *, owner_email: str, access_token: str, topic_id: uuid.UUID, subject: str, body: str
) -> dict:
    _get_topic(db, topic_id)  # 404, jeśli temat zniknął między podglądem a wysyłką
    gmail_id = send_message(access_token, to=owner_email, subject=subject, body=body)

    db.execute(
        pg_insert(notification_log).values(
            kind=_KIND,
            recipient=owner_email,
            sent_on=date.today(),
            gmail_id=gmail_id,
        )
    )
    db.commit()
    return {"sent": True, "gmail_id": gmail_id}
