"""Endpointy /people i /people/sync (SPEC.md §5, §9)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, require_user
from app.auth.tokens import get_valid_access_token
from app.db import get_db
from app.models import person
from app.people.sheets_client import SheetsApiError
from app.people.sync import PeopleSyncNotConfigured, sync_people_from_sheet

router = APIRouter(tags=["people"])


@router.post("/people/sync")
def trigger_sync(
    user: CurrentUser = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, int]:
    access_token = get_valid_access_token(db, user.id)
    try:
        result = sync_people_from_sheet(db, access_token)
    except (PeopleSyncNotConfigured, SheetsApiError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"upserted": result.upserted, "deactivated": result.deactivated}


@router.get("/people")
def list_people(
    user: CurrentUser = Depends(require_user), db: Session = Depends(get_db)
) -> list[dict]:
    rows = db.execute(
        select(person).where(person.c.active.is_(True)).order_by(person.c.full_name)
    ).mappings().all()
    return [
        {
            "id": str(row["id"]),
            "full_name": row["full_name"],
            "email": row["email"],
            "aliases": list(row["aliases"]),
            "org": row["org"],
        }
        for row in rows
    ]
