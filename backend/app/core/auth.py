"""Local Argon2 credentials and opaque server-side sessions."""

import secrets
from collections import deque
from hashlib import sha256
from threading import BoundedSemaphore, Lock
from time import monotonic, time
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Request, Response
from sqlalchemy import delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import AuthSession, Profile, User
from app.schemas.account import Credentials, Me, ProfileInput
from app.services.assessment import AssessmentError

COOKIE = "dbms_session"
SESSION_SECONDS = 24 * 60 * 60
PASSWORD_HASHER = PasswordHasher(time_cost=2, memory_cost=19_456, parallelism=1)
PASSWORD_SLOTS = BoundedSemaphore(2)


def token_hash(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


class LoginThrottle:
    """Bound a single local service's password checks, including unknown accounts."""

    def __init__(self, maximum: int = 15, window_seconds: int = 60):
        self.timestamps: deque[float] = deque()
        self.maximum = maximum
        self.window_seconds = window_seconds
        self.lock = Lock()

    def check(self) -> None:
        now = monotonic()
        with self.lock:
            while self.timestamps and self.timestamps[0] <= now - self.window_seconds:
                self.timestamps.popleft()
            if len(self.timestamps) >= self.maximum:
                raise AssessmentError(
                    "Too many account requests. Try again in a minute.", "rate_limited", 429
                )
            self.timestamps.append(now)


def read_me(db: Session, user: User) -> Me:
    if user.email is None:
        raise AssessmentError("Sign in to continue.", "sign_in_required", 401)
    profile = db.get(Profile, user.id)
    preferences = (
        ProfileInput()
        if profile is None
        else ProfileInput.model_validate(
            {"goal": profile.goal, "level": profile.level, "daily_minutes": profile.daily_minutes}
        )
    )
    return Me(email=user.email, created_at=user.created_at, preferences=preferences)


class Accounts:
    def __init__(self, engine: Engine, *, secure_cookie: bool):
        self.engine = engine
        self.secure_cookie = secure_cookie
        self.throttle = LoginThrottle()
        self.dummy_hash = PASSWORD_HASHER.hash("unused local authentication sentinel")

    def set_cookie(self, response: Response, token: str) -> None:
        response.set_cookie(
            COOKIE,
            token,
            max_age=SESSION_SECONDS,
            secure=self.secure_cookie,
            httponly=True,
            samesite="lax",
            path="/",
        )

    def drop_cookie(self, response: Response) -> None:
        response.delete_cookie(
            COOKIE, path="/", httponly=True, secure=self.secure_cookie, samesite="lax"
        )

    def issue(self, db: Session, user_id: str) -> str:
        now = int(time())
        db.execute(
            delete(AuthSession).where(AuthSession.user_id == user_id, AuthSession.expires_at <= now)
        )
        token = secrets.token_urlsafe(32)
        db.add(
            AuthSession(
                id=uuid4().hex,
                user_id=user_id,
                token_hash=token_hash(token),
                expires_at=now + SESSION_SECONDS,
            )
        )
        return token

    def register(self, credentials: Credentials) -> tuple[Me, str]:
        self.throttle.check()
        if not PASSWORD_SLOTS.acquire(blocking=False):
            raise AssessmentError("Account service is busy. Try again.", "auth_busy", 503)
        try:
            hashed = PASSWORD_HASHER.hash(credentials.password)
        finally:
            PASSWORD_SLOTS.release()
        try:
            with Session(self.engine) as db, db.begin():
                user = User(
                    id=uuid4().hex,
                    email=credentials.email.casefold(),
                    password_hash=hashed,
                    created_at=int(time()),
                    is_demo=False,
                )
                db.add(user)
                db.flush()
                return read_me(db, user), self.issue(db, user.id)
        except IntegrityError as error:
            raise AssessmentError(
                "An account already uses this email.", "email_exists", 409
            ) from error

    def login(self, credentials: Credentials) -> tuple[Me, str]:
        self.throttle.check()
        with Session(self.engine) as db:
            user = db.scalar(
                select(User).where(
                    User.email == credentials.email.casefold(), User.is_demo.is_(False)
                )
            )
            user_id = user.id if user is not None else None
            hashed = user.password_hash if user is not None and user.disabled_at is None else None
        if not PASSWORD_SLOTS.acquire(blocking=False):
            raise AssessmentError("Account service is busy. Try again.", "auth_busy", 503)
        try:
            matched: bool = PASSWORD_HASHER.verify(hashed or self.dummy_hash, credentials.password)
        except (VerificationError, InvalidHashError):
            matched = False
        finally:
            PASSWORD_SLOTS.release()
        if not matched or user_id is None or hashed is None:
            raise AssessmentError("Email or password is incorrect.", "invalid_credentials", 401)
        with Session(self.engine) as db, db.begin():
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            current = db.get(User, user_id)
            if (
                current is None
                or current.disabled_at is not None
                or current.password_hash != hashed
            ):
                raise AssessmentError("Email or password is incorrect.", "invalid_credentials", 401)
            return read_me(db, current), self.issue(db, user_id)

    def require_user(self, request: Request) -> str:
        token = request.cookies.get(COOKIE, "")
        if len(token) == 43 and token.isascii():
            with Session(self.engine) as db:
                user_id = db.scalar(
                    select(User.id)
                    .join(AuthSession, AuthSession.user_id == User.id)
                    .where(
                        AuthSession.token_hash == token_hash(token),
                        AuthSession.revoked_at.is_(None),
                        AuthSession.expires_at > int(time()),
                        User.is_demo.is_(False),
                        User.disabled_at.is_(None),
                    )
                )
                if user_id is not None:
                    return user_id
        raise AssessmentError("Sign in to continue.", "sign_in_required", 401)

    def revoke(self, request: Request) -> None:
        token = request.cookies.get(COOKIE, "")
        if len(token) == 43 and token.isascii():
            with Session(self.engine) as db, db.begin():
                session = db.scalar(
                    select(AuthSession).where(AuthSession.token_hash == token_hash(token))
                )
                if session is not None:
                    session.revoked_at = int(time())
