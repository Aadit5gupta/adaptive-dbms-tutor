"""Learner-facing assessment DTOs."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.services.adaptive import NextAction

StudyScope = Annotated[
    str, StringConstraints(pattern=r"^[a-z_]+(?:\.[a-z][a-z0-9_]*)?$", max_length=64)
]


class ItemView(BaseModel):
    item_id: str
    question_ref: str
    subtopic_id: str
    stem: str
    difficulty: str
    options: list[str]


class SessionView(BaseModel):
    session_id: str
    items: list[ItemView]
    total: int = 0
    remaining: int = 0


class AnswerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: Annotated[str, StringConstraints(min_length=1, max_length=64)]
    option_index: Annotated[int, Field(strict=True, ge=0, le=3)]


class SQLAnswerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: Annotated[str, StringConstraints(min_length=1, max_length=64)]
    query: Annotated[str, StringConstraints(min_length=1, max_length=8192)]


class MasteryChange(BaseModel):
    before: float
    after: float
    confidence: str


class HypothesisView(BaseModel):
    code: str
    title: str
    topic_id: str
    state: str
    evidence_count: int


class AnswerResult(BaseModel):
    attempt_id: str
    correct: bool
    explanation: str
    feedback_code: str | None = None
    mastery: MasteryChange | None = None
    next_action: NextAction | None = None
    misconception: HypothesisView | None = None
