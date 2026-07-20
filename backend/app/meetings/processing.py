"""Orkiestracja przetwarzania spotkania (SPEC.md §4): transkrypcja audio,
sklejanie po part_index w backendzie, aktualizacja statusu.

Uruchamiane w tle przez FastAPI BackgroundTasks (POST /meetings/{id}/process).
Ekstrakcja zadań/decyzji to etap 5 — tutaj przetwarzanie kończy się na
status=analyzing, zgodnie z ETAPY.md (etap 4, punkt 7).
"""

from __future__ import annotations

import logging
import mimetypes
import os
import uuid

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.meetings.gemini_client import GeminiNotConfigured, TranscriptionError, transcribe_audio
from app.meetings.prompts import build_transcription_prompt
from app.meetings.storage import StorageError, StorageNotConfigured, download_object
from app.models import meeting, meeting_audio, person, transcript

logger = logging.getLogger(__name__)

_MIME_OVERRIDES = {
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".aac": "audio/aac",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}


def _mime_for(storage_path: str) -> str:
    ext = os.path.splitext(storage_path)[1].lower()
    return _MIME_OVERRIDES.get(ext, mimetypes.guess_type(storage_path)[0] or "application/octet-stream")


def _load_participants(db: Session) -> list[tuple[str, list[str]]]:
    rows = db.execute(
        select(person.c.full_name, person.c.aliases)
        .where(person.c.active.is_(True))
        .order_by(person.c.full_name)
    ).all()
    return [(row.full_name, list(row.aliases)) for row in rows]


def _upsert_transcript(db: Session, meeting_id: uuid.UUID, part_index: int, content: str) -> None:
    stmt = pg_insert(transcript).values(meeting_id=meeting_id, part_index=part_index, content=content)
    stmt = stmt.on_conflict_do_update(
        index_elements=[transcript.c.meeting_id, transcript.c.part_index],
        set_={"content": stmt.excluded.content},
    )
    db.execute(stmt)


def _set_status(db: Session, meeting_id: uuid.UUID, status: str, error_message: str | None = None) -> None:
    db.execute(
        update(meeting).where(meeting.c.id == meeting_id).values(status=status, error_message=error_message)
    )
    db.commit()


def run_processing(meeting_id: uuid.UUID) -> None:
    """Wywoływane przez BackgroundTasks — otwiera własną sesję DB (request-scoped
    jest już zamknięta, gdy to wystartuje)."""
    db = SessionLocal()
    try:
        _run(db, meeting_id)
    finally:
        db.close()


def _run(db: Session, meeting_id: uuid.UUID) -> None:
    row = db.execute(select(meeting.c.source_type).where(meeting.c.id == meeting_id)).mappings().one()
    try:
        if row["source_type"] == "audio":
            _transcribe_audio_parts(db, meeting_id)
        _set_status(db, meeting_id, "analyzing")
    except (StorageError, StorageNotConfigured, GeminiNotConfigured, TranscriptionError) as exc:
        logger.warning("Przetwarzanie spotkania %s nie powiodło się: %s", meeting_id, exc)
        db.rollback()
        _set_status(db, meeting_id, "failed", str(exc))
    except Exception as exc:
        logger.exception("Przetwarzanie spotkania %s nie powiodło się (nieoczekiwany błąd).", meeting_id)
        db.rollback()
        _set_status(db, meeting_id, "failed", f"Nieoczekiwany błąd: {exc}")


def _transcribe_audio_parts(db: Session, meeting_id: uuid.UUID) -> None:
    audio_rows = db.execute(
        select(meeting_audio.c.storage_path, meeting_audio.c.part_index)
        .where(meeting_audio.c.meeting_id == meeting_id)
        .order_by(meeting_audio.c.part_index)
    ).all()
    participants = _load_participants(db)
    prompt = build_transcription_prompt(participants)

    for audio_row in audio_rows:
        data = download_object(audio_row.storage_path)
        content = transcribe_audio(
            data,
            mime_type=_mime_for(audio_row.storage_path),
            display_name=f"meeting-{meeting_id}-part{audio_row.part_index}",
            prompt=prompt,
        )
        _upsert_transcript(db, meeting_id, audio_row.part_index, content)
        db.commit()
