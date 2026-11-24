"""Bounded tutoring requests and source-attributed replies."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.services.retrieval import Citation

Mode = Literal["ask", "explain", "simpler", "example", "hint", "sql_feedback"]
Topic = Annotated[str, StringConstraints(pattern=r"^[a-z_]+\.[a-z][a-z0-9_]*$", max_length=64)]


Identifier = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{32}$")]


class TutorInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: Annotated[str, StringConstraints(strip_whitespace=True, max_length=600)] = ""
    topic_id: Topic | None = None
    mode: Mode = "ask"
    hint_level: Annotated[int, Field(strict=True, ge=1, le=3)] = 1
    conversation_id: Identifier | None = None
    item_id: Identifier | None = None
    attempt_id: Identifier | None = None

    @model_validator(mode="after")
    def require_question(self) -> "TutorInput":
        if len(self.query) == 1 or (not self.query and self.item_id is None):
            raise ValueError("Enter a question with at least two characters")
        return self


class TutorReply(BaseModel):
    answer: str
    citations: list[Citation]
    mode: Mode
    provider: Literal["curated", "ollama"]
    degraded: bool
    status: Literal["ok", "ai_unavailable", "no_evidence"]
    topic_id: str | None = None
    conversation_id: str | None = None


class TutorTurnView(BaseModel):
    role: Literal["user", "assistant"]
    text: str
    reply: TutorReply | None = None
