from datetime import date

from app.meetings.draft_prompts import (
    DraftDecisionContext,
    DraftTaskContext,
    _format_decisions,
    _format_tasks,
    build_draft_prompt,
    build_subject,
)


def _decision(**overrides) -> DraftDecisionContext:
    base: DraftDecisionContext = {
        "statement": "Dostawca X zgadza się na rabat 3%",
        "decided_on": date(2026, 7, 1),
        "decided_by_name": None,
        "category": None,
    }
    base.update(overrides)
    return base


def _task(**overrides) -> DraftTaskContext:
    base: DraftTaskContext = {
        "description": "Wyślij ofertę",
        "deadline": date(2026, 7, 10),
        "status": "open",
        "r_name": "Jan Kowalski",
        "a_name": None,
    }
    base.update(overrides)
    return base


def test_format_decisions_empty_uses_placeholder():
    assert _format_decisions([]) == "(brak zarejestrowanych decyzji na tym spotkaniu)"


def test_format_decisions_includes_statement_date_and_who_decided():
    text = _format_decisions([_decision(decided_by_name="Anna Nowak", category="cena")])
    assert "Dostawca X zgadza się na rabat 3%" in text
    assert "2026-07-01" in text
    assert "zdecydował: Anna Nowak" in text
    assert "[cena]" in text


def test_format_tasks_empty_uses_placeholder():
    assert _format_tasks([]) == "(brak zadań ustalonych na tym spotkaniu)"


def test_format_tasks_includes_r_a_deadline_and_status():
    text = _format_tasks([_task(a_name="Anna Nowak")])
    assert "Wyślij ofertę" in text
    assert "wykonawca: Jan Kowalski" in text
    assert "odpowiedzialny: Anna Nowak" in text
    assert "2026-07-10" in text
    assert "status: open" in text


def test_format_tasks_handles_missing_r_and_deadline():
    text = _format_tasks([_task(r_name=None, deadline=None)])
    assert "wykonawca: brak" in text
    assert "brak terminu" in text


def test_build_subject_varies_per_template():
    subjects = {
        build_subject("formal_board", "Spotkanie z Dostawcą X"),
        build_subject("supplier", "Spotkanie z Dostawcą X"),
        build_subject("team_casual", "Spotkanie z Dostawcą X"),
    }
    assert len(subjects) == 3
    assert all("Spotkanie z Dostawcą X" in s for s in subjects)


def test_supplier_prompt_never_receives_task_data_even_if_passed():
    # Nawet gdyby wywołujący przez pomyłkę przekazał zadania do wariantu
    # supplier, build_draft_prompt ich nie umieszcza w treści promptu — to
    # jedyne twarde zabezpieczenie przed wyciekiem "zadań własnych" (patrz
    # docstring draft_prompts.py).
    prompt = build_draft_prompt(
        template="supplier",
        meeting_title="Spotkanie z Dostawcą X",
        meeting_date=date(2026, 7, 1),
        topic_name="Dostawca X",
        decisions=[_decision()],
        tasks=[_task(description="TAJNE_ZADANIE_WEWNETRZNE")],
    )
    assert "TAJNE_ZADANIE_WEWNETRZNE" not in prompt
    assert "Zadania ustalone" not in prompt
    assert "Dostawca X zgadza się na rabat 3%" in prompt


def test_formal_board_and_team_casual_prompts_include_tasks():
    for template in ("formal_board", "team_casual"):
        prompt = build_draft_prompt(
            template=template,
            meeting_title="Spotkanie wewnętrzne",
            meeting_date=date(2026, 7, 1),
            topic_name=None,
            decisions=[_decision()],
            tasks=[_task()],
        )
        assert "Wyślij ofertę" in prompt


def test_build_draft_prompt_contains_template_specific_instructions():
    prompt_board = build_draft_prompt(
        template="formal_board",
        meeting_title="Spotkanie",
        meeting_date=date(2026, 7, 1),
        topic_name=None,
        decisions=[],
        tasks=[],
    )
    prompt_team = build_draft_prompt(
        template="team_casual",
        meeting_title="Spotkanie",
        meeting_date=date(2026, 7, 1),
        topic_name=None,
        decisions=[],
        tasks=[],
    )
    assert prompt_board != prompt_team
    assert "raport dla zarządu" in prompt_board
    assert "wiadomość robocza" in prompt_team
