"""Endpointy /briefing — notatka przed spotkaniem (SPEC.md §10.4, §9, etap 9).

SPEC.md §9 opisuje jeden endpoint ("POST /briefing → generuje i wysyła"), ale
ETAPY.md dla tego etapu wymaga wprost ekranu podglądu przed wysyłką ("Bez
automatycznej wysyłki") — ten sam guardrail, co przy zatwierdzaniu spotkania
(GET/PUT /review → dopiero POST /approve) i przy szablonach draftów (§10.5).
Stąd dwa endpointy zamiast jednego: /briefing/preview generuje treść i niczego
nie wysyła, /briefing/send wysyła dokładnie to, co zwrócił podgląd.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, require_user
from app.auth.tokens import get_valid_access_token
from app.briefing.service import TopicNotFound, generate_preview, send_briefing
from app.db import get_db
from app.meetings.gemini_client import BriefingError, GeminiNotConfigured
from app.notifications.gmail_client import GmailApiError

router = APIRouter(prefix="/briefing", tags=["briefing"])


class BriefingPreviewIn(BaseModel):
    topic_id: uuid.UUID


class BriefingSendIn(BaseModel):
    topic_id: uuid.UUID
    subject: str
    body: str


@router.post("/preview")
def preview_briefing(
    body: BriefingPreviewIn, user: CurrentUser = Depends(require_user), db: Session = Depends(get_db)
) -> dict:
    try:
        return generate_preview(db, body.topic_id)
    except TopicNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (GeminiNotConfigured, BriefingError) as exc:
        raise HTTPException(status_code=400, detail=f"Generowanie briefingu nie powiodło się: {exc}") from exc


@router.post("/send")
def send_briefing_endpoint(
    body: BriefingSendIn, user: CurrentUser = Depends(require_user), db: Session = Depends(get_db)
) -> dict:
    access_token = get_valid_access_token(db, user.id)
    try:
        return send_briefing(
            db,
            owner_email=user.email,
            access_token=access_token,
            topic_id=body.topic_id,
            subject=body.subject,
            body=body.body,
        )
    except TopicNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GmailApiError as exc:
        raise HTTPException(status_code=400, detail=f"Wysyłka briefingu nie powiodła się: {exc}") from exc
