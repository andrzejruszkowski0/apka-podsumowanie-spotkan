"""FastAPI dependency chroniąca endpointy — wymaga zalogowanego użytkownika."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import app_user


@dataclass
class CurrentUser:
    id: uuid.UUID
    email: str
    display_name: str | None


def require_user(request: Request, db: Session = Depends(get_db)) -> CurrentUser:
    raw_user_id = request.session.get("user_id")
    if not raw_user_id:
        raise HTTPException(status_code=401, detail="Wymagane logowanie (/auth/login).")

    row = db.execute(select(app_user).where(app_user.c.id == uuid.UUID(raw_user_id))).mappings().first()
    if row is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Wymagane logowanie (/auth/login).")

    return CurrentUser(id=row["id"], email=row["email"], display_name=row["display_name"])
