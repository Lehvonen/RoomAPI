"""Rooms and availability (User Story 3: FR-007, FR-010)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import MAX_ID
from ..db import get_session
from ..models import Booking, Room, User
from ..schemas import Availability, RoomOut, TimeSlot
from ..security import get_current_user
from ..timerules import opening_window

router = APIRouter(tags=["rooms"])

RoomId = Annotated[int, Path(ge=1, le=MAX_ID)]
NOT_FOUND = {404: {"description": "Room not found"}}


def get_visible_room(session: Session, room_id: int, user: User) -> Room:
    """Inactive rooms are hidden from regular users (FR-007, FR-009)."""
    room = session.get(Room, room_id)
    if room is None or (not room.is_active and not user.is_admin):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


@router.get("/rooms", response_model=list[RoomOut])
def list_rooms(user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> list[Room]:
    """Active rooms, ordered by name (FR-007)."""
    return list(session.scalars(select(Room).where(Room.is_active.is_(True)).order_by(Room.name)))


@router.get("/rooms/{room_id}", response_model=RoomOut, responses=NOT_FOUND)
def get_room(room_id: RoomId, user: User = Depends(get_current_user),
             session: Session = Depends(get_session)) -> Room:
    return get_visible_room(session, room_id, user)


@router.get("/rooms/{room_id}/availability", response_model=Availability, responses=NOT_FOUND)
def room_availability(
    room_id: RoomId,
    date: date,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Availability:
    """Booked and free intervals within that Helsinki date's opening hours, in UTC (FR-010)."""
    room = get_visible_room(session, room_id, user)
    opens, closes = opening_window(date)
    bookings = session.scalars(
        select(Booking)
        .where(
            Booking.room_id == room.id,
            Booking.status == "active",
            Booking.start_time < closes,
            Booking.end_time > opens,
        )
        .order_by(Booking.start_time)
    )

    booked: list[TimeSlot] = []
    free: list[TimeSlot] = []
    cursor = opens
    for b in bookings:
        start, end = max(b.start_time, opens), min(b.end_time, closes)
        booked.append(TimeSlot(start=start, end=end))
        if start > cursor:
            free.append(TimeSlot(start=cursor, end=start))
        cursor = max(cursor, end)
    if cursor < closes:
        free.append(TimeSlot(start=cursor, end=closes))

    return Availability(room_id=room.id, date=date, opens_at=opens, closes_at=closes, booked=booked, free=free)
