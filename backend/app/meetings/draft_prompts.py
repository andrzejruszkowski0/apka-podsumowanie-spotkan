"""Prompty szablonów maili podsumowujących (SPEC.md §10.5, ETAPY.md etap 10).

Trzy warianty, jeden budowniczy promptu z parametrem `template`. Wariant
`supplier` NIE dostaje w ogóle danych o zadaniach (task_raci) w kontekście —
to one są w tym systemie "zadaniami własnymi" (przypisanymi do R/A z tabeli
person), więc jedyny bezpieczny sposób na dotrzymanie wymogu "wewnętrzne
uwagi i zadania własne pominięte" (ETAPY.md pkt 2) to nie wysyłać ich do
Gemini w ogóle — instrukcja w prompcie to za mało, gdyby dane tam trafiły.
Decyzje (`decision.statement`) to z definicji ustalenia, więc dla dostawcy
zostają.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Literal, TypedDict

Template = Literal["formal_board", "supplier", "team_casual"]

SUBJECT_LABELS: dict[Template, str] = {
    "formal_board": "Raport ze spotkania",
    "supplier": "Podsumowanie spotkania",
    "team_casual": "Notatka ze spotkania",
}


class DraftDecisionContext(TypedDict):
    statement: str
    decided_on: date
    decided_by_name: str | None
    category: str | None


class DraftTaskContext(TypedDict):
    description: str
    deadline: date | None
    status: str
    r_name: str | None
    a_name: str | None


_TEMPLATE_INSTRUCTIONS: dict[Template, str] = {
    "formal_board": """Wariant: raport dla zarządu (formal_board).
Struktura:
1. Cel spotkania — jedno zdanie.
2. Ustalenia — najważniejsze decyzje, zwięźle.
3. Ryzyka — co może się nie udać albo wymaga uwagi (np. zadania po terminie,
   nierozstrzygnięte kwestie). Wywnioskuj je z danych poniżej, nie zmyślaj
   nowych.
4. Wymagane decyzje — co zarząd musi jeszcze rozstrzygnąć.
Ton: bezosobowy, zwięzły, bez potocznych sformułowań.""",
    "supplier": """Wariant: oficjalne podsumowanie dla dostawcy (supplier).
Zawiera WYŁĄCZNIE ustalenia z sekcji „Ustalenia” poniżej — to jedyne dane,
jakie dostałeś, więc nie masz jak wspomnieć o niczym innym. Nie zgaduj i nie
dopisuj żadnych zadań, osób odpowiedzialnych ani wewnętrznych uwag.
Ton: uprzejmy, oficjalny, wiążący — dostawca ma móc się na to podsumowanie
powołać.""",
    "team_casual": """Wariant: wiadomość robocza dla zespołu (team_casual).
Struktura: lista zadań — kto, co, do kiedy. Bezpośrednio, bez zbędnych
wstępów. Wspomnij krótko kluczowe ustalenia, jeśli mają znaczenie dla
wykonania zadań.
Ton: swobodny, roboczy (np. „Cześć zespół,”).""",
}


def _format_decisions(decisions: Sequence[DraftDecisionContext]) -> str:
    if not decisions:
        return "(brak zarejestrowanych decyzji na tym spotkaniu)"
    lines = []
    for d in decisions:
        by = f", zdecydował: {d['decided_by_name']}" if d["decided_by_name"] else ""
        category = f" [{d['category']}]" if d["category"] else ""
        lines.append(f"- {d['statement']} ({d['decided_on'].isoformat()}{by}){category}")
    return "\n".join(lines)


def _format_tasks(tasks: Sequence[DraftTaskContext]) -> str:
    if not tasks:
        return "(brak zadań ustalonych na tym spotkaniu)"
    lines = []
    for t in tasks:
        deadline = t["deadline"].isoformat() if t["deadline"] else "brak terminu"
        r = t["r_name"] or "brak"
        a = f", odpowiedzialny: {t['a_name']}" if t["a_name"] else ""
        lines.append(f"- {t['description']} — wykonawca: {r}{a}, termin: {deadline}, status: {t['status']}")
    return "\n".join(lines)


def build_draft_prompt(
    *,
    template: Template,
    meeting_title: str,
    meeting_date: date,
    topic_name: str | None,
    decisions: Sequence[DraftDecisionContext],
    tasks: Sequence[DraftTaskContext],
) -> str:
    sections = [
        "Przygotuj SZKIC maila podsumowującego spotkanie. To wyłącznie szkic —"
        " nie jest wysyłany automatycznie, właściciel przeczyta go i będzie mógł"
        " poprawić przed wysyłką.",
        "",
        f"Spotkanie: {meeting_title} ({meeting_date.isoformat()})",
        f"Temat/dostawca: {topic_name or 'brak'}",
        "",
        "Ustalenia (decyzje z tego spotkania):",
        _format_decisions(decisions),
    ]
    if template != "supplier":
        sections += [
            "",
            "Zadania ustalone na tym spotkaniu:",
            _format_tasks(tasks),
        ]
    sections += [
        "",
        _TEMPLATE_INSTRUCTIONS[template],
        "",
        "Zwróć wyłącznie treść maila — bez tematu, bez markdown, gotowe do wysłania.",
    ]
    return "\n".join(sections)


def build_subject(template: Template, meeting_title: str) -> str:
    return f"{SUBJECT_LABELS[template]}: {meeting_title}"
