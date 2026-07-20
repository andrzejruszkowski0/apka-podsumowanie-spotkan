"""SQLAlchemy Core table definitions.

Tylko tabele faktycznie używane przez aplikację (na razie: auth, person, topic).
Reszta schematu z SPEC.md §2 istnieje w bazie (patrz migrations/) i doczeka się
własnych definicji, gdy kolejne etapy zaczną z niej korzystać.
"""

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    LargeBinary,
    MetaData,
    Table,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

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
