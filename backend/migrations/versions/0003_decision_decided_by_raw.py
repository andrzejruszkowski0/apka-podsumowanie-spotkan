"""decision.decided_by_raw (etap 6)

Ten sam problem, co task.raci_raw z migracji 0002: `decision.decided_by`
przechowuje wyłącznie rozwiązany person_id (albo null), więc po nieudanej
próbie rozwiązania nazwiska tracimy informację, KOGO AI w ogóle wskazało.
Ekran weryfikacji (etap 6) musi umieć odróżnić „AI nie wskazało nikogo" od
„AI wskazało kogoś, ale resolver się pomylił" — to drugie blokuje
zatwierdzenie i wymaga ręcznego wyboru z listy osób.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("decision", sa.Column("decided_by_raw", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("decision", "decided_by_raw")
