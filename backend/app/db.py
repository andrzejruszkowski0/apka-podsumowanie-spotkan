from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# prepare_threshold=None wyłącza server-side prepared statements psycopg3.
# DATABASE_URL wskazuje na Supabase transaction-mode pooler (port 6543,
# PgBouncer) — PgBouncer w tym trybie może przydzielić kolejnemu zapytaniu
# inne fizyczne połączenie do Postgresa niż to, na którym przygotowano
# statement, co kończy się błędem "prepared statement already exists".
# Bez tego psycopg3 zaczyna przygotowywać powtarzające się zapytania po
# kilku wywołaniach i całe zapytania do bazy zaczynają losowo padać.
engine = create_engine(
    settings.database_url,
    connect_args={"connect_timeout": 5, "prepare_threshold": None},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
