"""Zapis zadań do Google Sheets — widok eksportowy (SPEC.md §6, etap 7).

Kierunek jednostronny: Postgres -> Sheets. `append_task_row` dopisuje nowy
wiersz przy zatwierdzeniu spotkania, `update_task_row` aktualizuje istniejący
wiersz przy zmianie statusu/deadline'u (PATCH /tasks/{id}).

Kolumna A (uuid zadania) to klucz do odnalezienia wiersza, gdyby numeracja
zapisana w `task.sheets_row` rozjechała się z zawartością arkusza (np. ktoś
ręcznie wstawił/usunął wiersz) — patrz `_find_row_index` i `update_task_row`.

`_row_values` / `_parse_row_number` / `_find_row_index` są czystymi funkcjami
(łatwe do testowania w izolacji, tak jak w app.meetings.review).
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.models import meeting, person, task, task_raci, topic
from app.tasks.sheets_client import (
    SheetsApiError,
    append_values,
    batch_update,
    get_first_sheet_id,
    get_values,
    update_values,
)

logger = logging.getLogger(__name__)

HEADER = [
    "ID zadania",
    "Data spotkania",
    "Temat/Dostawca",
    "Zadanie",
    "R",
    "A",
    "C",
    "I",
    "Deadline",
    "Status",
    "Zaktualizowano",
]

_STATUS_LABELS = {"open": "otwarte", "done": "zrobione", "cancelled": "anulowane"}

_VALUES_RANGE = "A:K"
_HEADER_RANGE = "A1:K1"
_COLUMN_A_RANGE = "A2:A"


class TasksSheetsNotConfigured(RuntimeError):
    pass


def _require_spreadsheet_id() -> str:
    if not settings.sheets_tasks_id:
        raise TasksSheetsNotConfigured("SHEETS_TASKS_ID nie jest ustawione w .env.")
    return settings.sheets_tasks_id


def _row_values(data: dict, now: datetime | None = None) -> list[str]:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M")
    return [
        data["id"],
        data["meeting_date"],
        data["topic_name"],
        data["description"],
        data["r"],
        data["a"],
        data["c"],
        data["i"],
        data["deadline"],
        _STATUS_LABELS.get(data["status"], data["status"]),
        stamp,
    ]


def _parse_row_number(updated_range: str) -> int:
    """"'Zadania RACI'!A6:K6" (lub "Sheet1!A6:K6") -> 6."""
    cell_range = updated_range.rsplit("!", 1)[-1]
    match = re.search(r"[A-Z]+(\d+)", cell_range)
    if not match:
        raise SheetsApiError(f"Nie udało się odczytać numeru wiersza z odpowiedzi Sheets API: {updated_range!r}")
    return int(match.group(1))


def _find_row_index(column_values: list[list[str]], target_id: str) -> int | None:
    """column_values = wynik get_values(..., "A2:A") — bez nagłówka.
    Zwraca numer wiersza w arkuszu (1-indexed, z uwzględnieniem nagłówka) albo None."""
    for offset, row in enumerate(column_values):
        if row and row[0] == target_id:
            return offset + 2  # +1 za 1-indexing, +1 za wiersz nagłówka
    return None


def _load_row_data(db: Session, task_id: uuid.UUID) -> dict:
    row = (
        db.execute(
            select(
                task.c.id,
                task.c.description,
                task.c.deadline,
                task.c.status,
                meeting.c.meeting_date,
                topic.c.name.label("topic_name"),
            )
            .select_from(
                task.join(meeting, task.c.meeting_id == meeting.c.id).outerjoin(
                    topic, task.c.topic_id == topic.c.id
                )
            )
            .where(task.c.id == task_id)
        )
        .mappings()
        .one()
    )

    raci_rows = db.execute(
        select(task_raci.c.role, person.c.full_name)
        .select_from(task_raci.join(person, task_raci.c.person_id == person.c.id))
        .where(task_raci.c.task_id == task_id)
    ).all()
    names: dict[str, list[str]] = {"R": [], "A": [], "C": [], "I": []}
    for raci_row in raci_rows:
        names[raci_row.role].append(raci_row.full_name)

    return {
        "id": str(row["id"]),
        "meeting_date": row["meeting_date"].isoformat(),
        "topic_name": row["topic_name"] or "",
        "description": row["description"],
        "r": names["R"][0] if names["R"] else "",
        "a": names["A"][0] if names["A"] else "",
        "c": ", ".join(names["C"]),
        "i": ", ".join(names["I"]),
        "deadline": row["deadline"].isoformat() if row["deadline"] else "",
        "status": row["status"],
    }


def ensure_header(access_token: str) -> None:
    spreadsheet_id = _require_spreadsheet_id()
    existing = get_values(access_token, spreadsheet_id, _HEADER_RANGE)
    if existing:
        # Nagłówek już jest — nie nadpisuj (mógł zostać ręcznie sformatowany).
        return
    update_values(access_token, spreadsheet_id, _HEADER_RANGE, [HEADER])
    try:
        sheet_id = get_first_sheet_id(access_token, spreadsheet_id)
        batch_update(
            access_token,
            spreadsheet_id,
            {
                "requests": [
                    {
                        "addProtectedRange": {
                            "protectedRange": {
                                "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                                "description": "Nagłówek — nie edytować ręcznie",
                                # warningOnly=True zamiast twardej blokady: właściciela arkusza
                                # (jedynego użytkownika tej appki) i tak nie da się zablokować
                                # protected range'em — Sheets nigdy nie ogranicza właściciela.
                                # Warning pokazuje się każdemu, właścicielowi też, więc realnie
                                # chroni przed przypadkowym ruszeniem kolumn (SPEC.md §6).
                                "warningOnly": True,
                            }
                        }
                    }
                ]
            },
        )
    except SheetsApiError:
        logger.warning("Nie udało się ustawić protected range na nagłówku arkusza „Zadania RACI”.")


def append_task_row(db: Session, access_token: str, task_id: uuid.UUID) -> int:
    spreadsheet_id = _require_spreadsheet_id()
    data = _load_row_data(db, task_id)
    result = append_values(access_token, spreadsheet_id, _VALUES_RANGE, [_row_values(data)])
    row_number = _parse_row_number(result["updates"]["updatedRange"])
    db.execute(update(task).where(task.c.id == task_id).values(sheets_row=row_number))
    return row_number


def update_task_row(db: Session, access_token: str, task_id: uuid.UUID) -> None:
    spreadsheet_id = _require_spreadsheet_id()
    stored_row = db.execute(select(task.c.sheets_row).where(task.c.id == task_id)).scalar_one()
    data = _load_row_data(db, task_id)

    row_number = stored_row
    if row_number is not None:
        current = get_values(access_token, spreadsheet_id, f"A{row_number}:A{row_number}")
        matches = bool(current) and bool(current[0]) and current[0][0] == data["id"]
        if not matches:
            row_number = None

    if row_number is None:
        column = get_values(access_token, spreadsheet_id, _COLUMN_A_RANGE)
        row_number = _find_row_index(column, data["id"])

    if row_number is None:
        # Zadanie nigdy nie trafiło do arkusza (np. dodane zanim skonfigurowano
        # SHEETS_TASKS_ID) — dopisz zamiast aktualizować nieistniejący wiersz.
        append_task_row(db, access_token, task_id)
        return

    if row_number != stored_row:
        db.execute(update(task).where(task.c.id == task_id).values(sheets_row=row_number))

    update_values(access_token, spreadsheet_id, f"A{row_number}:K{row_number}", [_row_values(data)])
