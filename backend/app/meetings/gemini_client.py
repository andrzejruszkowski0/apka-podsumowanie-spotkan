"""Klient Gemini — transkrypcja audio (SPEC.md §4) i ekstrakcja MAP/REDUCE
(SPEC.md §10.2, §10.3, etap 5).

Pliki audio przekazywane przez Files API, nie inline base64: inline ma limit
20 MB, a godzinne nagranie to zwykle 25-60 MB (SPEC.md §4). Files API
przyjmuje do 2 GB, pliki żyją 48h po stronie Google — usuwamy je od razu po
transkrypcji, więc to nie ma znaczenia.

Ekstrakcja używa structured output (response_schema) zamiast parsowania
wolnego tekstu — Gemini gwarantuje wtedy JSON zgodny z pydantic modelem.
"""

from __future__ import annotations

import io
import logging
import time
import uuid
from pathlib import Path

from google import genai
from google.genai import types

from app.config import settings
from app.meetings.extraction_schemas import ExtractionResult, MergedResult

logger = logging.getLogger(__name__)

_POLL_INTERVAL_SEC = 2
_POLL_TIMEOUT_SEC = 300

# ETAPY.md etap 5, pkt 8: surowe odpowiedzi Gemini do pliku (debug jakości
# promptów) — nie do bazy, to tylko narzędzie deweloperskie.
_RAW_LOG_DIR = Path(__file__).resolve().parents[2] / "logs" / "gemini_raw"


class GeminiNotConfigured(RuntimeError):
    pass


class TranscriptionError(RuntimeError):
    pass


class ExtractionError(RuntimeError):
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


def _log_raw_response(meeting_id: uuid.UUID, phase: str, index: int, raw_text: str) -> None:
    """Zapisuje surową odpowiedź Gemini do pliku — debug jakości promptów
    (ETAPY.md etap 5, pkt 8). Nigdy nie rzuca — logowanie nie może wywrócić
    przetwarzania."""
    try:
        _RAW_LOG_DIR.mkdir(parents=True, exist_ok=True)
        path = _RAW_LOG_DIR / f"{meeting_id}_{phase}_{index}.json"
        path.write_text(raw_text, encoding="utf-8")
    except OSError:
        logger.warning("Nie udało się zapisać surowej odpowiedzi Gemini do logu (%s, %s).", phase, index)


def extract_from_fragment(fragment_prompt: str, meeting_id: uuid.UUID, chunk_index: int) -> ExtractionResult:
    """Faza MAP (SPEC.md §10.2): jedno wywołanie na fragment, structured output."""
    client = _client()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=fragment_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractionResult,
        ),
    )
    if not response.text:
        raise ExtractionError("Gemini zwrócił pustą odpowiedź dla fazy MAP.")
    _log_raw_response(meeting_id, "map", chunk_index, response.text)
    return ExtractionResult.model_validate_json(response.text)


def reduce_candidates(reduce_prompt: str, meeting_id: uuid.UUID) -> MergedResult:
    """Faza REDUCE (SPEC.md §10.3): jedno wywołanie scalające wszystkie kandydatury."""
    client = _client()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=reduce_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=MergedResult,
        ),
    )
    if not response.text:
        raise ExtractionError("Gemini zwrócił pustą odpowiedź dla fazy REDUCE.")
    _log_raw_response(meeting_id, "reduce", 0, response.text)
    return MergedResult.model_validate_json(response.text)
