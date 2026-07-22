"""Cienki klient wysyłki Gmail (REST v1) — bez google-api-python-client.

Odpowiednik app.tasks.sheets_client, tym razem do wysyłki maili (SPEC.md §7,
etap 8). Wiadomość budowana jako RFC 2822 (email.message.EmailMessage, obsługa
UTF-8 w nagłówkach i treści „za darmo"), kodowana base64url zgodnie z
wymaganiami Gmail API `users.messages.send`.
"""

from __future__ import annotations

import base64
from email import policy
from email.message import EmailMessage

import requests

_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


class GmailApiError(RuntimeError):
    pass


def _build_raw_message(*, to: str, subject: str, body: str, cc: str | None) -> str:
    # policy.SMTP (nie domyślny policy.default) kończy linie \r\n zgodnie z RFC 5322 —
    # bez tego Gmail API czasem odrzuca wiadomość błędem "Invalid To header",
    # bo jego parser jest rygorystyczny co do zakończeń linii w nagłówkach.
    msg = EmailMessage(policy=policy.SMTP)
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    msg.set_content(body)
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")


def send_message(access_token: str, *, to: str, subject: str, body: str, cc: str | None = None) -> str:
    """Wysyła maila, zwraca id wiadomości Gmail (do zapisu w notification_log.gmail_id)."""
    raw = _build_raw_message(to=to, subject=subject, body=body, cc=cc)
    try:
        resp = requests.post(
            _SEND_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            json={"raw": raw},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise GmailApiError(f"Nie udało się połączyć z Gmail API: {exc}") from exc
    if not resp.ok:
        raise GmailApiError(f"Gmail API zwróciło błąd {resp.status_code}: {resp.text}")
    return resp.json()["id"]
