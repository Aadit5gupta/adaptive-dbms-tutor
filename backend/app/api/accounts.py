"""Account, preference and privacy endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import Accounts, read_me
from app.db.models import (
    AssessmentSession,
    Attempt,
    Mastery,
    MasteryHistory,
    MisconceptionEvidence,
    PolicyDecision,
    Profile,
    Recommendation,
    User,
    UserMisconception,
)
from app.schemas.account import Credentials, Me, ProfileInput
from app.services.assessment import AssessmentError


def account_router(accounts: Accounts) -> APIRouter:
    router = APIRouter()

    @router.post("/auth/register", status_code=201)
    def register(body: Credentials, response: Response) -> Me:
        view, token = accounts.register(body)
        accounts.set_cookie(response, token)
        return view

    @router.post("/auth/login")
    def login(body: Credentials, response: Response) -> Me:
        view, token = accounts.login(body)
        accounts.set_cookie(response, token)
        return view

    @router.post("/auth/logout")
    def logout(request: Request, response: Response) -> dict[str, bool]:
        accounts.revoke(request)
        accounts.drop_cookie(response)
        return {"ok": True}

    @router.get("/me")
    def me(user_id: Annotated[str, Depends(accounts.require_user)]) -> Me:
        with Session(accounts.engine) as db:
            return read_me(db, require_account(db, user_id))

    @router.patch("/me")
    def preferences(
        body: ProfileInput, user_id: Annotated[str, Depends(accounts.require_user)]
    ) -> Me:
        with Session(accounts.engine) as db, db.begin():
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            user = require_account(db, user_id)
            profile = db.get(Profile, user_id)
            if profile is None:
                profile = Profile(user_id=user_id)
                db.add(profile)
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(profile, key, value)
            db.flush()
            return read_me(db, user)

    @router.get("/me/export")
    def export(
        response: Response, user_id: Annotated[str, Depends(accounts.require_user)]
    ) -> dict[str, Any]:
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Disposition"] = 'attachment; filename="adaptive-dbms-data.json"'
        with Session(accounts.engine) as db, db.begin():
            result: dict[str, Any] = {
                "profile": read_me(db, require_account(db, user_id)).model_dump()
            }
            for model in (
                AssessmentSession,
                Attempt,
                Mastery,
                MasteryHistory,
                MisconceptionEvidence,
                UserMisconception,
                PolicyDecision,
                Recommendation,
            ):
                records = db.scalars(select(model).where(model.user_id == user_id))
                keys = [
                    key.key
                    for key in model.__mapper__.column_attrs
                    if key.key not in {"user_id", "idempotency_key", "request_fingerprint"}
                ]
                result[model.__tablename__] = [
                    {key: getattr(row, key) for key in keys} for row in records
                ]
            return result

    @router.delete("/me")
    def delete_account(
        response: Response, user_id: Annotated[str, Depends(accounts.require_user)]
    ) -> dict[str, bool]:
        with Session(accounts.engine) as db, db.begin():
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            db.delete(require_account(db, user_id))
        accounts.drop_cookie(response)
        return {"ok": True}

    return router


def require_account(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None or user.disabled_at is not None or user.is_demo:
        raise AssessmentError("Sign in to continue.", "sign_in_required", 401)
    return user
