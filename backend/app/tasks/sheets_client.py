"""Cienki klient zapisu Google Sheets (REST v4) — bez google-api-python-client.

Odpowiednik app.people.sheets_client, ale z operacjami zapisu potrzebnymi do
eksportu zadań (SPEC.md §6, etap 7): append, update, metadane arkusza
i batchUpdate (protected range na nagłówku).
"""

from __future__ import annotations

import requests

_BASE_URL = "https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
_VALUES_URL = _BASE_URL + "/values/{range_}"
_APPEND_URL = _VALUES_URL + ":append"
_BATCH_UPDATE_URL = _BASE_URL + ":batchUpdate"


class SheetsApiError(RuntimeError):
    pass


def _headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def get_values(access_token: str, spreadsheet_id: str, range_: str) -> list[list[str]]:
    try:
        resp = requests.get(
            _VALUES_URL.format(spreadsheet_id=spreadsheet_id, range_=range_),
            headers=_headers(access_token),
            timeout=15,
        )
    except requests.RequestException as exc:
        raise SheetsApiError(f"Nie udało się połączyć z Google Sheets API: {exc}") from exc
    if not resp.ok:
        raise SheetsApiError(f"Sheets API zwróciło błąd {resp.status_code}: {resp.text}")
    return resp.json().get("values", [])


def update_values(access_token: str, spreadsheet_id: str, range_: str, values: list[list[str]]) -> dict:
    try:
        resp = requests.put(
            _VALUES_URL.format(spreadsheet_id=spreadsheet_id, range_=range_),
            headers=_headers(access_token),
            params={"valueInputOption": "USER_ENTERED"},
            json={"values": values},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise SheetsApiError(f"Nie udało się połączyć z Google Sheets API: {exc}") from exc
    if not resp.ok:
        raise SheetsApiError(f"Sheets API zwróciło błąd {resp.status_code}: {resp.text}")
    return resp.json()


def append_values(access_token: str, spreadsheet_id: str, range_: str, values: list[list[str]]) -> dict:
    try:
        resp = requests.post(
            _APPEND_URL.format(spreadsheet_id=spreadsheet_id, range_=range_),
            headers=_headers(access_token),
            params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
            json={"values": values},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise SheetsApiError(f"Nie udało się połączyć z Google Sheets API: {exc}") from exc
    if not resp.ok:
        raise SheetsApiError(f"Sheets API zwróciło błąd {resp.status_code}: {resp.text}")
    return resp.json()


def get_first_sheet_id(access_token: str, spreadsheet_id: str) -> int:
    try:
        resp = requests.get(
            _BASE_URL.format(spreadsheet_id=spreadsheet_id),
            headers=_headers(access_token),
            params={"fields": "sheets.properties.sheetId"},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise SheetsApiError(f"Nie udało się połączyć z Google Sheets API: {exc}") from exc
    if not resp.ok:
        raise SheetsApiError(f"Sheets API zwróciło błąd {resp.status_code}: {resp.text}")
    sheets = resp.json().get("sheets", [])
    if not sheets:
        raise SheetsApiError("Arkusz nie ma żadnych zakładek.")
    return sheets[0]["properties"]["sheetId"]


def batch_update(access_token: str, spreadsheet_id: str, body: dict) -> dict:
    try:
        resp = requests.post(
            _BATCH_UPDATE_URL.format(spreadsheet_id=spreadsheet_id),
            headers=_headers(access_token),
            json=body,
            timeout=15,
        )
    except requests.RequestException as exc:
        raise SheetsApiError(f"Nie udało się połączyć z Google Sheets API: {exc}") from exc
    if not resp.ok:
        raise SheetsApiError(f"Sheets API zwróciło błąd {resp.status_code}: {resp.text}")
    return resp.json()
