"""Provider isolation from the application database and grading services."""

from dataclasses import dataclass
from typing import Literal, Protocol

from app.schemas.tutor import TutorInput
from app.services.retrieval import PassageHit


@dataclass(frozen=True)
class Turn:
    role: Literal["user", "assistant"]
    text: str


@dataclass(frozen=True)
class TutorContext:
    request: TutorInput
    passages: tuple[PassageHit, ...]
    history: tuple[Turn, ...] = ()
    learner_context: str = ""


@dataclass(frozen=True)
class ProviderAnswer:
    text: str
    passage_ids: tuple[str, ...]


class ProviderUnavailable(RuntimeError):
    """A bounded tutor inference attempt could not produce a usable reply."""


class TutorProvider(Protocol):
    async def respond(self, context: TutorContext) -> ProviderAnswer: ...
