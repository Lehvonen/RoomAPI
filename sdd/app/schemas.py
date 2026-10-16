"""Shared Pydantic types and response models (contracts/api.md). Request models are added per user story."""

from datetime import date, datetime, timezone
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, Field, PlainSerializer, model_validator

from .config import MAX_ID

# IDs are bounded to the SQLite integer range, so huge numbers get 422, not 500 (NFR-004).
Id = Annotated[int, Field(ge=1, le=MAX_ID)]


def _utc_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Every time returned is UTC with a Z suffix (FR-017).
UTCDatetime = Annotated[datetime, PlainSerializer(_utc_z, return_type=str)]


class UserCreate(BaseModel):
    """Registration (FR-001, FR-002). Unknown fields such as is_admin are ignored (FR-006)."""

    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=10, max_length=128)


class UserOut(BaseModel):
    """Never carries the password or its hash (FR-005, NFR-001)."""

    id: int
    username: str
    is_admin: bool
    created_at: UTCDatetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoomCreate(BaseModel):
    """Room fields and limits from data-model.md (FR-008)."""

    name: str = Field(min_length=1, max_length=100)
    capacity: int = Field(ge=1, le=10_000)
    location: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class RoomUpdate(BaseModel):
    """Any subset of the room's fields (FR-008), plus is_active (FR-009)."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    capacity: int | None = Field(default=None, ge=1, le=10_000)
    location: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None

    @model_validator(mode="after")
    def required_fields_not_null(self):
        # name, capacity and is_active may be left out, but not set to null.
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
    created_at: UTCDatetime
    updated_at: UTCDatetime


class BookingCreate(BaseModel):
    """Times must carry an offset; without one Pydantic answers 422 (FR-017)."""

    room_id: Id
    start_time: AwareDatetime
    end_time: AwareDatetime


class BookingOut(BaseModel):
    id: int
    room_id: int
    room_name: str
    user_id: int
    start_time: UTCDatetime
    end_time: UTCDatetime
    status: Literal["active", "cancelled"]
    created_at: UTCDatetime
    cancelled_at: UTCDatetime | None
    cancelled_by: int | None


class TimeSlot(BaseModel):
    start: UTCDatetime
    end: UTCDatetime


class Availability(BaseModel):
    room_id: int
    date: date
    opens_at: UTCDatetime
    closes_at: UTCDatetime
    booked: list[TimeSlot]
    free: list[TimeSlot]
