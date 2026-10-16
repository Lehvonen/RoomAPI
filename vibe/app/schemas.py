"""Request and response models."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .config import SQLITE_MAX_INT
from .db import to_utc

# Database IDs are positive and must fit in SQLite's 64-bit INTEGER.
DbId = Annotated[int, Field(ge=1, le=SQLITE_MAX_INT)]

PASSWORD_MIN_LENGTH = 10
PASSWORD_MIN_DISTINCT_CHARS = 5
# Small blocklist of very common passwords that would otherwise pass the rules below.
COMMON_PASSWORDS = {
    "password1", "password12", "password123", "password1234", "passw0rd123",
    "qwerty1234", "qwerty12345", "qwertyuiop1", "1q2w3e4r5t", "1qaz2wsx3edc",
    "abc1234567", "abcd123456", "iloveyou12", "welcome123", "letmein123",
    "admin12345", "salasana12", "salasana123", "salasana1234",
}


def password_problem(password: str, username: str) -> str | None:
    """Return why a password is too weak, or None if it is acceptable."""
    if len(password) < PASSWORD_MIN_LENGTH:
        return f"password must be at least {PASSWORD_MIN_LENGTH} characters"
    if not any(c.isalpha() for c in password) or all(c.isalpha() for c in password):
        return "password must contain letters and at least one digit or symbol"
    if len(set(password.lower())) < PASSWORD_MIN_DISTINCT_CHARS:
        return f"password must contain at least {PASSWORD_MIN_DISTINCT_CHARS} different characters"
    if username and username.lower() in password.lower():
        return "password must not contain the username"
    if password.lower() in COMMON_PASSWORDS:
        return "password is too common"
    return None


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=128,
        description="At least 10 characters with letters and a digit or symbol, at least 5 different "
        "characters, not containing the username, and not a common password",
    )

    @model_validator(mode="after")
    def strong_password(self):
        problem = password_problem(self.password, self.username)
        if problem:
            raise ValueError(problem)
        return self


class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    capacity: int = Field(ge=1, le=10_000)
    location: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool = True


class RoomUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    capacity: int | None = Field(default=None, ge=1, le=10_000)
    location: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None

    @model_validator(mode="after")
    def no_null_required_fields(self):
        # name/capacity/is_active may be omitted but not explicitly set to null.
        for field in ("name", "capacity", "is_active"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class RoomOut(BaseModel):
    id: int
    name: str
    capacity: int
    location: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TimeSlot(BaseModel):
    start: datetime
    end: datetime


class Availability(BaseModel):
    room_id: int
    start: datetime
    end: datetime
    booked: list[TimeSlot]
    free: list[TimeSlot]


class BookingCreate(BaseModel):
    room_id: DbId
    start_time: datetime = Field(description="ISO-8601; times without an offset are Finnish local time")
    end_time: datetime = Field(description="ISO-8601; times without an offset are Finnish local time")

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize(cls, v: datetime) -> datetime:
        return to_utc(v)

    @model_validator(mode="after")
    def check_order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class BookingOut(BaseModel):
    id: int
    room_id: int
    room_name: str
    user_id: int
    username: str
    start_time: datetime
    end_time: datetime
    status: Literal["active", "cancelled"]
    created_at: datetime
    cancelled_at: datetime | None
