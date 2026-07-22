"""Prompt briefingu przed spotkaniem (SPEC.md §10.4, etap 9)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import TypedDict


class TaskContext(TypedDict):
    description: str
    deadline: date | None
    r_name: str | None
    overdue: bool


def _format_decisions(decisions: Sequence[tuple[str, date]]) -> str:
    if not decisions:
        return "(brak zarejestrowanych decyzji dla tego tematu)"
    return "\n".join(f"- {statement} ({decided_on.isoformat()})" for statement, decided_on in decisions)


def _format_open_tasks(tasks: Sequence[TaskContext]) -> str:
    if not tasks:
        return "(brak otwartych zadań)"
    lines = []
    for t in tasks:
        overdue = " [PO TERMINIE]" if t["overdue"] else ""
        deadline = t["deadline"].isoformat() if t["deadline"] else "brak terminu"
        lines.append(f"- {t['description']} — R: {t['r_name'] or 'brak'}, termin: {deadline}{overdue}")
    return "\n".join(lines)


def _format_closed_tasks(tasks: Sequence[TaskContext]) -> str:
    if not tasks:
        return "(brak zamkniętych zadań od ostatniego spotkania)"
    return "\n".join(f"- {t['description']} — R: {t['r_name'] or 'brak'}" for t in tasks)


def build_briefing_prompt(
    *,
    topic_name: str,
    decisions: Sequence[tuple[str, date]],
    open_tasks: Sequence[TaskContext],
    closed_tasks: Sequence[TaskContext],
) -> str:
    return f"""Przygotuj krótką notatkę przed spotkaniem. Odbiorca: właściciel aplikacji.
Ma ją przeczytać w 30 sekund.

Temat/dostawca: {topic_name}
Ostatnie decyzje (chronologicznie):
{_format_decisions(decisions)}
Otwarte zadania:
{_format_open_tasks(open_tasks)}
Zadania zamknięte od ostatniego spotkania:
{_format_closed_tasks(closed_tasks)}

Struktura:
1. Jedno zdanie: na czym stanęło.
2. Ustalenia, do których trzeba wrócić (max 3).
3. Status zadań: kto zalega, kto skończył. Konkretnie, po nazwisku.
4. Jeśli coś wymaga decyzji na tym spotkaniu — wymień.

Ton rzeczowy. Bez wstępów typu „Oto Twój briefing". Zaczynaj od treści."""
