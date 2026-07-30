"""Skrypt jednorazowy: wypełnia bazę syntetycznymi rekordami testowymi
(person, topic, meeting, task, task_raci, decision) do ręcznego testowania
API i frontendu bez użycia prawdziwych danych biznesowych.

Dane są w pełni fikcyjne i deterministyczne:
- e-maile w domenie example.com (zarezerwowanej pod dokumentację/testy,
  RFC 2606) w formacie imie.nazwisko@example.com — gwarancja braku kolizji
  z prawdziwym adresem i czytelny format do wizualnej weryfikacji w Supabase
  Studio,
- wszystkie UUID generowane przez uuid4() (jak w resztę aplikacji —
  server_default=func.gen_random_uuid() w app/models.py), bez ręcznie
  wpisywanych identyfikatorów,
- stały seed random (SEED = 20260722) — powtarzalny zestaw danych między
  uruchomieniami, ułatwia debugowanie ("dlaczego test X przeszedł wczoraj,
  a dziś nie" przestaje być pytaniem o losowość danych),
- unikalność email (person.email UNIQUE) i name (topic.name UNIQUE)
  wymuszona już na poziomie generatora (nie liczymy na to, że baza odrzuci
  duplikat) — patrz _unique_email()/_unique_topic_name().

Uruchomienie (z katalogu backend/, z aktywnym venv i wypełnionym .env
wskazującym na środowisko DEV/staging Supabase — NIGDY na produkcję):
    python -m scripts.seed_test_data
"""

from __future__ import annotations

import random
import uuid
from datetime import date, timedelta

from sqlalchemy import text

from app.db import SessionLocal
from app.models import decision, meeting, person, task, task_raci, topic

SEED = 20260722
random.seed(SEED)

FIRST_NAMES = ["Jan", "Anna", "Piotr", "Katarzyna", "Michał", "Ola", "Tomasz", "Barbara"]
LAST_NAMES = ["Kowalski", "Nowak", "Wiśniewska", "Wójcik", "Zielińska", "Duda", "Baran", "Malinowska"]
ORGS = ["Synthetic Test Co", "Fikcyjny Dostawca Sp. z o.o.", None]
TOPIC_KINDS = ["project", "supplier", "internal"]

_used_emails: set[str] = set()
_used_topic_names: set[str] = set()


def _unique_email(first: str, last: str) -> str:
    """imie.nazwisko@example.com; przy kolizji dokleja licznik (.2, .3, ...)."""
    base = f"{first}.{last}".lower().replace("ł", "l").replace("ń", "n").replace("ó", "o")
    candidate = f"{base}@example.com"
    n = 2
    while candidate in _used_emails:
        candidate = f"{base}.{n}@example.com"
        n += 1
    _used_emails.add(candidate)
    return candidate


def _unique_topic_name(base: str) -> str:
    candidate = base
    n = 2
    while candidate in _used_topic_names:
        candidate = f"{base} ({n})"
        n += 1
    _used_topic_names.add(candidate)
    return candidate


def make_people(n: int) -> list[dict]:
    rows = []
    for _ in range(n):
        first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        rows.append(
            {
                "id": uuid.uuid4(),
                "full_name": f"{first} {last}",
                "email": _unique_email(first, last),
                "aliases": [],
                "org": random.choice(ORGS),
                "active": True,
            }
        )
    return rows


def make_topics(n: int) -> list[dict]:
    rows = []
    for i in range(n):
        rows.append(
            {
                "id": uuid.uuid4(),
                "name": _unique_topic_name(f"Temat testowy {i + 1}"),
                "kind": random.choice(TOPIC_KINDS),
                "notes": "Rekord syntetyczny — wygenerowany przez scripts/seed_test_data.py",
            }
        )
    return rows


def make_meetings(n: int, user_id: uuid.UUID, topics: list[dict]) -> list[dict]:
    rows = []
    for i in range(n):
        rows.append(
            {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "topic_id": random.choice(topics)["id"] if topics else None,
                "title": f"Spotkanie testowe #{i + 1}",
                "meeting_date": date.today() - timedelta(days=random.randint(0, 30)),
                "source_type": random.choice(["audio", "text"]),
                "status": "approved",
            }
        )
    return rows


def make_tasks_and_raci(meetings_: list[dict], people: list[dict], per_meeting: int) -> tuple[list[dict], list[dict]]:
    tasks, raci = [], []
    for m in meetings_:
        for i in range(per_meeting):
            task_id = uuid.uuid4()
            tasks.append(
                {
                    "id": task_id,
                    "meeting_id": m["id"],
                    "topic_id": m["topic_id"],
                    "description": f"Zadanie testowe {i + 1} ze spotkania '{m['title']}'",
                    "deadline": date.today() + timedelta(days=random.randint(1, 14)),
                    "status": "open",
                    "edited_by_user": False,
                }
            )
            responsible = random.choice(people)
            raci.append({"task_id": task_id, "person_id": responsible["id"], "role": "R"})
    return tasks, raci


def make_decisions(meetings_: list[dict], people: list[dict], per_meeting: int) -> list[dict]:
    rows = []
    for m in meetings_:
        for i in range(per_meeting):
            rows.append(
                {
                    "id": uuid.uuid4(),
                    "meeting_id": m["id"],
                    "topic_id": m["topic_id"],
                    "statement": f"Decyzja testowa {i + 1} ze spotkania '{m['title']}'",
                    "decided_on": m["meeting_date"],
                    "decided_by": random.choice(people)["id"],
                    "category": None,
                }
            )
    return rows


def main() -> None:
    db = SessionLocal()
    try:
        existing_user_id = db.execute(text("SELECT id FROM app_user LIMIT 1")).scalar()
        if existing_user_id is None:
            raise RuntimeError(
                "Brak app_user w bazie — seed testowy zakłada zalogowanie się "
                "raz przez Google OAuth przed uruchomieniem (auth.py). Nie "
                "tworzymy syntetycznego app_user, bo ten rekord jest powiązany "
                "z prawdziwym kontem Google i tokenami OAuth."
            )

        people = make_people(8)
        topics = make_topics(3)
        meetings_ = make_meetings(5, existing_user_id, topics)
        tasks, raci = make_tasks_and_raci(meetings_, people, per_meeting=2)
        decisions = make_decisions(meetings_, people, per_meeting=1)

        db.execute(person.insert(), people)
        db.execute(topic.insert(), topics)
        db.execute(meeting.insert(), meetings_)
        db.execute(task.insert(), tasks)
        db.execute(task_raci.insert(), raci)
        db.execute(decision.insert(), decisions)
        db.commit()

        print(
            f"Wstawiono: {len(people)} person, {len(topics)} topic, "
            f"{len(meetings_)} meeting, {len(tasks)} task, {len(raci)} task_raci, "
            f"{len(decisions)} decision."
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
