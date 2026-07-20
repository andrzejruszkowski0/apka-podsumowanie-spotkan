"""Schematy structured output dla ekstrakcji AI (SPEC.md §10.2, §10.3).

Używane jako `response_schema` w wywołaniach Gemini (structured output ->
JSON zgodny ze schematem, bez markdown/komentarza) oraz do parsowania
odpowiedzi.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RaciCandidate(BaseModel):
    R: str | None = None
    A: str | None = None
    C: list[str] = Field(default_factory=list)
    I: list[str] = Field(default_factory=list)


class TaskCandidate(BaseModel):
    description: str
    deadline: str | None = None  # ISO 8601 albo null
    raci: RaciCandidate = Field(default_factory=RaciCandidate)
    confidence: float
    quote: str


class DecisionCandidate(BaseModel):
    statement: str
    decided_by: str | None = None
    category: str | None = None
    confidence: float
    quote: str


class ExtractionResult(BaseModel):
    """Wyjście fazy MAP dla jednego fragmentu."""

    tasks: list[TaskCandidate] = Field(default_factory=list)
    decisions: list[DecisionCandidate] = Field(default_factory=list)


class MergedTask(TaskCandidate):
    conflict_note: str | None = None


class MergedDecision(DecisionCandidate):
    conflict_note: str | None = None


class MergedResult(BaseModel):
    """Wyjście fazy REDUCE — scalone i zdeduplikowane kandydatury."""

    tasks: list[MergedTask] = Field(default_factory=list)
    decisions: list[MergedDecision] = Field(default_factory=list)
