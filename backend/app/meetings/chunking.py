"""Dzielenie transkryptu na fragmenty do fazy MAP (SPEC.md §4, ETAPY.md etap 5).

Czysty moduł tekstowy — bez zależności na DB/FastAPI, żeby dało się go
testować w izolacji, tak jak resolver.py.

Zasady dokładnie wg SPEC.md:
- transkrypt < 5000 słów -> jeden fragment, bez dzielenia (jeden przebieg MAP,
  bez fazy REDUCE po stronie wywołującego).
- w przeciwnym razie: fragmenty ~4000 słów z zakładem ~200 słów.
"""

from __future__ import annotations

SINGLE_PASS_WORD_THRESHOLD = 5000
CHUNK_SIZE_WORDS = 4000
OVERLAP_WORDS = 200


def split_into_chunks(transcript: str) -> list[str]:
    """Zwraca listę fragmentów tekstu. Zawsze co najmniej jeden element
    (pusty transkrypt -> lista z jednym pustym fragmentem), żeby wywołujący
    kod nie musiał osobno obsługiwać przypadku brzegowego."""
    words = transcript.split()
    if not words:
        return [transcript]

    if len(words) < SINGLE_PASS_WORD_THRESHOLD:
        return [transcript]

    step = CHUNK_SIZE_WORDS - OVERLAP_WORDS
    chunks = []
    start = 0
    while start < len(words):
        end = start + CHUNK_SIZE_WORDS
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start += step
    return chunks
