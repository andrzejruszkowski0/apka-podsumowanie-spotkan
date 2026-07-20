"""Ekstrakcja zadań, RACI i decyzji z transkryptu (SPEC.md §4 część
ekstrakcyjna, §10.2, §10.3; ETAPY.md etap 5).

Przepływ:
  transkrypt (sklejony wg part_index) -> chunking -> faza MAP na każdym
  fragmencie -> (jeśli >1 fragment) faza REDUCE scalająca kandydatury ->
  rozwiązanie nazwisk resolverem z etapu 3 -> zapis task/task_raci/decision
  -> meeting.status = awaiting_review.

Ekran weryfikacji (etap 6) to osobny zakres — tu tylko zapisujemy dane,
z których ten ekran skorzysta.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.meetings.chunking import split_into_chunks
from app.meetings.extraction_schemas import (
    ExtractionResult,
    MergedDecision,
    MergedResult,
    MergedTask,
    RaciCandidate,
)
from app.meetings.gemini_client import extract_from_fragment, reduce_candidates
from app.meetings.prompts import build_map_prompt, build_reduce_prompt
from app.models import decision, meeting, person, task, task_raci, transcript
from app.resolver import PersonRecord, resolve_name

logger = logging.getLogger(__name__)

# Przy nierozwiązanym nazwisku w RACI/decyzji, ai_confidence jest obniżane
# do co najwyżej tej wartości (ETAPY.md etap 5 pkt 4: "ai_confidence obniżone").
# Ta sama wartość, co próg konfliktu w fazie REDUCE (§10.3 pkt 4) — spójne
# potraktowanie "sytuacji wymagającej ręcznej weryfikacji".
UNRESOLVED_CONFIDENCE_CAP = 0.4


def _load_transcript_text(db: Session, meeting_id: uuid.UUID) -> str:
    rows = (
        db.execute(
            select(transcript.c.content)
            .where(transcript.c.meeting_id == meeting_id)
            .order_by(transcript.c.part_index)
        )
        .scalars()
        .all()
    )
    return "\n\n".join(rows)


def _load_people(db: Session) -> list[PersonRecord]:
    rows = db.execute(
        select(person.c.id, person.c.full_name, person.c.aliases).where(person.c.active.is_(True))
    ).all()
    return [PersonRecord(id=str(row.id), full_name=row.full_name, aliases=list(row.aliases)) for row in rows]


def _run_map_reduce(meeting_id: uuid.UUID, full_text: str) -> MergedResult:
    chunks = split_into_chunks(full_text)

    if len(chunks) == 1:
        result: ExtractionResult = extract_from_fragment(build_map_prompt(chunks[0]), meeting_id, 0)
        return MergedResult(
            tasks=[MergedTask(**t.model_dump()) for t in result.tasks],
            decisions=[MergedDecision(**d.model_dump()) for d in result.decisions],
        )

    aggregate = ExtractionResult()
    for idx, chunk in enumerate(chunks):
        chunk_result = extract_from_fragment(build_map_prompt(chunk), meeting_id, idx)
        aggregate.tasks.extend(chunk_result.tasks)
        aggregate.decisions.extend(chunk_result.decisions)

    candidates_json = aggregate.model_dump_json()
    return reduce_candidates(build_reduce_prompt(candidates_json), meeting_id)


def _parse_deadline(raw: str | None, meeting_id: uuid.UUID) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        logger.warning(
            "Spotkanie %s: nieparsowalny deadline z ekstrakcji (%r) — zapisuję jako null.",
            meeting_id,
            raw,
        )
        return None


def _resolve_raci(
    raci: RaciCandidate, people: list[PersonRecord]
) -> tuple[dict[str, str | None], bool, list[str | None], list[str | None]]:
    """Zwraca (mapa roli -> person_id-lub-None dla R/A, flaga czy jakiekolwiek
    podane nazwisko nie zostało rozwiązane, lista wyników dla C, lista
    wyników dla I)."""
    any_unresolved = False
    resolved: dict[str, str | None] = {}

    if raci.R:
        resolved_r = resolve_name(raci.R, people)
        resolved["R"] = resolved_r
        any_unresolved = any_unresolved or resolved_r is None
    if raci.A:
        resolved_a = resolve_name(raci.A, people)
        resolved["A"] = resolved_a
        any_unresolved = any_unresolved or resolved_a is None

    resolved_c = [resolve_name(name, people) for name in raci.C]
    resolved_i = [resolve_name(name, people) for name in raci.I]
    any_unresolved = any_unresolved or any(r is None for r in resolved_c) or any(
        r is None for r in resolved_i
    )

    return resolved, any_unresolved, resolved_c, resolved_i


def _save_task(
    db: Session,
    meeting_row,
    candidate: MergedTask,
    people: list[PersonRecord],
) -> None:
    resolved_ra, any_unresolved, resolved_c, resolved_i = _resolve_raci(candidate.raci, people)
    confidence = candidate.confidence
    if any_unresolved:
        confidence = min(confidence, UNRESOLVED_CONFIDENCE_CAP)

    task_row = db.execute(
        task.insert()
        .values(
            meeting_id=meeting_row.id,
            topic_id=meeting_row.topic_id,
            description=candidate.description,
            deadline=_parse_deadline(candidate.deadline, meeting_row.id),
            ai_confidence=confidence,
            quote=candidate.quote,
            raci_raw=candidate.raci.model_dump(),
        )
        .returning(task.c.id)
    ).scalar_one()

    raci_rows = []
    r_id = resolved_ra.get("R")
    if r_id:
        raci_rows.append({"task_id": task_row, "person_id": uuid.UUID(r_id), "role": "R"})
    a_id = resolved_ra.get("A")
    if a_id:
        raci_rows.append({"task_id": task_row, "person_id": uuid.UUID(a_id), "role": "A"})
    for c_id in resolved_c:
        if c_id:
            raci_rows.append({"task_id": task_row, "person_id": uuid.UUID(c_id), "role": "C"})
    for i_id in resolved_i:
        if i_id:
            raci_rows.append({"task_id": task_row, "person_id": uuid.UUID(i_id), "role": "I"})

    if raci_rows:
        db.execute(task_raci.insert(), raci_rows)


def _save_decision(
    db: Session,
    meeting_row,
    candidate: MergedDecision,
    people: list[PersonRecord],
) -> None:
    decided_by_id = resolve_name(candidate.decided_by, people) if candidate.decided_by else None
    confidence = candidate.confidence
    if candidate.decided_by and decided_by_id is None:
        confidence = min(confidence, UNRESOLVED_CONFIDENCE_CAP)

    db.execute(
        decision.insert().values(
            meeting_id=meeting_row.id,
            topic_id=meeting_row.topic_id,
            statement=candidate.statement,
            decided_on=meeting_row.meeting_date,
            decided_by=uuid.UUID(decided_by_id) if decided_by_id else None,
            decided_by_raw=candidate.decided_by,
            category=candidate.category,
            quote=candidate.quote,
            ai_confidence=confidence,
        )
    )


def run_extraction(db: Session, meeting_id: uuid.UUID) -> None:
    meeting_row = db.execute(select(meeting).where(meeting.c.id == meeting_id)).one()
    full_text = _load_transcript_text(db, meeting_id)
    if not full_text.strip():
        raise ValueError(f"Spotkanie {meeting_id} nie ma transkryptu — nie ma czego ekstrahować.")

    merged = _run_map_reduce(meeting_id, full_text)
    people = _load_people(db)

    for task_candidate in merged.tasks:
        _save_task(db, meeting_row, task_candidate, people)
    for decision_candidate in merged.decisions:
        _save_decision(db, meeting_row, decision_candidate, people)

    db.execute(update(meeting).where(meeting.c.id == meeting_id).values(status="awaiting_review"))
    db.commit()
