import sqlite3
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from ..config import CLOSING_TIME, MAX_BOOKING_LENGTH, OPENING_TIME, SQLITE_MAX_INT
from ..db import from_db, get_db, now_utc, to_db, to_local, transaction
from ..schemas import BookingCreate, BookingOut
from ..security import get_current_user

router = APIRouter(prefix="/bookings", tags=["bookings"])

BOOKING_SELECT = (
    "SELECT b.*, r.name AS room_name, u.username AS username"
    " FROM bookings b JOIN rooms r ON r.id = b.room_id JOIN users u ON u.id = b.user_id"
)


def booking_out(row: sqlite3.Row) -> BookingOut:
    return BookingOut(
        id=row["id"],
        room_id=row["room_id"],
        room_name=row["room_name"],
        user_id=row["user_id"],
        username=row["username"],
        start_time=from_db(row["start_time"]),
        end_time=from_db(row["end_time"]),
        status=row["status"],
        created_at=from_db(row["created_at"]),
        cancelled_at=from_db(row["cancelled_at"]),
    )


BookingId = Annotated[int, Path(ge=1, le=SQLITE_MAX_INT)]


def booking_rule_violation(start: datetime, end: datetime) -> str | None:
    """Check length and opening hours (in local time). Returns the problem, or None."""
    if end - start > MAX_BOOKING_LENGTH:
        return f"A booking may be at most {MAX_BOOKING_LENGTH.total_seconds() / 3600:g} hours long"
    local_start, local_end = to_local(start), to_local(end)
    opening, closing = OPENING_TIME.strftime("%H:%M"), CLOSING_TIME.strftime("%H:%M")
    if (
        local_start.date() != local_end.date()
        or local_start.time() < OPENING_TIME
        or local_end.time() > CLOSING_TIME
    ):
        return f"Rooms can only be booked between {opening} and {closing} local time, within one day"
    return None


def fetch_booking(db: sqlite3.Connection, booking_id: int) -> sqlite3.Row | None:
    return db.execute(f"{BOOKING_SELECT} WHERE b.id = ?", (booking_id,)).fetchone()


def get_visible_booking(db: sqlite3.Connection, booking_id: int, user: sqlite3.Row) -> sqlite3.Row:
    row = fetch_booking(db, booking_id)
    # Other users' bookings are reported as missing rather than forbidden, to avoid leaking IDs.
    if row is None or (row["user_id"] != user["id"] and not user["is_admin"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return row


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    body: BookingCreate,
    user: sqlite3.Row = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    if body.start_time < now_utc():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot book a time in the past")
    problem = booking_rule_violation(body.start_time, body.end_time)
    if problem:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=problem)

    start, end = to_db(body.start_time), to_db(body.end_time)
    with transaction(db):
        room = db.execute("SELECT is_active FROM rooms WHERE id = ?", (body.room_id,)).fetchone()
        if room is None or not room["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        clash = db.execute(
            "SELECT 1 FROM bookings WHERE room_id = ? AND status = 'active' AND start_time < ? AND end_time > ?",
            (body.room_id, end, start),
        ).fetchone()
        if clash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room is already booked for that time")
        cur = db.execute(
            "INSERT INTO bookings (room_id, user_id, start_time, end_time, status, created_at)"
            " VALUES (?, ?, ?, ?, 'active', ?)",
            (body.room_id, user["id"], start, end, to_db(now_utc())),
        )
    return booking_out(fetch_booking(db, cur.lastrowid))


@router.get("", response_model=list[BookingOut])
def list_bookings(
    include_cancelled: bool = False,
    upcoming_only: bool = False,
    all_users: bool = Query(default=False, description="Admins only: list every user's bookings"),
    room_id: int | None = Query(default=None, ge=1, le=SQLITE_MAX_INT),
    user: sqlite3.Row = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Your own bookings. Admins can pass `all_users=true` to see everyone's."""
    if all_users and not user["is_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    sql = f"{BOOKING_SELECT} WHERE 1 = 1"
    params: list = []
    if not all_users:
        sql += " AND b.user_id = ?"
        params.append(user["id"])
    if not include_cancelled:
        sql += " AND b.status = 'active'"
    if upcoming_only:
        sql += " AND b.end_time > ?"
        params.append(to_db(now_utc()))
    if room_id is not None:
        sql += " AND b.room_id = ?"
        params.append(room_id)
    sql += " ORDER BY b.start_time"
    return [booking_out(r) for r in db.execute(sql, params)]


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: BookingId, user: sqlite3.Row = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    return booking_out(get_visible_booking(db, booking_id, user))


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(booking_id: BookingId, user: sqlite3.Row = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    """Cancel a booking. Users may cancel their own; admins may cancel any. The record is kept as 'cancelled'."""
    row = get_visible_booking(db, booking_id, user)
    if row["status"] == "cancelled":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking is already cancelled")
    if from_db(row["end_time"]) <= now_utc() and not user["is_admin"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot cancel a booking that has already ended")
    db.execute(
        "UPDATE bookings SET status = 'cancelled', cancelled_at = ?, cancelled_by = ? WHERE id = ? AND status = 'active'",
        (to_db(now_utc()), user["id"], booking_id),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
