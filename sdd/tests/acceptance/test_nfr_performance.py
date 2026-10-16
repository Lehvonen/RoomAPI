"""NFR-006: with 1,000 bookings stored, each request completes in under 500 ms (logins delayed by NFR-009 excepted)."""

import time
from datetime import datetime, timedelta, timezone

import pytest

from .. import conftest
from ..conftest import PASSWORD, book, helsinki, helsinki_date, unique

pytestmark = pytest.mark.skipif(conftest.external(), reason="seeds 1,000 bookings directly in the test database")

LIMIT = 0.5
BOOKINGS = 1000


def seed(db_path: str, room_ids: list[int], user_id: int) -> None:
    from sqlalchemy.orm import Session

    from app.db import make_engine
    from app.models import Booking

    engine = make_engine(db_path)
    base = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(days=5)
    try:
        with Session(engine) as session:
            for i in range(BOOKINGS):
                start = base + timedelta(days=i // len(room_ids))
                session.add(Booking(room_id=room_ids[i % len(room_ids)], user_id=user_id,
                                    start_time=start, end_time=start + timedelta(minutes=30)))
            session.commit()
    finally:
        engine.dispose()


def timed(call):
    start = time.perf_counter()
    r = call()
    return r, time.perf_counter() - start


def test_every_operation_under_500_ms_with_1000_bookings(client, db_path, admin):
    rooms = [conftest.create_room(client, db_path, admin) for _ in range(20)]
    name = unique("alice")
    client.post("/auth/register", json={"username": name, "password": PASSWORD})
    user = conftest.login(client, name)
    me = client.get("/users/me", headers=user).json()
    seed(db_path, [r["id"] for r in rooms], me["id"])
    room = rooms[0]

    operations = {
        "register": lambda: client.post("/auth/register", json={"username": unique("bob"), "password": PASSWORD}),
        "login": lambda: client.post("/auth/login", data={"username": name, "password": PASSWORD}),
        "users/me": lambda: client.get("/users/me", headers=user),
        "list rooms": lambda: client.get("/rooms", headers=user),
        "get room": lambda: client.get(f"/rooms/{room['id']}", headers=user),
        "availability": lambda: client.get(f"/rooms/{room['id']}/availability",
                                           params={"date": helsinki_date(2).isoformat()}, headers=user),
        "book": lambda: book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)),
        "my bookings": lambda: client.get("/bookings/me", headers=user),
        "create room": lambda: client.post("/rooms", json={"name": unique("room"), "capacity": 4}, headers=admin),
        "edit room": lambda: client.patch(f"/rooms/{rooms[1]['id']}", json={"capacity": 5}, headers=admin),
    }
    results = {}
    for label, call in operations.items():
        r, elapsed = timed(call)
        assert r.status_code < 400, (label, r.status_code, r.text)
        results[label] = elapsed
    booking_id = client.get("/bookings/me", headers=user).json()[0]["id"]
    r, results["cancel"] = timed(lambda: client.delete(f"/bookings/{booking_id}", headers=user))
    assert r.status_code == 204

    slow = {k: round(v, 3) for k, v in results.items() if v >= LIMIT}
    assert not slow, f"over {LIMIT * 1000:.0f} ms: {slow}"
