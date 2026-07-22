"""SQLAlchemy Core table definitions.

Tabele faktycznie używane przez aplikację: auth, person, topic, meeting
i pochodne, task/task_raci/decision (etap 5) oraz notification_log/
scheduler_run (etap 8 — przypomnienia mailowe i catch-up schedulera).

task.quote, task.raci_raw i decision.quote/ai_confidence nie są w SPEC.md §2 —
dodane migracją 0002, patrz komentarz tam.
"""

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    REAL,
    Table,
    Text,
    func,
    text,
)
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID

metadata = MetaData()

app_user = Table(
    "app_user",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("google_sub", Text, nullable=False, unique=True),
    Column("email", Text, nullable=False),
    Column("display_name", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

oauth_token = Table(
    "oauth_token",
    metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), primary_key=True),
    Column("refresh_token_enc", LargeBinary, nullable=False),
    Column("access_token_enc", LargeBinary),
    Column("access_expires_at", DateTime(timezone=True)),
    Column("scopes", ARRAY(Text), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

person = Table(
    "person",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("full_name", Text, nullable=False),
    Column("email", Text, nullable=False, unique=True),
    Column("aliases", ARRAY(Text), nullable=False, server_default=text("'{}'")),
    Column("org", Text),
    Column("active", Boolean, nullable=False, server_default=text("true")),
    Column("synced_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

topic = Table(
    "topic",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("name", Text, nullable=False, unique=True),
    Column("kind", Text, nullable=False),
    Column("notes", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

meeting = Table(
    "meeting",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("user_id", UUID(as_uuid=True), ForeignKey("app_user.id"), nullable=False),
    Column("topic_id", UUID(as_uuid=True), ForeignKey("topic.id")),
    Column("title", Text, nullable=False),
    Column("meeting_date", Date, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("status", Text, nullable=False, server_default=text("'uploaded'")),
    Column("error_message", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

meeting_audio = Table(
    "meeting_audio",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("meeting_id", UUID(as_uuid=True), ForeignKey("meeting.id", ondelete="CASCADE"), nullable=False),
    Column("storage_path", Text, nullable=False),
    Column("part_index", Integer, nullable=False),
    Column("duration_sec", Integer),
    Column("bytes", BigInteger),
)

transcript = Table(
    "transcript",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("meeting_id", UUID(as_uuid=True), ForeignKey("meeting.id", ondelete="CASCADE"), nullable=False),
    Column("part_index", Integer, nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

task = Table(
    "task",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("meeting_id", UUID(as_uuid=True), ForeignKey("meeting.id", ondelete="CASCADE"), nullable=False),
    Column("topic_id", UUID(as_uuid=True), ForeignKey("topic.id")),
    Column("description", Text, nullable=False),
    Column("deadline", Date),
    Column("status", Text, nullable=False, server_default=text("'open'")),
    Column("done_at", DateTime(timezone=True)),
    Column("ai_confidence", REAL),
    Column("edited_by_user", Boolean, nullable=False, server_default=text("false")),
    Column("sheets_row", Integer),
    Column("quote", Text),
    Column("raci_raw", JSONB),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint("status in ('open','done','cancelled')", name="task_status_check"),
)

task_raci = Table(
    "task_raci",
    metadata,
    Column("task_id", UUID(as_uuid=True), ForeignKey("task.id", ondelete="CASCADE"), primary_key=True),
    Column("person_id", UUID(as_uuid=True), ForeignKey("person.id"), primary_key=True),
    Column("role", Text, primary_key=True),
    CheckConstraint("role in ('R','A','C','I')", name="task_raci_role_check"),
)

decision = Table(
    "decision",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("meeting_id", UUID(as_uuid=True), ForeignKey("meeting.id", ondelete="CASCADE"), nullable=False),
    Column("topic_id", UUID(as_uuid=True), ForeignKey("topic.id")),
    Column("statement", Text, nullable=False),
    Column("decided_on", Date, nullable=False),
    Column("decided_by", UUID(as_uuid=True), ForeignKey("person.id")),
    Column("decided_by_raw", Text),
    Column("category", Text),
    Column("quote", Text),
    Column("ai_confidence", REAL),
    # Kolumna istnieje w bazie od migracji 0001 (create table + indeks ivfflat);
    # tu dopiero dodajemy jej typ do metadanych, gdy pojawia się generowanie
    # embeddingów (etap 9, SPEC.md §10.4).
    Column("embedding", Vector(768)),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

notification_log = Table(
    "notification_log",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("kind", Text, nullable=False),
    Column("task_id", UUID(as_uuid=True), ForeignKey("task.id", ondelete="CASCADE")),
    Column("meeting_id", UUID(as_uuid=True), ForeignKey("meeting.id", ondelete="CASCADE")),
    Column("recipient", Text, nullable=False),
    Column("sent_on", Date, nullable=False),
    Column("gmail_id", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint("kind in ('reminder','briefing','summary')", name="notification_log_kind_check"),
)

# Znacznik ostatniego przebiegu schedulera — podstawa catch-up przy starcie
# backendu (SPEC.md §7): job_name='daily_reminders' -> data ostatniego przebiegu.
scheduler_run = Table(
    "scheduler_run",
    metadata,
    Column("job_name", Text, primary_key=True),
    Column("last_run", Date, nullable=False),
)
