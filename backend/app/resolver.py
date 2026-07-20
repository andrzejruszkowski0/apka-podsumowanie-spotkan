"""Rozwiązywanie nazwisk z transkryptu na person.id (SPEC.md §5).

Czysty moduł — brak zależności od FastAPI czy SQLAlchemy, żeby dało się go
testować bez bazy i żeby mógł go współdzielić etap 5 (ekstrakcja) bez
dociągania warstwy web.

Kolejność prób, dokładnie wg SPEC.md §5:
1. dokładne dopasowanie do full_name (case-insensitive)
2. dopasowanie do jednego z aliases
3. dopasowanie po imieniu — tylko jeśli jednoznaczne
4. podobieństwo trigramowe > 0.6 — tylko jeśli jednoznaczne
5. brak dopasowania -> None

Zasada nadrzędna: przy niejednoznaczności (więcej niż jeden pasujący
kandydat na danym etapie) wynikiem jest None, nigdy losowy/pierwszy wybór.

Krok 4 to przybliżenie algorytmu pg_trgm (Postgres) w czystym Pythonie:
trigramy z paddingiem "  tekst ", podobieństwo Jaccarda na zbiorach
trigramów. Nie jest bit-identyczne z funkcją `similarity()` w Postgresie,
ale ten moduł jest jedynym miejscem, które tę wartość liczy — więc spójność
z samym sobą (i testowalność bez żywej bazy) jest tym, co się liczy.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

SIMILARITY_THRESHOLD = 0.6


@dataclass(frozen=True)
class PersonRecord:
    id: str
    full_name: str
    aliases: Sequence[str] = field(default_factory=tuple)


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _trigrams(value: str) -> set[str]:
    padded = f"  {value} "
    if len(padded) < 3:
        return {padded}
    return {padded[i : i + 3] for i in range(len(padded) - 2)}


def _similarity(a: str, b: str) -> float:
    trigrams_a, trigrams_b = _trigrams(a), _trigrams(b)
    if not trigrams_a or not trigrams_b:
        return 0.0
    union = len(trigrams_a | trigrams_b)
    if union == 0:
        return 0.0
    return len(trigrams_a & trigrams_b) / union


def resolve_name(raw_name: str, people: Iterable[PersonRecord]) -> str | None:
    """Zwraca person.id albo None, jeśli brak dopasowania lub jest niejednoznaczne."""
    if not raw_name or not raw_name.strip():
        return None

    candidates = list(people)
    target = _normalize(raw_name)
    if not target:
        return None

    exact = [p for p in candidates if _normalize(p.full_name) == target]
    if len(exact) == 1:
        return exact[0].id
    if len(exact) > 1:
        return None

    alias_matches = [
        p for p in candidates if target in {_normalize(alias) for alias in p.aliases}
    ]
    if len(alias_matches) == 1:
        return alias_matches[0].id
    if len(alias_matches) > 1:
        return None

    first_name_matches = [
        p for p in candidates if _normalize(p.full_name).split(" ")[0] == target
    ]
    if len(first_name_matches) == 1:
        return first_name_matches[0].id
    if len(first_name_matches) > 1:
        return None

    above_threshold = [
        p for p in candidates if _similarity(target, _normalize(p.full_name)) > SIMILARITY_THRESHOLD
    ]
    if len(above_threshold) == 1:
        return above_threshold[0].id

    return None
