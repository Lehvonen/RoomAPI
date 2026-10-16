"""Rooms and availability (User Story 3: FR-007, FR-010) and room management (User Story 5: FR-008, FR-009)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import MAX_ID
from ..db import get_session
from ..models import Booking, Room, User, utcnow
from ..schemas import Availability, RoomCreate, RoomOut, RoomUpdate, TimeSlot
from ..security import get_current_user, require_admin
from ..timerules import opening_window

router = APIRouter(tags=["rooms"])

RoomId = Annotated[int, Path(ge=1, le=MAX_ID)]
NOT_FOUND = {404: {"description": "Room not found"}}
NAME_TAKEN = "A room with that name already exists"


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
    day: date = Query(alias="date", description="A Helsinki calendar date, YYYY-MM-DD"),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Availability:
    """Booked and free intervals within that Helsinki date's opening hours, in UTC (FR-010)."""
    room = get_visible_room(session, room_id, user)
    opens, closes = opening_window(day)
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

    return Availability(room_id=room.id, date=day, opens_at=opens, closes_at=closes, booked=booked, free=free)


@router.post("/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED,
             responses={403: {"description": "Admin rights required"}, 409: {"description": NAME_TAKEN}})
def create_room(body: RoomCreate, admin: User = Depends(require_admin),
                session: Session = Depends(get_session)) -> Room:
    """Create an active room; names are unique regardless of case (FR-008)."""
    room = Room(**body.model_dump())
    session.add(room)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=NAME_TAKEN) from None
    return room


@router.patch(
    "/rooms/{room_id}",
    response_model=RoomOut,
    responses={
        **NOT_FOUND,
        403: {"description": "Admin rights required"},
        409: {"description": "Name taken, or the room still has active bookings"},
    },
)
def update_room(room_id: RoomId, body: RoomUpdate, admin: User = Depends(require_admin),
                session: Session = Depends(get_session)) -> Room:
    """Edit any of the room's fields. Deactivating is refused while it has bookings that haven't ended (FR-009)."""
    room = get_visible_room(session, room_id, admin)
    changes = body.model_dump(exclude_unset=True)

    if changes.get("is_active") is False and room.is_active:
        blocking = session.scalar(
            select(func.count(Booking.id)).where(
                Booking.room_id == room.id, Booking.status == "active", Booking.end_time > utcnow()
            )
        )
        if blocking:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"The room has {blocking} active booking(s) that haven't ended; cancel them first",
            )

    for field, value in changes.items():
        setattr(room, field, value)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=NAME_TAKEN) from None
    return room
