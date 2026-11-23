"""Private tutorial endpoints for signed-in accounts and the local demo."""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.api.demo import loopback_only
from app.schemas.tutor import TutorInput, TutorReply, TutorTurnView
from app.services.conversations import conversation_history, teach
from app.services.demo import Learner, require_learner
from app.services.tutor import TutorService


def tutor_router(
    service: TutorService,
    engine: Engine,
    identity: Callable[..., str],
    *,
    prefix: str = "/tutor",
) -> APIRouter:
    router = APIRouter(prefix=prefix)

    @router.post("/ask", response_model=TutorReply)
    async def ask(body: TutorInput, user_id: Annotated[str, Depends(identity)]) -> TutorReply:
        return await teach(engine, service, user_id, body.model_copy(update={"mode": "ask"}))

    @router.post("/explain", response_model=TutorReply)
    async def explain(body: TutorInput, user_id: Annotated[str, Depends(identity)]) -> TutorReply:
        request = (
            body
            if body.mode in ("simpler", "example", "sql_feedback")
            else body.model_copy(update={"mode": "explain"})
        )
        return await teach(engine, service, user_id, request)

    @router.post("/hint", response_model=TutorReply)
    async def hint(body: TutorInput, user_id: Annotated[str, Depends(identity)]) -> TutorReply:
        return await teach(engine, service, user_id, body.model_copy(update={"mode": "hint"}))

    @router.get("/conversations/{thread}")
    def history(thread: str, user_id: Annotated[str, Depends(identity)]) -> list[TutorTurnView]:
        return conversation_history(engine, user_id, thread)

    return router


def local_tutor_router(service: TutorService, engine: Engine) -> APIRouter:
    def learner_identity(learner: Learner, request: Request) -> str:
        loopback_only(request)
        with Session(engine) as db:
            return require_learner(db, learner)

    return tutor_router(service, engine, learner_identity, prefix="/demo/tutor/{learner}")
