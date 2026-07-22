from datetime import date
from email import message_from_bytes, policy
from email.header import decode_header, make_header

import pytest

from app.notifications.gmail_client import GmailApiError, _build_raw_message, send_message
from app.notifications.templates import reminder_body, reminder_subject


def test_reminder_subject_keeps_short_description():
    assert reminder_subject("Wyślij raport") == "Przypomnienie: Wyślij raport"


def test_reminder_subject_truncates_long_description():
    long_description = "x" * 80
    subject = reminder_subject(long_description)
    assert subject == "Przypomnienie: " + "x" * 57 + "..."


def test_reminder_body_contains_task_deadline_topic_and_panel_link():
    body = reminder_body(description="Wyślij raport", deadline=date(2026, 8, 1), topic_name="Dostawca X")
    assert "Zadanie: Wyślij raport" in body
    assert "Termin: 2026-08-01" in body
    assert "Temat: Dostawca X" in body
    assert "/tasks" in body


def test_reminder_body_uses_placeholder_when_no_topic():
    body = reminder_body(description="Wyślij raport", deadline=date(2026, 8, 1), topic_name=None)
    assert "Temat: —" in body


def test_build_raw_message_roundtrips_to_cc_subject_and_body():
    raw = _build_raw_message(
        to="r@example.com", subject="Przypomnienie: coś", body="treść\nmaila", cc="a@example.com"
    )
    import base64

    parsed = message_from_bytes(base64.urlsafe_b64decode(raw), policy=policy.default)
    subject = str(make_header(decode_header(parsed["Subject"])))
    assert parsed["To"] == "r@example.com"
    assert parsed["Cc"] == "a@example.com"
    assert subject == "Przypomnienie: coś"
    # policy.SMTP normalizuje zakończenia linii do \r\n (RFC 5322) — stąd normalizacja przed porównaniem.
    assert parsed.get_content().strip().replace("\r\n", "\n") == "treść\nmaila"


def test_build_raw_message_without_cc_omits_header():
    raw = _build_raw_message(to="r@example.com", subject="S", body="B", cc=None)
    import base64

    parsed = message_from_bytes(base64.urlsafe_b64decode(raw))
    assert parsed["Cc"] is None


class _FakeResponse:
    def __init__(self, status_code: int, json_body: dict, text: str = ""):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self._json_body = json_body
        self.text = text or str(json_body)

    def json(self):
        return self._json_body


def test_send_message_returns_gmail_id_on_success(monkeypatch):
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return _FakeResponse(200, {"id": "msg-123"})

    monkeypatch.setattr("app.notifications.gmail_client.requests.post", fake_post)

    gmail_id = send_message("token-abc", to="r@example.com", cc="a@example.com", subject="S", body="B")

    assert gmail_id == "msg-123"
    assert captured["url"] == "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    assert captured["headers"] == {"Authorization": "Bearer token-abc"}
    assert "raw" in captured["json"]


def test_send_message_raises_gmail_api_error_on_failure(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        return _FakeResponse(403, {}, text="insufficient scope")

    monkeypatch.setattr("app.notifications.gmail_client.requests.post", fake_post)

    with pytest.raises(GmailApiError):
        send_message("token-abc", to="r@example.com", subject="S", body="B")


def test_send_message_raises_gmail_api_error_on_connection_failure(monkeypatch):
    import requests

    def fake_post(url, headers=None, json=None, timeout=None):
        raise requests.RequestException("boom")

    monkeypatch.setattr("app.notifications.gmail_client.requests.post", fake_post)

    with pytest.raises(GmailApiError):
        send_message("token-abc", to="r@example.com", subject="S", body="B")
