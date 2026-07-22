from datetime import date

from app.briefing.prompts import (
    TaskContext,
    _format_closed_tasks,
    _format_decisions,
    _format_open_tasks,
    build_briefing_prompt,
)


def test_format_decisions_empty_uses_placeholder():
    assert _format_decisions([]) == "(brak zarejestrowanych decyzji dla tego tematu)"


def test_format_decisions_lists_statement_and_date():
    text = _format_decisions([("Dostawca X zgadza się na rabat 3%", date(2026, 7, 1))])
    assert text == "- Dostawca X zgadza się na rabat 3% (2026-07-01)"


def test_format_open_tasks_empty_uses_placeholder():
    assert _format_open_tasks([]) == "(brak otwartych zadań)"


def test_format_open_tasks_marks_overdue():
    tasks: list[TaskContext] = [
        TaskContext(description="Wyślij raport", deadline=date(2026, 7, 1), r_name="Jan Kowalski", overdue=True)
    ]
    text = _format_open_tasks(tasks)
    assert "Wyślij raport" in text
    assert "R: Jan Kowalski" in text
    assert "[PO TERMINIE]" in text


def test_format_open_tasks_handles_missing_r_and_deadline():
    tasks: list[TaskContext] = [TaskContext(description="Coś zrobić", deadline=None, r_name=None, overdue=False)]
    text = _format_open_tasks(tasks)
    assert "R: brak" in text
    assert "brak terminu" in text
    assert "[PO TERMINIE]" not in text


def test_format_closed_tasks_empty_uses_placeholder():
    assert _format_closed_tasks([]) == "(brak zamkniętych zadań od ostatniego spotkania)"


def test_format_closed_tasks_lists_description_and_r():
    tasks: list[TaskContext] = [TaskContext(description="Wysłano ofertę", deadline=None, r_name="Anna Nowak", overdue=False)]
    assert _format_closed_tasks(tasks) == "- Wysłano ofertę — R: Anna Nowak"


def test_build_briefing_prompt_contains_all_sections():
    prompt = build_briefing_prompt(
        topic_name="Dostawca X",
        decisions=[("Ustalono rabat 3%", date(2026, 7, 1))],
        open_tasks=[TaskContext(description="Wyślij umowę", deadline=date(2026, 8, 1), r_name="Jan", overdue=False)],
        closed_tasks=[TaskContext(description="Podpisano NDA", deadline=None, r_name="Anna", overdue=False)],
    )
    assert "Temat/dostawca: Dostawca X" in prompt
    assert "Ustalono rabat 3%" in prompt
    assert "Wyślij umowę" in prompt
    assert "Podpisano NDA" in prompt
