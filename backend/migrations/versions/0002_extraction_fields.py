"""extraction fields (etap 5)

SPEC.md §10.2/§10.3 każe wyciągać `quote` (cytat uzasadniający) dla zadań
i decyzji oraz confidence dla decyzji, ale §2 nie przewiduje dla nich kolumn.
Bez tego etap 6 (ekran weryfikacji) nie miałby jak pokazać cytatu ani
wyróżnić decyzji o niskiej pewności — a tych danych nie da się odtworzyć
później bez ponownego wywołania AI. Stąd minimalne, addytywne rozszerzenie.

Analogicznie: task_raci.person_id jest NOT NULL, więc nierozwiązanego
nazwiska („Janek" bez dopasowania w person) nie da się tam zapisać wprost.
task.raci_raw przechowuje surowe {R, A, C, I} z ekstrakcji — ekran
weryfikacji porówna je z faktycznymi wierszami task_raci, żeby wykryć
braki i zaproponować ręczny wybór.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("task", sa.Column("quote", sa.Text(), nullable=True))
    op.add_column("task", sa.Column("raci_raw", postgresql.JSONB(), nullable=True))
    op.add_column("decision", sa.Column("quote", sa.Text(), nullable=True))
    op.add_column("decision", sa.Column("ai_confidence", sa.REAL(), nullable=True))


def downgrade() -> None:
    op.drop_column("decision", "ai_confidence")
    op.drop_column("decision", "quote")
    op.drop_column("task", "raci_raw")
    op.drop_column("task", "quote")
