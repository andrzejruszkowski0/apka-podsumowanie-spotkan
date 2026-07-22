import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.decisions.router import _serialize

MEETING_ID = uuid.uuid4()
TOPIC_ID = uuid.uuid4()
DECISION_ID = uuid.uuid4()


def _row(**overrides) -> SimpleNamespace:
    data = {
        "id": DECISION_ID,
        "meeting_id": MEETING_ID,
        "topic_id": TOPIC_ID,
        "topic_name": "Dostawca X",
        "statement": "Dostawca X zgadza się na rabat 3%",
        "decided_on": date(2026, 7, 1),
        "category": "cena",
        "decided_by_raw": "Janek",
        "decided_by_name": "Jan Kowalski",
        "created_at": datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_serialize_prefers_resolved_name_over_raw():
    result = _serialize(_row())
    assert result["decided_by"] == "Jan Kowalski"


def test_serialize_falls_back_to_raw_name_when_unresolved():
    result = _serialize(_row(decided_by_name=None))
    assert result["decided_by"] == "Janek"


def test_serialize_decided_by_none_when_ai_did_not_mention_anyone():
    result = _serialize(_row(decided_by_name=None, decided_by_raw=None))
    assert result["decided_by"] is None


def test_serialize_topic_id_none_when_no_topic():
    result = _serialize(_row(topic_id=None, topic_name=None))
    assert result["topic_id"] is None
    assert result["topic_name"] is None


def test_serialize_dates_are_iso_strings():
    result = _serialize(_row())
    assert result["decided_on"] == "2026-07-01"
    assert result["created_at"] == "2026-07-01T10:00:00+00:00"


def test_serialize_ids_are_strings():
    result = _serialize(_row())
    assert result["id"] == str(DECISION_ID)
    assert result["meeting_id"] == str(MEETING_ID)
    assert result["topic_id"] == str(TOPIC_ID)
