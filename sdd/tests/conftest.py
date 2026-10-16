"""Black-box test harness (research R7).

By default each test gets an in-process app on a fresh temporary database, so coverage
is measured. With ROOMAPI_BASE_URL set, the same tests run over HTTP against that
server instead, for example the vibe-coded version. Then ROOMAPI_TEST_ADMIN and
ROOMAPI_TEST_ADMIN_PASSWORD name an existing admin account.
"""

import os
import uuid
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

# Must be set before the app is created.
os.environ.setdefault("ROOMAPI_SECRET_KEY", "test-secret-key-that-is-long-enough-for-hs256")
os.environ.setdefault("ROOMAPI_LOGIN_DELAY_SECONDS", "0.2")

import httpx  # noqa: E402
import pytest  # noqa: E402

HELSINKI = ZoneInfo("Europe/Helsinki")
PASSWORD = "Correct-horse-42"  # 10–128 characters (FR-002)
BASE_URL = os.environ.get("ROOMAPI_BASE_URL")


def external() -> bool:
    return BASE_URL is not None


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / "test.db")


@pytest.fixture
def client(db_path):
    if external():
        with httpx.Client(base_url=BASE_URL, timeout=30) as c:
            yield c
    else:
        from fastapi.testclient import TestClient

        from app.main import create_app

        with TestClient(create_app(db_path)) as c:
            yield c


def unique(prefix: str) -> str:
    """Unique usernames and room names, so tests don't collide on a shared external server."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def login(client, username: str, password: str = PASSWORD) -> dict[str, str]:
    r = client.post("/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def register_and_login(client, username: str | None = None, password: str = PASSWORD) -> dict[str, str]:
    username = username or unique("user")
    r = client.post("/auth/register", json={"username": username, "password": password})
    assert r.status_code == 201, r.text
    return login(client, username, password)


@pytest.fixture
def admin(client, db_path) -> dict[str, str]:
    if external():
        return login(client, os.environ["ROOMAPI_TEST_ADMIN"], os.environ["ROOMAPI_TEST_ADMIN_PASSWORD"])
    from app.cli import create_admin

    create_admin(db_path, "admin", PASSWORD)
    return login(client, "admin")


@pytest.fixture
def user(client) -> dict[str, str]:
    return register_and_login(client)


@pytest.fixture
def other_user(client) -> dict[str, str]:
    return register_and_login(client)


def helsinki_date(days_ahead: int) -> date:
    return (datetime.now(HELSINKI) + timedelta(days=days_ahead)).date()


def helsinki(days_ahead: int, hh: int, mm: int = 0) -> str:
    """ISO time with the correct Helsinki offset for that day (summer or winter time)."""
    return datetime.combine(helsinki_date(days_ahead), time(hh, mm), tzinfo=HELSINKI).isoformat()


def create_room(client, db_path: str, admin_headers: dict[str, str], *, name: str | None = None,
                capacity: int = 8, active: bool = True) -> dict:
    """Set up a room. In-process it is written to the test database directly, because room
    management (US5) is built later; against an external server it goes through the admin API."""
    name = name or unique("room")
    if external():
        r = client.post("/rooms", json={"name": name, "capacity": capacity}, headers=admin_headers)
        assert r.status_code == 201, r.text
        room = r.json()
        if not active:
            r = client.patch(f"/rooms/{room['id']}", json={"is_active": False}, headers=admin_headers)
            assert r.status_code == 200, r.text
        return room
    from sqlalchemy.orm import Session

    from app.db import make_engine
    from app.models import Room

    engine = make_engine(db_path)
    try:
        with Session(engine) as session:
            room = Room(name=name, capacity=capacity, is_active=active)
            session.add(room)
            session.commit()
            return {"id": room.id, "name": room.name}
    finally:
        engine.dispose()


@pytest.fixture
def room(client, db_path, admin) -> dict:
    return create_room(client, db_path, admin)


def book(client, headers: dict[str, str], room_id: int, start: str, end: str):
    return client.post("/bookings", json={"room_id": room_id, "start_time": start, "end_time": end}, headers=headers)


def insert_ended_booking(db_path: str, room_id: int, username: str) -> int:
    """In-process only: a booking that has already ended, which the API can't create (FR-011)."""
    from datetime import timezone

    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from app.db import make_engine
    from app.models import Booking, User

    engine = make_engine(db_path)
    try:
        with Session(engine) as session:
            user_id = session.scalars(select(User.id).where(User.username == username)).one()
            end = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(hours=1)
            booking = Booking(room_id=room_id, user_id=user_id, start_time=end - timedelta(hours=1), end_time=end)
            session.add(booking)
            session.commit()
            return booking.id
    finally:
        engine.dispose()


def booking_row(db_path: str, booking_id: int) -> dict:
    """In-process only: the stored booking, for checking status and who cancelled it (FR-015)."""
    import sqlite3

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        return dict(conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone())
