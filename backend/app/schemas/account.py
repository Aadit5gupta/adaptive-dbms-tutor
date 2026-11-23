"""Local account and profile contracts."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

Goal = Literal["exam", "placements", "understanding"]
Level = Literal["beginner", "some_experience", "advanced"]


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=10, max_length=128)]


class ProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: Goal | None = None
    level: Level | None = None
    daily_minutes: Annotated[int, Field(strict=True, ge=5, le=180)] | None = None


class Me(BaseModel):
    email: str
    created_at: int
    preferences: ProfileInput
