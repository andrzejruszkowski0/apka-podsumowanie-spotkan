"""Klient Gemini Files API — transkrypcja audio (SPEC.md §4).

Pliki audio przekazywane przez Files API, nie inline base64: inline ma limit
20 MB, a godzinne nagranie to zwykle 25-60 MB (SPEC.md §4). Files API
przyjmuje do 2 GB, pliki żyją 48h po stronie Google — usuwamy je od razu po
transkrypcji, więc to nie ma znaczenia.
"""

from __future__ import annotations

import io
import logging
import time

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

_POLL_INTERVAL_SEC = 2
_POLL_TIMEOUT_SEC = 300


class GeminiNotConfigured(RuntimeError):
    pass


class TranscriptionError(RuntimeError):
    pass


def _client() -> genai.Client:
    if not settings.gemini_api_key:
        raise GeminiNotConfigured("GEMINI_API_KEY nie jest ustawiony w .env.")
    return genai.Client(api_key=settings.gemini_api_key)


def _wait_until_active(client: genai.Client, file: types.File) -> types.File:
    deadline = time.monotonic() + _POLL_TIMEOUT_SEC
    while file.state == types.FileState.PROCESSING:
        if time.monotonic() > deadline:
            raise TranscriptionError(
                f"Plik {file.name} nie osiągnął stanu ACTIVE w Gemini Files API "
                f"w ciągu {_POLL_TIMEOUT_SEC}s."
            )
        time.sleep(_POLL_INTERVAL_SEC)
        file = client.files.get(name=file.name)
    if file.state == types.FileState.FAILED:
        raise TranscriptionError(f"Gemini nie przetworzył pliku {file.name}: {file.error}")
    return file


def transcribe_audio(data: bytes, mime_type: str, display_name: str, prompt: str) -> str:
    """Wysyła jeden plik audio do Gemini (Files API) i zwraca transkrypt."""
    client = _client()
    uploaded = client.files.upload(
        file=io.BytesIO(data),
        config=types.UploadFileConfig(mime_type=mime_type, display_name=display_name),
    )
    try:
        uploaded = _wait_until_active(client, uploaded)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=[prompt, uploaded],
        )
        if not response.text:
            raise TranscriptionError("Gemini zwrócił pustą odpowiedź dla transkrypcji.")
        return response.text
    finally:
        try:
            client.files.delete(name=uploaded.name)
        except Exception:
            logger.warning("Nie udało się usunąć pliku %s z Gemini Files API.", uploaded.name)
