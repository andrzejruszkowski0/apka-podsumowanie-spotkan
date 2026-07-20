import uuid

from app.meetings.extraction import (
    UNRESOLVED_CONFIDENCE_CAP,
    _parse_deadline,
    _resolve_raci,
)
from app.meetings.extraction_schemas import RaciCandidate
from app.resolver import PersonRecord

MEETING_ID = uuid.uuid4()

JAN = PersonRecord(id="jan", full_name="Jan Kowalski", aliases=["Janek"])
ANNA = PersonRecord(id="anna", full_name="Anna Nowak", aliases=[])
PEOPLE = [JAN, ANNA]


def test_resolve_raci_all_resolved_no_flag():
    raci = RaciCandidate(R="Janek", A="Anna Nowak", C=[], I=[])
    resolved, any_unresolved, resolved_c, resolved_i = _resolve_raci(raci, PEOPLE)
    assert resolved == {"R": "jan", "A": "anna"}
    assert any_unresolved is False
    assert resolved_c == []
    assert resolved_i == []


def test_resolve_raci_unresolved_r_sets_flag():
    raci = RaciCandidate(R="Ktoś Nieznany", A=None, C=[], I=[])
    resolved, any_unresolved, _, _ = _resolve_raci(raci, PEOPLE)
    assert resolved["R"] is None
    assert any_unresolved is True


def test_resolve_raci_unresolved_c_member_sets_flag_even_if_ra_ok():
    raci = RaciCandidate(R="Janek", A="Anna Nowak", C=["Nieznany"], I=[])
    resolved, any_unresolved, resolved_c, _ = _resolve_raci(raci, PEOPLE)
    assert any_unresolved is True
    assert resolved_c == [None]


def test_resolve_raci_no_r_or_a_mentioned_no_flag():
    raci = RaciCandidate(R=None, A=None, C=[], I=[])
    resolved, any_unresolved, _, _ = _resolve_raci(raci, PEOPLE)
    assert resolved == {}
    assert any_unresolved is False


def test_parse_deadline_valid_iso_date():
    assert _parse_deadline("2026-08-01", MEETING_ID) is not None
    assert _parse_deadline("2026-08-01", MEETING_ID).isoformat() == "2026-08-01"


def test_parse_deadline_none_when_missing():
    assert _parse_deadline(None, MEETING_ID) is None


def test_parse_deadline_none_when_unparseable():
    assert _parse_deadline("wkrótce", MEETING_ID) is None


def test_unresolved_confidence_cap_is_below_review_threshold():
    # 0.7 to próg wyróżnienia na ekranie weryfikacji (SPEC.md §11) — capnięta
    # wartość musi być poniżej niego, inaczej nierozwiązane nazwisko nie
    # zostałoby wizualnie wyróżnione.
    assert UNRESOLVED_CONFIDENCE_CAP < 0.7
