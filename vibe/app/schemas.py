"""Request and response models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .db import to_utc


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


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
    room_id: int
    start_time: datetime = Field(description="ISO-8601; times without an offset are treated as UTC")
    end_time: datetime = Field(description="ISO-8601; times without an offset are treated as UTC")

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
