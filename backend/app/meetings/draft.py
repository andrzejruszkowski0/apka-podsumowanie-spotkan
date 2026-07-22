"""Generowanie i wysyłka szablonów maili podsumowujących spotkanie
(SPEC.md §10.5, §9, ETAPY.md etap 10).

Guardrail jak w reszcie aplikacji (§0, §8, briefing z etapu 9): `generate_draft_preview`
tylko generuje treść przez Gemini, nic nie wysyła. `send_draft` wysyła DOKŁADNIE
to, co wywołujący przekaże (subject/body, które właściciel przeczytał i mógł
poprawić w panelu) — nie regeneruje treści.

Router (app.meetings.router) waliduje, że `meeting_id` istnieje i należy do
zalogowanego użytkownika, zanim wywoła funkcje tego modułu — tak samo jak przy
GET/PUT /review i POST /approve.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.meetings.draft_prompts import (
    DraftDecisionContext,
    DraftTaskContext,
    Template,
    build_draft_prompt,
    build_subject,
)
from app.meetings.gemini_client import generate_draft
from app.models import decision, meeting, notification_log, person, task, task_raci, topic
from app.notifications.gmail_client import send_message

_KIND = "summary"


def _topic_name(db: Session, topic_id: uuid.UUID | None) -> str | None:
    if topic_id is None:
        return None
    return db.execute(select(topic.c.name).where(topic.c.id == topic_id)).scalar_one_or_none()


def _decisions_for_meeting(db: Session, meeting_id: uuid.UUID) -> list[DraftDecisionContext]:
    rows = db.execute(
        select(
            decision.c.statement,
            decision.c.decided_on,
            decision.c.category,
            person.c.full_name.label("decided_by_name"),
        )
        .select_from(decision.outerjoin(person, decision.c.decided_by == person.c.id))
        .where(decision.c.meeting_id == meeting_id)
        .order_by(decision.c.decided_on, decision.c.created_at)
    ).all()
    return [
        DraftDecisionContext(
            statement=r.statement, decided_on=r.decided_on, decided_by_name=r.decided_by_name, category=r.category
        )
        for r in rows
    ]


# Aliasy person osobno dla R i A: jedno zadanie ma co najwyżej jedną osobę w
# każdej z tych ról (indeksy częściowe task_single_r/task_single_a, SPEC.md
# §2), więc dwa outerjoiny nie mnożą wierszy.
_tr_r = task_raci.alias("tr_r")
_tr_a = task_raci.alias("tr_a")
_person_r = person.alias("person_r")
_person_a = person.alias("person_a")

_TASK_WITH_RACI = (
    task.outerjoin(_tr_r, (_tr_r.c.task_id == task.c.id) & (_tr_r.c.role == "R"))
    .outerjoin(_person_r, _tr_r.c.person_id == _person_r.c.id)
    .outerjoin(_tr_a, (_tr_a.c.task_id == task.c.id) & (_tr_a.c.role == "A"))
    .outerjoin(_person_a, _tr_a.c.person_id == _person_a.c.id)
)


def _tasks_for_meeting(db: Session, meeting_id: uuid.UUID) -> list[DraftTaskContext]:
    rows = db.execute(
        select(
            task.c.description,
            task.c.deadline,
            task.c.status,
            _person_r.c.full_name.label("r_name"),
            _person_a.c.full_name.label("a_name"),
        )
        .select_from(_TASK_WITH_RACI)
        .where(task.c.meeting_id == meeting_id)
        .order_by(task.c.created_at)
    ).all()
    return [
        DraftTaskContext(description=r.description, deadline=r.deadline, status=r.status, r_name=r.r_name, a_name=r.a_name)
        for r in rows
    ]


def generate_draft_preview(db: Session, meeting_id: uuid.UUID, template: Template) -> dict:
    meeting_row = db.execute(select(meeting).where(meeting.c.id == meeting_id)).mappings().one()
    topic_name = _topic_name(db, meeting_row["topic_id"])
    decisions = _decisions_for_meeting(db, meeting_id)
    # supplier: brak zadań w kontekście promptu w ogóle — patrz docstring
    # draft_prompts.py, to jedyny pewny sposób, żeby "zadania własne" nie
    # wyciekły do dostawcy.
    tasks = [] if template == "supplier" else _tasks_for_meeting(db, meeting_id)

    prompt = build_draft_prompt(
        template=template,
        meeting_title=meeting_row["title"],
        meeting_date=meeting_row["meeting_date"],
        topic_name=topic_name,
        decisions=decisions,
        tasks=tasks,
    )
    body = generate_draft(prompt)
    return {
        "template": template,
        "subject": build_subject(template, meeting_row["title"]),
        "body": body,
    }


def send_draft(
    db: Session,
    *,
    access_token: str,
    meeting_id: uuid.UUID,
    subject: str,
    body: str,
    to: str,
    cc: str | None = None,
) -> dict:
    gmail_id = send_message(access_token, to=to, cc=cc, subject=subject, body=body)
    db.execute(
        pg_insert(notification_log).values(
            kind=_KIND,
            meeting_id=meeting_id,
            recipient=to,
            sent_on=date.today(),
            gmail_id=gmail_id,
        )
    )
    db.commit()
    return {"sent": True, "gmail_id": gmail_id}
