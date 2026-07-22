"""Job daily_reminders: mail przypomnień o zadaniach z bliskim terminem
(SPEC.md §7, etap 8).

Wybór: task.status='open' AND deadline BETWEEN dziś a dziś+REMINDER_DAYS_AHEAD.
Odbiorca: osoba z rolą R (To), z rolą A w Cc (jeśli jest).

Idempotencja: sprawdzenie notification_log przed wysyłką (per zadanie, nie per
odbiorca — jedno zadanie = jeden mail dziennie, niezależnie ilu ma odbiorców).
Unikalny indeks notif_once_per_day (kind, task_id, recipient, sent_on) jest
twardym zabezpieczeniem — insert przez ON CONFLICT DO NOTHING nigdy go nie
narusza, nawet przy równoległym/powtórzonym uruchomieniu.

Catch-up: `catch_up_if_needed` woła run_daily_reminders() przy starcie
backendu, jeśli scheduler_run.daily_reminders.last_run < dziś (albo nie ma
wpisu). Nadrabia TYLKO bieżący dzień — nie ma tu pętli po zaległych dniach.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.auth.accounts import get_owner_id
from app.auth.google_oauth import NeedsReauthError
from app.auth.tokens import get_valid_access_token
from app.config import settings
from app.db import SessionLocal
from app.models import notification_log, person, scheduler_run, task, task_raci, topic
from app.notifications.gmail_client import GmailApiError, send_message
from app.notifications.templates import reminder_body, reminder_subject

logger = logging.getLogger(__name__)

_KIND = "reminder"
_JOB_NAME = "daily_reminders"


def _today() -> date:
    return datetime.now(ZoneInfo(settings.timezone)).date()


def _due_tasks(db: Session, today: date) -> list:
    end = today + timedelta(days=settings.reminder_days_ahead)
    return (
        db.execute(
            select(
                task.c.id,
                task.c.description,
                task.c.deadline,
                topic.c.name.label("topic_name"),
            )
            .select_from(task.outerjoin(topic, task.c.topic_id == topic.c.id))
            .where(task.c.status == "open", task.c.deadline.between(today, end))
        )
        .mappings()
        .all()
    )


def _raci_emails(db: Session, task_id: uuid.UUID) -> tuple[str | None, str | None]:
    rows = db.execute(
        select(task_raci.c.role, person.c.email)
        .select_from(task_raci.join(person, task_raci.c.person_id == person.c.id))
        .where(task_raci.c.task_id == task_id, task_raci.c.role.in_(("R", "A")))
    ).all()
    by_role = {row.role: row.email for row in rows}
    return by_role.get("R"), by_role.get("A")


def _already_sent(db: Session, task_id: uuid.UUID, today: date) -> bool:
    return (
        db.execute(
            select(notification_log.c.id).where(
                notification_log.c.kind == _KIND,
                notification_log.c.task_id == task_id,
                notification_log.c.sent_on == today,
            )
        ).first()
        is not None
    )


def _log_send(db: Session, *, task_id: uuid.UUID, recipient: str, sent_on: date, gmail_id: str) -> None:
    stmt = pg_insert(notification_log).values(
        kind=_KIND,
        task_id=task_id,
        recipient=recipient,
        sent_on=sent_on,
        gmail_id=gmail_id,
    )
    stmt = stmt.on_conflict_do_nothing(
        index_elements=[
            notification_log.c.kind,
            notification_log.c.task_id,
            notification_log.c.recipient,
            notification_log.c.sent_on,
        ],
        # notif_once_per_day to indeks CZĘŚCIOWY (where task_id is not null) —
        # bez powtórzenia tego warunku tutaj Postgres nie rozpozna go jako
        # arbitra ON CONFLICT (InvalidColumnReference).
        index_where=notification_log.c.task_id.isnot(None),
    )
    db.execute(stmt)


def _send_reminder(db: Session, access_token: str, row, today: date) -> None:
    r_email, a_email = _raci_emails(db, row["id"])
    if not r_email:
        logger.info("Zadanie %s pominięte — brak osoby z rolą R.", row["id"])
        return

    subject = reminder_subject(row["description"])
    body = reminder_body(description=row["description"], deadline=row["deadline"], topic_name=row["topic_name"])
    gmail_id = send_message(access_token, to=r_email, cc=a_email, subject=subject, body=body)

    _log_send(db, task_id=row["id"], recipient=r_email, sent_on=today, gmail_id=gmail_id)
    if a_email:
        _log_send(db, task_id=row["id"], recipient=a_email, sent_on=today, gmail_id=gmail_id)
    db.commit()


def _mark_run(db: Session, today: date) -> None:
    stmt = pg_insert(scheduler_run).values(job_name=_JOB_NAME, last_run=today)
    stmt = stmt.on_conflict_do_update(
        index_elements=[scheduler_run.c.job_name], set_={"last_run": stmt.excluded.last_run}
    )
    db.execute(stmt)
    db.commit()


def run_daily_reminders(db: Session | None = None) -> None:
    owns_session = db is None
    db = db or SessionLocal()
    try:
        today = _today()
        user_id = get_owner_id(db)
        if user_id is None:
            logger.info("Brak zalogowanego właściciela — pomijam wysyłkę przypomnień.")
            return

        try:
            access_token = get_valid_access_token(db, user_id)
        except NeedsReauthError as exc:
            logger.error("Wysyłka przypomnień nieudana — wymagane ponowne logowanie Google: %s", exc)
            return

        for row in _due_tasks(db, today):
            if _already_sent(db, row["id"], today):
                continue
            try:
                _send_reminder(db, access_token, row, today)
            except GmailApiError as exc:
                db.rollback()
                logger.error("Nie udało się wysłać przypomnienia dla zadania %s: %s", row["id"], exc)

        _mark_run(db, today)
    finally:
        if owns_session:
            db.close()


def catch_up_if_needed(db: Session | None = None) -> None:
    owns_session = db is None
    db = db or SessionLocal()
    try:
        today = _today()
        last_run = db.execute(
            select(scheduler_run.c.last_run).where(scheduler_run.c.job_name == _JOB_NAME)
        ).scalar_one_or_none()
        if last_run is None or last_run < today:
            logger.info("Catch-up: uruchamiam %s (last_run=%s, today=%s).", _JOB_NAME, last_run, today)
            run_daily_reminders(db)
    finally:
        if owns_session:
            db.close()
