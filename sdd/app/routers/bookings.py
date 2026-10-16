"""Bookings (User Story 2: FR-011–FR-013, FR-017, NFR-005; User Story 4: FR-014–FR-016)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import MAX_ID
from ..db import get_session
from ..models import Booking, Room, User, utcnow
from ..schemas import BookingCreate, BookingOut
from ..security import get_current_user
from ..timerules import BookingRuleError, check_booking_window

router = APIRouter(tags=["bookings"])

BookingId = Annotated[int, Path(ge=1, le=MAX_ID)]


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


@router.get("/bookings/me", response_model=list[BookingOut])
def my_bookings(user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> list[BookingOut]:
    """Your own active bookings that haven't ended, oldest first (FR-014)."""
    rows = session.execute(
        select(Booking, Room.name)
        .join(Room, Room.id == Booking.room_id)
        .where(Booking.user_id == user.id, Booking.status == "active", Booking.end_time > utcnow())
        .order_by(Booking.start_time)
    )
    return [booking_out(booking, room_name) for booking, room_name in rows]


@router.delete(
    "/bookings/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"description": "Not your booking"},
        404: {"description": "Booking not found"},
        409: {"description": "Already cancelled, or already ended"},
    },
)
def cancel_booking(
    booking_id: BookingId,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Response:
    """Cancel your own booking before it ends; admins may cancel any booking (FR-015).

    The booking is kept with its status, cancellation time and who cancelled it.
    There is no endpoint to edit a booking: cancel and book again (FR-016).
    """
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only cancel your own bookings")
    if booking.status == "cancelled":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The booking is already cancelled")
    if booking.end_time <= utcnow() and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The booking has already ended")
    booking.status = "cancelled"
    booking.cancelled_at = utcnow()
    booking.cancelled_by = user.id
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
