from datetime import datetime, timezone

import pytest

from app.tasks.sheets_client import SheetsApiError
from app.tasks.sheets_sync import _find_row_index, _parse_row_number, _row_values

FIXED_NOW = datetime(2026, 7, 22, 12, 30, tzinfo=timezone.utc)


def _task_data(**overrides) -> dict:
    data = {
        "id": "11111111-1111-1111-1111-111111111111",
        "meeting_date": "2026-07-20",
        "topic_name": "Dostawca X",
        "description": "Wyślij raport",
        "r": "Jan Kowalski",
        "a": "Anna Nowak",
        "c": "Piotr",
        "i": "Zarząd",
        "deadline": "2026-08-01",
        "status": "open",
    }
    data.update(overrides)
    return data


def test_row_values_order_matches_columns_a_to_k():
    row = _row_values(_task_data(), now=FIXED_NOW)
    assert row == [
        "11111111-1111-1111-1111-111111111111",
        "2026-07-20",
        "Dostawca X",
        "Wyślij raport",
        "Jan Kowalski",
        "Anna Nowak",
        "Piotr",
        "Zarząd",
        "2026-08-01",
        "otwarte",
        "2026-07-22 12:30",
    ]


def test_row_values_translates_status_label():
    row = _row_values(_task_data(status="done"), now=FIXED_NOW)
    assert row[9] == "zrobione"


def test_row_values_handles_empty_raci_and_topic():
    row = _row_values(_task_data(topic_name="", r="", a="", c="", i="", deadline=""), now=FIXED_NOW)
    assert row[2:9] == ["", "Wyślij raport", "", "", "", "", ""]


def test_parse_row_number_with_quoted_sheet_name():
    assert _parse_row_number("'Zadania RACI'!A6:K6") == 6


def test_parse_row_number_without_sheet_name():
    assert _parse_row_number("A2:K2") == 2


def test_parse_row_number_raises_on_unexpected_format():
    with pytest.raises(SheetsApiError):
        _parse_row_number("garbage")


def test_find_row_index_locates_matching_uuid():
    column = [["aaa"], ["bbb"], ["ccc"]]
    assert _find_row_index(column, "bbb") == 3  # +1 header, +1 1-indexing


def test_find_row_index_skips_empty_rows():
    column = [[], ["bbb"]]
    assert _find_row_index(column, "bbb") == 3


def test_find_row_index_returns_none_when_absent():
    column = [["aaa"], ["bbb"]]
    assert _find_row_index(column, "zzz") is None
