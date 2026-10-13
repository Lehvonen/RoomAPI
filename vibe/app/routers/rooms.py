import sqlite3
from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..db import from_db, get_db, now_utc, to_db, to_utc
from ..schemas import Availability, RoomCreate, RoomOut, RoomUpdate, TimeSlot
from ..security import get_current_user, require_admin

router = APIRouter(prefix="/rooms", tags=["rooms"])

MAX_AVAILABILITY_WINDOW = timedelta(days=31)


def room_out(row: sqlite3.Row) -> RoomOut:
    return RoomOut(
        id=row["id"],
        name=row["name"],
        capacity=row["capacity"],
        location=row["location"],
        description=row["description"],
        is_active=bool(row["is_active"]),
        created_at=from_db(row["created_at"]),
        updated_at=from_db(row["updated_at"]),
    )


def get_room_or_404(db: sqlite3.Connection, room_id: int, user: sqlite3.Row) -> sqlite3.Row:
    row = db.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
    # Inactive rooms are hidden from regular users.
    if row is None or (not row["is_active"] and not user["is_admin"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return row


@router.get("", response_model=list[RoomOut])
def list_rooms(
    min_capacity: int | None = Query(default=None, ge=1),
    include_inactive: bool = Query(default=False, description="Admins only"),
    user: sqlite3.Row = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    sql = "SELECT * FROM rooms WHERE 1 = 1"
    params: list = []
    if not (include_inactive and user["is_admin"]):
        sql += " AND is_active = 1"
    if min_capacity is not None:
        sql += " AND capacity >= ?"
        params.append(min_capacity)
    sql += " ORDER BY name"
    return [room_out(r) for r in db.execute(sql, params)]


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(
    body: RoomCreate,
    _: sqlite3.Row = Depends(require_admin),
    db: sqlite3.Connection = Depends(get_db),
):
    now = to_db(now_utc())
    try:
        cur = db.execute(
            "INSERT INTO rooms (name, capacity, location, description, is_active, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (body.name, body.capacity, body.location, body.description, int(body.is_active), now, now),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A room with that name already exists")
    return room_out(db.execute("SELECT * FROM rooms WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.get("/{room_id}", response_model=RoomOut)
def get_room(room_id: int, user: sqlite3.Row = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    return room_out(get_room_or_404(db, room_id, user))


@router.patch("/{room_id}", response_model=RoomOut)
def update_room(
    room_id: int,
    body: RoomUpdate,
    admin: sqlite3.Row = Depends(require_admin),
    db: sqlite3.Connection = Depends(get_db),
):
    get_room_or_404(db, room_id, admin)
    changes = body.model_dump(exclude_unset=True)
    if changes:
        if "is_active" in changes:
            changes["is_active"] = int(changes["is_active"])
        changes["updated_at"] = to_db(now_utc())
        assignments = ", ".join(f"{col} = ?" for col in changes)  # columns come from the schema, not the client
        try:
            db.execute(f"UPDATE rooms SET {assignments} WHERE id = ?", (*changes.values(), room_id))
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A room with that name already exists")
    return room_out(db.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone())


@router.get("/{room_id}/availability", response_model=Availability)
def room_availability(
    room_id: int,
    start: datetime | None = Query(default=None, description="Window start (default: today 00:00 UTC)"),
    end: datetime | None = Query(default=None, description="Window end (default: start + 1 day)"),
    user: sqlite3.Row = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Booked and free time slots for a room within a time window (max 31 days)."""
    get_room_or_404(db, room_id, user)
    start = to_utc(start) if start else datetime.combine(now_utc().date(), time.min, tzinfo=timezone.utc)
    end = to_utc(end) if end else start + timedelta(days=1)
    if end <= start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end must be after start")
    if end - start > MAX_AVAILABILITY_WINDOW:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Window may be at most 31 days")

    rows = db.execute(
        "SELECT start_time, end_time FROM bookings"
        " WHERE room_id = ? AND status = 'active' AND start_time < ? AND end_time > ?"
        " ORDER BY start_time",
        (room_id, to_db(end), to_db(start)),
    ).fetchall()

    booked: list[TimeSlot] = []
    free: list[TimeSlot] = []
    cursor = start
    for r in rows:
        b_start = max(from_db(r["start_time"]), start)
        b_end = min(from_db(r["end_time"]), end)
        booked.append(TimeSlot(start=b_start, end=b_end))
        if b_start > cursor:
            free.append(TimeSlot(start=cursor, end=b_start))
        cursor = max(cursor, b_end)
    if cursor < end:
        free.append(TimeSlot(start=cursor, end=end))

    return Availability(room_id=room_id, start=start, end=end, booked=booked, free=free)
