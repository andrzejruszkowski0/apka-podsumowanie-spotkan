"""Cienki klient odczytu Google Sheets (REST v4) — bez google-api-python-client.

Używa access tokena Google dostarczonego przez wywołującego (patrz
app.auth.service_account.get_service_account_access_token) — ten moduł nic
nie wie o auth ani o bazie.
"""

from __future__ import annotations

import requests

_VALUES_URL = "https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_}"


class SheetsApiError(RuntimeError):
    pass


def fetch_values(access_token: str, spreadsheet_id: str, range_: str = "A2:E") -> list[list[str]]:
    """Zwraca wiersze arkusza jako listę list stringów (bez nagłówka, patrz range_)."""
    try:
        resp = requests.get(
            _VALUES_URL.format(spreadsheet_id=spreadsheet_id, range_=range_),
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise SheetsApiError(f"Nie udało się połączyć z Google Sheets API: {exc}") from exc

    if not resp.ok:
        raise SheetsApiError(f"Sheets API zwróciło błąd {resp.status_code}: {resp.text}")

    return resp.json().get("values", [])
