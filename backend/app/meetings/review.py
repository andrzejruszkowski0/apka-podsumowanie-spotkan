"""Ekran weryfikacji — logika serwerowa (SPEC.md §11, ETAPY.md etap 6).

To jest guardrail całego systemu: nic nie trafia do Sheets/przypomnień (etap 7,
8), dopóki właściciel nie przejrzy i nie zatwierdzi kandydatur AI.

`_compute_task_unresolved` / `_compute_decision_unresolved` są czystymi
funkcjami (bez DB) — łatwe do przetestowania w izolacji, tak jak resolver.py.
Reguła: nazwisko jest „nierozwiązane" tylko wtedy, gdy AI w ogóle je podało
(raci_raw / decided_by_raw niepuste), a nie ma dla niego odpowiadającego
wiersza w task_raci / decision.decided_by. Brak wzmianki o roli w ogóle
(np. A nigdy nie padło) to stan poprawny, nie blokujący — zgodnie z §10.2
(„A = null, jeśli nie padło wprost — nie zgaduj").
"""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, Field
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models import decision, task, task_raci


def _compute_task_unresolved(
    raci_raw: dict | None, r_person_id, a_person_id, c_count: int, i_count: int
) -> bool:
    raw = raci_raw or {}
    if raw.get("R") and r_person_id is None:
        return True
    if raw.get("A") and a_person_id is None:
        return True
    if len(raw.get("C") or []) > c_count:
        return True
    if len(raw.get("I") or []) > i_count:
        return True
    return False


def _compute_decision_unresolved(decided_by_raw: str | None, decided_by_person_id) -> bool:
    return bool(decided_by_raw) and decided_by_person_id is None


def _load_task_raci(db: Session, task_id: uuid.UUID) -> dict[str, list[str]]:
    rows = db.execute(
        select(task_raci.c.role, task_raci.c.person_id).where(task_raci.c.task_id == task_id)
    ).all()
    grouped: dict[str, list[str]] = {"R": [], "A": [], "C": [], "I": []}
    for row in rows:
        grouped[row.role].append(str(row.person_id))
    return grouped


def _serialize_task(db: Session, row) -> dict:
    raci_resolved = _load_task_raci(db, row.id)
    r_person_id = raci_resolved["R"][0] if raci_resolved["R"] else None
    a_person_id = raci_resolved["A"][0] if raci_resolved["A"] else None
    raci_raw = row.raci_raw or {}

    unresolved = _compute_task_unresolved(
        raci_raw, r_person_id, a_person_id, len(raci_resolved["C"]), len(raci_resolved["I"])
    )

    return {
        "id": str(row.id),
        "description": row.description,
        "deadline": row.deadline.isoformat() if row.deadline else None,
        "ai_confidence": row.ai_confidence,
        "quote": row.quote,
        "edited_by_user": row.edited_by_user,
        "unresolved": unresolved,
        "raci": {
            "R": {"person_id": r_person_id, "raw": raci_raw.get("R")},
            "A": {"person_id": a_person_id, "raw": raci_raw.get("A")},
            "C": {"person_ids": raci_resolved["C"], "raw": raci_raw.get("C") or []},
            "I": {"person_ids": raci_resolved["I"], "raw": raci_raw.get("I") or []},
        },
    }


def _serialize_decision(row) -> dict:
    decided_by_id = str(row.decided_by) if row.decided_by else None
    unresolved = _compute_decision_unresolved(row.decided_by_raw, row.decided_by)
    return {
        "id": str(row.id),
        "statement": row.statement,
        "decided_on": row.decided_on.isoformat(),
        "category": row.category,
        "ai_confidence": row.ai_confidence,
        "quote": row.quote,
        "unresolved": unresolved,
        "decided_by": {"person_id": decided_by_id, "raw": row.decided_by_raw},
    }


def get_review_payload(db: Session, meeting_id: uuid.UUID) -> dict:
    task_rows = db.execute(
        select(task).where(task.c.meeting_id == meeting_id).order_by(task.c.created_at)
    ).all()
    decision_rows = db.execute(
        select(decision).where(decision.c.meeting_id == meeting_id).order_by(decision.c.created_at)
    ).all()
    return {
        "tasks": [_serialize_task(db, row) for row in task_rows],
        "decisions": [_serialize_decision(row) for row in decision_rows],
    }


def any_unresolved(db: Session, meeting_id: uuid.UUID) -> bool:
    payload = get_review_payload(db, meeting_id)
    return any(t["unresolved"] for t in payload["tasks"]) or any(
        d["unresolved"] for d in payload["decisions"]
    )


# --- modele wejściowe dla PUT /meetings/{id}/review ---


class TaskRaciUpdate(BaseModel):
    r_person_id: uuid.UUID | None = None
    a_person_id: uuid.UUID | None = None
    c_person_ids: list[uuid.UUID] = Field(default_factory=list)
    i_person_ids: list[uuid.UUID] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    id: uuid.UUID
    description: str
    deadline: date | None = None
    raci: TaskRaciUpdate = Field(default_factory=TaskRaciUpdate)


class DecisionUpdate(BaseModel):
    id: uuid.UUID
    statement: str
    category: str | None = None
    decided_on: date
    decided_by_person_id: uuid.UUID | None = None


class ReviewUpdateIn(BaseModel):
    tasks: list[TaskUpdate] = Field(default_factory=list)
    decisions: list[DecisionUpdate] = Field(default_factory=list)
    deleted_task_ids: list[uuid.UUID] = Field(default_factory=list)
    deleted_decision_ids: list[uuid.UUID] = Field(default_factory=list)


def _apply_task_update(db: Session, meeting_id: uuid.UUID, update_in: TaskUpdate) -> None:
    current = db.execute(
        select(task).where(task.c.id == update_in.id, task.c.meeting_id == meeting_id)
    ).one()
    current_raci = _load_task_raci(db, update_in.id)
    current_r = current_raci["R"][0] if current_raci["R"] else None
    current_a = current_raci["A"][0] if current_raci["A"] else None

    new_r = str(update_in.raci.r_person_id) if update_in.raci.r_person_id else None
    new_a = str(update_in.raci.a_person_id) if update_in.raci.a_person_id else None
    new_c = sorted(str(pid) for pid in update_in.raci.c_person_ids)
    new_i = sorted(str(pid) for pid in update_in.raci.i_person_ids)

    changed = (
        current.description != update_in.description
        or current.deadline != update_in.deadline
        or current_r != new_r
        or current_a != new_a
        or sorted(current_raci["C"]) != new_c
        or sorted(current_raci["I"]) != new_i
    )

    db.execute(
        update(task)
        .where(task.c.id == update_in.id)
        .values(
            description=update_in.description,
            deadline=update_in.deadline,
            edited_by_user=current.edited_by_user or changed,
        )
    )

    db.execute(delete(task_raci).where(task_raci.c.task_id == update_in.id))
    # dict.fromkeys zamiast set(): usuwa duplikaty (np. podwójny klik w liście
    # zaznaczeń na froncie), zachowując kolejność — bez tego duplikat w C/I
    # wywalał 500 na unique constraint (task_id, person_id, role).
    new_rows = []
    if update_in.raci.r_person_id:
        new_rows.append({"task_id": update_in.id, "person_id": update_in.raci.r_person_id, "role": "R"})
    if update_in.raci.a_person_id:
        new_rows.append({"task_id": update_in.id, "person_id": update_in.raci.a_person_id, "role": "A"})
    for pid in dict.fromkeys(update_in.raci.c_person_ids):
        new_rows.append({"task_id": update_in.id, "person_id": pid, "role": "C"})
    for pid in dict.fromkeys(update_in.raci.i_person_ids):
        new_rows.append({"task_id": update_in.id, "person_id": pid, "role": "I"})
    if new_rows:
        db.execute(task_raci.insert(), new_rows)


def _apply_decision_update(db: Session, meeting_id: uuid.UUID, update_in: DecisionUpdate) -> None:
    db.execute(
        update(decision)
        .where(decision.c.id == update_in.id, decision.c.meeting_id == meeting_id)
        .values(
            statement=update_in.statement,
            category=update_in.category,
            decided_on=update_in.decided_on,
            decided_by=update_in.decided_by_person_id,
        )
    )


def apply_review_update(db: Session, meeting_id: uuid.UUID, body: ReviewUpdateIn) -> None:
    if body.deleted_task_ids:
        db.execute(
            delete(task).where(task.c.id.in_(body.deleted_task_ids), task.c.meeting_id == meeting_id)
        )
    if body.deleted_decision_ids:
        db.execute(
            delete(decision).where(
                decision.c.id.in_(body.deleted_decision_ids), decision.c.meeting_id == meeting_id
            )
        )
    for task_update in body.tasks:
        _apply_task_update(db, meeting_id, task_update)
    for decision_update in body.decisions:
        _apply_decision_update(db, meeting_id, decision_update)
    db.commit()
