"""Bookings (User Story 2: FR-011–FR-013, FR-017; NFR-005)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import Booking, Room, User, utcnow
from ..schemas import BookingCreate, BookingOut
from ..security import get_current_user
from ..timerules import BookingRuleError, check_booking_window

router = APIRouter(tags=["bookings"])


def booking_out(booking: Booking, room_name: str) -> BookingOut:
    return BookingOut(
        id=booking.id,
        room_id=booking.room_id,
        room_name=room_name,
        user_id=booking.user_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        created_at=booking.created_at,
        cancelled_at=booking.cancelled_at,
        cancelled_by=booking.cancelled_by,
    )


@router.post(
    "/bookings",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Room not found or inactive"},
        409: {"description": "Overlaps an existing booking"},
        422: {"description": "Invalid input or a broken booking rule"},
    },
)
def create_booking(
    body: BookingCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> BookingOut:
    """Book an active room for [start, end). Times need an offset and are returned in UTC."""
    try:
        start, end = check_booking_window(body.start_time, body.end_time, utcnow())
    except BookingRuleError as exc:
        # A broken rule is the client's error: 422 with the rule's message, never 500 (NFR-004).
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from None

    # The session's transaction began with BEGIN IMMEDIATE when the user was loaded, so the
    # write lock is held from here to commit: the overlap check and insert are atomic (FR-013).
    room = session.get(Room, body.room_id)
    if room is None or not room.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    clash = session.scalars(
        select(Booking.id).where(
            Booking.room_id == room.id,
            Booking.status == "active",
            Booking.start_time < end,
            Booking.end_time > start,
        )
    ).first()
    if clash is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The room is already booked for that time")

    booking = Booking(room_id=room.id, user_id=user.id, start_time=start, end_time=end)
    session.add(booking)
    session.commit()
    return booking_out(booking, room.name)
