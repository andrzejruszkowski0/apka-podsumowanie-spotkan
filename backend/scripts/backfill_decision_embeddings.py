"""Skrypt jednorazowy: dolicza embeddingi decyzjom zapisanym przed etapem 9
(SPEC.md §10.4, ETAPY.md etap 9 pkt 3) — bez tego wyszukiwanie semantyczne
(/decisions?q=) po prostu pomija starsze decyzje, bo `embedding is null`.

Uruchomienie (z katalogu backend/, z aktywnym venv i wypełnionym .env):
    python -m scripts.backfill_decision_embeddings
"""

from __future__ import annotations

import logging

from app.db import SessionLocal
from app.decisions.embeddings import backfill_missing_embeddings

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")


def main() -> None:
    db = SessionLocal()
    try:
        count = backfill_missing_embeddings(db)
        print(f"Uzupełniono embeddingi dla {count} decyzji.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
