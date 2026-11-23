"""Bounded tutoring requests and source-attributed replies."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.services.retrieval import Citation

Mode = Literal["ask", "explain", "simpler", "example", "hint", "sql_feedback"]
Topic = Annotated[str, StringConstraints(pattern=r"^[a-z_]+\.[a-z][a-z0-9_]*$", max_length=64)]


class TutorInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=600)]
    topic_id: Topic | None = None
    mode: Mode = "ask"
    hint_level: Annotated[int, Field(ge=1, le=3)] = 1


class TutorReply(BaseModel):
    answer: str
    citations: list[Citation]
    mode: Mode
    provider: Literal["curated", "ollama"]
    degraded: bool
    status: Literal["ok", "ai_unavailable", "no_evidence"]
