"""napraw znaleziska Supabase Advisor: RLS na alembic_version, indeksy FK

Alembic tworzy tabelę `alembic_version` sam dla siebie (śledzenie wersji
migracji) — nie była na liście TABLES w migracji 0001, więc nigdy nie
dostała RLS + polityki deny-all dla `anon`, mimo że SPEC.md §2 wymaga tego
"na wszystkich tabelach". Supabase oznaczał to jako CRITICAL.

Reszta: Postgres NIE indeksuje automatycznie kolumn kluczy obcych (w
odróżnieniu od kluczy głównych) — bez indeksu każdy JOIN/DELETE po tej
kolumnie robi sekwencyjny skan całej tabeli. Dodaję indeks na każdej
kolumnie FK, która nie jest już wiodącą kolumną innego indeksu:
  - meeting_audio.meeting_id i transcript.meeting_id POMINIĘTE celowo —
    obie są już wiodącą kolumną istniejącego unique(meeting_id, part_index),
    co Postgres wykorzystuje tak samo jak zwykły indeks przy filtrowaniu
    po samym meeting_id.
  - task_raci.task_id POMINIĘTE — wiodąca kolumna primary key
    (task_id, person_id, role).

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-21

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_INDEXES = [
    ("ix_meeting_user_id", "meeting", "user_id"),
    ("ix_meeting_topic_id", "meeting", "topic_id"),
    ("ix_task_meeting_id", "task", "meeting_id"),
    ("ix_task_topic_id", "task", "topic_id"),
    ("ix_task_raci_person_id", "task_raci", "person_id"),
    ("ix_decision_meeting_id", "decision", "meeting_id"),
    ("ix_decision_topic_id", "decision", "topic_id"),
    ("ix_decision_decided_by", "decision", "decided_by"),
    ("ix_notification_log_task_id", "notification_log", "task_id"),
    ("ix_notification_log_meeting_id", "notification_log", "meeting_id"),
]


def upgrade() -> None:
    op.execute("alter table alembic_version enable row level security")
    op.execute(
        """
        create policy deny_all_anon on alembic_version
        for all to anon using (false) with check (false)
        """
    )

    for name, table, column in _INDEXES:
        op.execute(f"create index {name} on {table} ({column})")


def downgrade() -> None:
    for name, _table, _column in reversed(_INDEXES):
        op.execute(f"drop index if exists {name}")

    op.execute("drop policy if exists deny_all_anon on alembic_version")
    op.execute("alter table alembic_version disable row level security")
