"""Prompt transkrypcji + diaryzacji (SPEC.md §10.1)."""

from __future__ import annotations

from collections.abc import Sequence


def _format_participant(full_name: str, aliases: Sequence[str]) -> str:
    if not aliases:
        return f"- {full_name}"
    return f"- {full_name} (aliasy: {', '.join(aliases)})"


def build_transcription_prompt(participants: Sequence[tuple[str, Sequence[str]]]) -> str:
    people_lines = "\n".join(_format_participant(name, aliases) for name, aliases in participants)
    if not people_lines:
        people_lines = "(brak zarejestrowanych osób w bazie)"

    return f"""Jesteś systemem transkrypcji. Otrzymujesz nagranie spotkania biznesowego
w języku polskim.

Uczestnicy spotkania (możliwi mówcy):
{people_lines}

Zadanie:
1. Transkrybuj całość wiernie, po polsku.
2. Oznacz zmiany mówcy w formacie: [Imię Nazwisko]: treść
3. Jeśli nie potrafisz przypisać wypowiedzi do konkretnej osoby z listy,
   użyj [Mówca 1], [Mówca 2] — konsekwentnie dla tego samego głosu.
4. NIE streszczaj, NIE poprawiaj stylu. Zachowaj to, co faktycznie padło.
5. Znaczniki czasu co ~2 minuty w formacie (mm:ss).

Zwróć wyłącznie transkrypt."""
