"""Learner-facing assessment DTOs."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class ItemView(BaseModel):
    item_id: str
    question_ref: str
    subtopic_id: str
    stem: str
    options: list[str]


class SessionView(BaseModel):
    session_id: str
    items: list[ItemView]


class AnswerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: Annotated[str, StringConstraints(min_length=1, max_length=64)]
    option_index: Annotated[int, Field(strict=True, ge=0, le=3)]


class AnswerResult(BaseModel):
    attempt_id: str
    correct: bool
    explanation: str
