"""Shared Pydantic types and response models (contracts/api.md). Request models are added per user story."""

from datetime import date, datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, Field, PlainSerializer

from .config import MAX_ID

# IDs are bounded to the SQLite integer range, so huge numbers get 422, not 500 (NFR-004).
Id = Annotated[int, Field(ge=1, le=MAX_ID)]


def _utc_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Every time returned is UTC with a Z suffix (FR-017).
UTCDatetime = Annotated[datetime, PlainSerializer(_utc_z, return_type=str)]


class UserOut(BaseModel):
    """Never carries the password or its hash (FR-005, NFR-001)."""

    id: int
    username: str
    is_admin: bool
    created_at: UTCDatetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoomOut(BaseModel):
    id: int
    name: str
    capacity: int
    location: str | None
    description: str | None
    is_active: bool
    created_at: UTCDatetime
    updated_at: UTCDatetime


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
