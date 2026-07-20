"""Cienki klient Supabase Storage (REST v1) — upload/pobranie plików audio.

Bucket prywatny (SPEC.md §8): backend łączy się kluczem service role, który
omija RLS i politykę bucketa, więc nie potrzebujemy tu signed URL — te są
potrzebne tylko, gdyby frontend miał kiedyś czytać pliki bezpośrednio.

Bucket trzeba założyć ręcznie w Supabase (Storage → New bucket, Private) pod
nazwą z SUPABASE_AUDIO_BUCKET (domyślnie "meeting-audio") — REST API Storage
nie tworzy bucketów niejawnie przy pierwszym uploadzie.
"""

from __future__ import annotations

import requests

from app.config import settings


class StorageNotConfigured(RuntimeError):
    pass


class StorageError(RuntimeError):
    pass


def _require_config() -> tuple[str, str]:
    if not (settings.supabase_url and settings.supabase_service_role_key):
        raise StorageNotConfigured(
            "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY nie są ustawione w .env."
        )
    return settings.supabase_url.rstrip("/"), settings.supabase_service_role_key


def _headers(service_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {service_key}", "apikey": service_key}


def upload_object(path: str, data: bytes, content_type: str) -> None:
    base_url, service_key = _require_config()
    url = f"{base_url}/storage/v1/object/{settings.supabase_audio_bucket}/{path}"
    try:
        resp = requests.post(
            url,
            headers={**_headers(service_key), "Content-Type": content_type, "x-upsert": "true"},
            data=data,
            timeout=120,
        )
    except requests.RequestException as exc:
        raise StorageError(f"Nie udało się połączyć z Supabase Storage: {exc}") from exc
    if not resp.ok:
        raise StorageError(
            f"Upload do Supabase Storage nie powiódł się ({resp.status_code}): {resp.text}"
        )


def download_object(path: str) -> bytes:
    base_url, service_key = _require_config()
    url = f"{base_url}/storage/v1/object/{settings.supabase_audio_bucket}/{path}"
    try:
        resp = requests.get(url, headers=_headers(service_key), timeout=120)
    except requests.RequestException as exc:
        raise StorageError(f"Nie udało się połączyć z Supabase Storage: {exc}") from exc
    if not resp.ok:
        raise StorageError(
            f"Pobranie z Supabase Storage nie powiodło się ({resp.status_code}): {resp.text}"
        )
    return resp.content
