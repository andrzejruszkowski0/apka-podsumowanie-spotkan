"""Endpointy /meetings — upload i transkrypcja (SPEC.md §4, §9, etap 4),
ekstrakcja (etap 5) oraz ekran weryfikacji (SPEC.md §11, etap 6).

Zapis do Sheets po zatwierdzeniu to etap 7 — poza zakresem tego modułu.
"""

from __future__ import annotations

import os
import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, require_user
from app.db import get_db
from app.meetings.processing import run_processing
from app.meetings.review import ReviewUpdateIn, any_unresolved, apply_review_update, get_review_payload
from app.meetings.storage import StorageError, StorageNotConfigured, upload_object
from app.models import meeting, meeting_audio, transcript

router = APIRouter(prefix="/meetings", tags=["meetings"])

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac"}

_MIME_BY_EXT = {
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".wav": "audio/wav",
    ".aac": "audio/aac",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}

_PROCESSABLE_STATUSES = {"uploaded", "failed"}


class MeetingIn(BaseModel):
    title: str
    meeting_date: date
    topic_id: uuid.UUID | None = None
    source_type: Literal["audio", "text"]


class TextIn(BaseModel):
    content: str


def _serialize_meeting(row) -> dict:
    return {
        "id": str(row["id"]),
        "topic_id": str(row["topic_id"]) if row["topic_id"] else None,
        "title": row["title"],
        "meeting_date": row["meeting_date"].isoformat(),
        "source_type": row["source_type"],
        "status": row["status"],
        "error_message": row["error_message"],
        "created_at": row["created_at"].isoformat(),
    }


def _get_owned_meeting(db: Session, meeting_id: uuid.UUID, user_id: uuid.UUID) -> dict:
    row = (
        db.execute(select(meeting).where(meeting.c.id == meeting_id, meeting.c.user_id == user_id))
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Spotkanie nie istnieje.")
    return dict(row)


@router.post("")
def create_meeting(
    body: MeetingIn, user: CurrentUser = Depends(require_user), db: Session = Depends(get_db)
) -> dict:
    result = db.execute(
        meeting.insert()
        .values(
            user_id=user.id,
            topic_id=body.topic_id,
            title=body.title,
            meeting_date=body.meeting_date,
            source_type=body.source_type,
        )
        .returning(meeting)
    )
    row = result.mappings().one()
    db.commit()
    return _serialize_meeting(row)


@router.post("/{meeting_id}/audio")
async def upload_audio(
    meeting_id: uuid.UUID,
    files: list[UploadFile] = File(...),
    part_index: list[int] = Form(...),
    user: CurrentUser = Depends(require_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    row = _get_owned_meeting(db, meeting_id, user.id)
    if row["source_type"] != "audio":
        raise HTTPException(status_code=400, detail="Spotkanie nie jest typu audio.")
    if len(files) != len(part_index):
        raise HTTPException(
            status_code=400, detail="Liczba plików i wartości part_index musi się zgadzać."
        )

    created = []
    for file, idx in zip(files, part_index):
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in ALLOWED_AUDIO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Niedozwolone rozszerzenie pliku „{file.filename}”. "
                f"Akceptowane: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}.",
            )
        data = await file.read()
        storage_path = f"{meeting_id}/{idx}{ext}"
        try:
            upload_object(storage_path, data, _MIME_BY_EXT[ext])
        except (StorageError, StorageNotConfigured) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        stmt = pg_insert(meeting_audio).values(
            meeting_id=meeting_id,
            storage_path=storage_path,
            part_index=idx,
            bytes=len(data),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[meeting_audio.c.meeting_id, meeting_audio.c.part_index],
            set_={"storage_path": stmt.excluded.storage_path, "bytes": stmt.excluded.bytes},
        ).returning(meeting_audio)
        created_row = db.execute(stmt).mappings().one()
        created.append(created_row)

    db.commit()
    return [
        {
            "id": str(r["id"]),
            "storage_path": r["storage_path"],
            "part_index": r["part_index"],
            "bytes": r["bytes"],
        }
        for r in created
    ]


@router.post("/{meeting_id}/text")
def upload_text(
    meeting_id: uuid.UUID,
    body: TextIn,
    user: CurrentUser = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict:
    row = _get_owned_meeting(db, meeting_id, user.id)
    if row["source_type"] != "text":
        raise HTTPException(status_code=400, detail="Spotkanie nie jest typu tekstowego.")
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Treść nie może być pusta.")

    stmt = pg_insert(transcript).values(meeting_id=meeting_id, part_index=0, content=body.content)
    stmt = stmt.on_conflict_do_update(
        index_elements=[transcript.c.meeting_id, transcript.c.part_index],
        set_={"content": stmt.excluded.content},
    ).returning(transcript)
    created_row = db.execute(stmt).mappings().one()
    db.commit()
    return {"part_index": created_row["part_index"], "content": created_row["content"]}


@router.post("/{meeting_id}/process", status_code=202)
def process_meeting(
    meeting_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict:
    row = _get_owned_meeting(db, meeting_id, user.id)
    if row["status"] not in _PROCESSABLE_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Spotkanie w stanie „{row['status']}” nie może zostać ponownie przetworzone.",
        )

    if row["source_type"] == "audio":
        count = db.execute(
            select(func.count()).select_from(meeting_audio).where(meeting_audio.c.meeting_id == meeting_id)
        ).scalar_one()
        if count == 0:
            raise HTTPException(status_code=400, detail="Brak wgranych plików audio.")
    else:
        exists = db.execute(
            select(transcript.c.id).where(
                transcript.c.meeting_id == meeting_id, transcript.c.part_index == 0
            )
        ).first()
        if exists is None:
            raise HTTPException(status_code=400, detail="Brak wklejonego tekstu.")

    db.execute(
        update(meeting)
        .where(meeting.c.id == meeting_id)
        .values(status="transcribing", error_message=None)
    )
    db.commit()

    background_tasks.add_task(run_processing, meeting_id)
    return {"status": "transcribing"}


@router.get("/{meeting_id}")
def get_meeting(
    meeting_id: uuid.UUID, user: CurrentUser = Depends(require_user), db: Session = Depends(get_db)
) -> dict:
    row = _get_owned_meeting(db, meeting_id, user.id)
    parts = (
        db.execute(
            select(transcript.c.part_index, transcript.c.content)
            .where(transcript.c.meeting_id == meeting_id)
            .order_by(transcript.c.part_index)
        )
        .mappings()
        .all()
    )
    return {
        **_serialize_meeting(row),
        "transcript_parts": [{"part_index": p["part_index"], "content": p["content"]} for p in parts],
        "transcript": "\n\n".join(p["content"] for p in parts),
    }


@router.get("")
def list_meetings(
    status: str | None = None,
    topic_id: uuid.UUID | None = None,
    user: CurrentUser = Depends(require_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(meeting).where(meeting.c.user_id == user.id)
    if status:
        query = query.where(meeting.c.status == status)
    if topic_id:
        query = query.where(meeting.c.topic_id == topic_id)
    rows = db.execute(query.order_by(meeting.c.created_at.desc())).mappings().all()
    return [_serialize_meeting(row) for row in rows]


@router.get("/{meeting_id}/review")
def get_review(
    meeting_id: uuid.UUID, user: CurrentUser = Depends(require_user), db: Session = Depends(get_db)
) -> dict:
    _get_owned_meeting(db, meeting_id, user.id)
    return get_review_payload(db, meeting_id)


@router.put("/{meeting_id}/review")
def put_review(
    meeting_id: uuid.UUID,
    body: ReviewUpdateIn,
    user: CurrentUser = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict:
    row = _get_owned_meeting(db, meeting_id, user.id)
    if row["status"] != "awaiting_review":
        raise HTTPException(
            status_code=409,
            detail=f"Spotkanie w stanie „{row['status']}” nie jest w trakcie weryfikacji.",
        )
    apply_review_update(db, meeting_id, body)
    return get_review_payload(db, meeting_id)


@router.post("/{meeting_id}/approve")
def approve_meeting(
    meeting_id: uuid.UUID, user: CurrentUser = Depends(require_user), db: Session = Depends(get_db)
) -> dict:
    row = _get_owned_meeting(db, meeting_id, user.id)
    if row["status"] != "awaiting_review":
        raise HTTPException(
            status_code=409,
            detail=f"Spotkanie w stanie „{row['status']}” nie może zostać zatwierdzone.",
        )
    if any_unresolved(db, meeting_id):
        raise HTTPException(
            status_code=400,
            detail="Są nierozwiązane nazwiska w zadaniach lub decyzjach — popraw je przed zatwierdzeniem.",
        )

    db.execute(update(meeting).where(meeting.c.id == meeting_id).values(status="approved"))
    db.commit()
    return _serialize_meeting(
        db.execute(select(meeting).where(meeting.c.id == meeting_id)).mappings().one()
    )
