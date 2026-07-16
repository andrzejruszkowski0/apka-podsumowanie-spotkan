"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-16

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "app_user",
    "oauth_token",
    "person",
    "topic",
    "meeting",
    "meeting_audio",
    "transcript",
    "task",
    "task_raci",
    "decision",
    "notification_log",
    "scheduler_run",
]


def upgrade() -> None:
    op.execute("create extension if not exists pgcrypto")
    op.execute("create extension if not exists vector")
    op.execute("create extension if not exists pg_trgm")

    op.execute(
        """
        create table app_user (
          id            uuid primary key default gen_random_uuid(),
          google_sub    text unique not null,
          email         text not null,
          display_name  text,
          created_at    timestamptz not null default now()
        )
        """
    )

    op.execute(
        """
        create table oauth_token (
          user_id           uuid primary key references app_user(id) on delete cascade,
          refresh_token_enc bytea not null,
          access_token_enc  bytea,
          access_expires_at timestamptz,
          scopes            text[] not null,
          updated_at        timestamptz not null default now()
        )
        """
    )

    op.execute(
        """
        create table person (
          id          uuid primary key default gen_random_uuid(),
          full_name   text not null,
          email       text not null,
          aliases     text[] not null default '{}',
          org         text,
          active      boolean not null default true,
          synced_at   timestamptz not null default now(),
          unique (email)
        )
        """
    )
    op.execute("create index on person using gin (aliases)")

    op.execute(
        """
        create table topic (
          id          uuid primary key default gen_random_uuid(),
          name        text not null unique,
          kind        text not null check (kind in ('supplier','project','internal')),
          notes       text,
          created_at  timestamptz not null default now()
        )
        """
    )

    op.execute(
        """
        create table meeting (
          id            uuid primary key default gen_random_uuid(),
          user_id       uuid not null references app_user(id),
          topic_id      uuid references topic(id),
          title         text not null,
          meeting_date  date not null,
          source_type   text not null check (source_type in ('audio','text')),
          status        text not null default 'uploaded'
                        check (status in ('uploaded','transcribing','analyzing',
                                          'awaiting_review','approved','failed')),
          error_message text,
          created_at    timestamptz not null default now()
        )
        """
    )

    op.execute(
        """
        create table meeting_audio (
          id           uuid primary key default gen_random_uuid(),
          meeting_id   uuid not null references meeting(id) on delete cascade,
          storage_path text not null,
          part_index   int  not null,
          duration_sec int,
          bytes        bigint,
          unique (meeting_id, part_index)
        )
        """
    )

    op.execute(
        """
        create table transcript (
          id          uuid primary key default gen_random_uuid(),
          meeting_id  uuid not null references meeting(id) on delete cascade,
          part_index  int not null,
          content     text not null,
          created_at  timestamptz not null default now(),
          unique (meeting_id, part_index)
        )
        """
    )

    op.execute(
        """
        create table task (
          id             uuid primary key default gen_random_uuid(),
          meeting_id     uuid not null references meeting(id) on delete cascade,
          topic_id       uuid references topic(id),
          description    text not null,
          deadline       date,
          status         text not null default 'open'
                         check (status in ('open','done','cancelled')),
          done_at        timestamptz,
          ai_confidence  real,
          edited_by_user boolean not null default false,
          sheets_row     int,
          created_at     timestamptz not null default now()
        )
        """
    )

    op.execute(
        """
        create table task_raci (
          task_id    uuid not null references task(id) on delete cascade,
          person_id  uuid not null references person(id),
          role       char(1) not null check (role in ('R','A','C','I')),
          primary key (task_id, person_id, role)
        )
        """
    )
    op.execute("create unique index task_single_r on task_raci (task_id) where role = 'R'")
    op.execute("create unique index task_single_a on task_raci (task_id) where role = 'A'")

    op.execute(
        """
        create table decision (
          id           uuid primary key default gen_random_uuid(),
          meeting_id   uuid not null references meeting(id) on delete cascade,
          topic_id     uuid references topic(id),
          statement    text not null,
          decided_on   date not null,
          decided_by   uuid references person(id),
          category     text,
          embedding    vector(768),
          created_at   timestamptz not null default now()
        )
        """
    )
    op.execute("create index on decision using ivfflat (embedding vector_cosine_ops)")

    op.execute(
        """
        create table notification_log (
          id          uuid primary key default gen_random_uuid(),
          kind        text not null check (kind in ('reminder','briefing','summary')),
          task_id     uuid references task(id) on delete cascade,
          meeting_id  uuid references meeting(id) on delete cascade,
          recipient   text not null,
          sent_on     date not null,
          gmail_id    text,
          created_at  timestamptz not null default now()
        )
        """
    )
    op.execute(
        """
        create unique index notif_once_per_day
          on notification_log (kind, task_id, recipient, sent_on)
          where task_id is not null
        """
    )

    op.execute(
        """
        create table scheduler_run (
          job_name  text primary key,
          last_run  date not null
        )
        """
    )

    for table in TABLES:
        op.execute(f"alter table {table} enable row level security")
        op.execute(
            f"""
            create policy deny_all_anon on {table}
            for all to anon using (false) with check (false)
            """
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.execute(f"drop table if exists {table} cascade")

    op.execute("drop extension if exists pg_trgm")
    op.execute("drop extension if exists vector")
    op.execute("drop extension if exists pgcrypto")
