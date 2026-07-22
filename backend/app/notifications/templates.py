"""Szablon maila przypomnienia o zadaniu (SPEC.md §7, etap 8).

Zwięzły z założenia: zadanie, deadline, temat, link do panelu — bez ozdobników.
"""

from __future__ import annotations

from datetime import date

from app.config import settings

_MAX_SUBJECT_DESCRIPTION_LEN = 60


def reminder_subject(description: str) -> str:
    short = description if len(description) <= _MAX_SUBJECT_DESCRIPTION_LEN else description[:57] + "..."
    return f"Przypomnienie: {short}"


def reminder_body(*, description: str, deadline: date, topic_name: str | None) -> str:
    return (
        f"Zadanie: {description}\n"
        f"Termin: {deadline.isoformat()}\n"
        f"Temat: {topic_name or '—'}\n"
        "\n"
        f"Panel: {settings.frontend_origin}/tasks"
    )
