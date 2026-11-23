"""Local tutor endpoints, shared by demo and signed-in learning."""

from collections.abc import Callable

from fastapi import APIRouter, Depends, Request

from app.api.demo import loopback_only
from app.schemas.tutor import TutorInput, TutorReply
from app.services.tutor import TutorService


def tutor_router(
    service: TutorService,
    guard: Callable[[Request], object],
    *,
    prefix: str = "/tutor",
) -> APIRouter:
    router = APIRouter(prefix=prefix, dependencies=[Depends(guard)])

    @router.post("/ask", response_model=TutorReply)
    async def ask(body: TutorInput) -> TutorReply:
        return await service.answer(body)

    @router.post("/explain", response_model=TutorReply)
    async def explain(body: TutorInput) -> TutorReply:
        request = (
            body
            if body.mode in ("simpler", "example", "sql_feedback")
            else body.model_copy(update={"mode": "explain"})
        )
        return await service.answer(request)

    @router.post("/hint", response_model=TutorReply)
    async def hint(body: TutorInput) -> TutorReply:
        return await service.answer(body.model_copy(update={"mode": "hint"}))

    return router


def local_tutor_router(service: TutorService) -> APIRouter:
    return tutor_router(service, loopback_only, prefix="/demo/tutor")
