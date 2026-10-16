"""Probe of the round-1 vibe API (issue #11).

Runs each check against a fresh throwaway database through FastAPI's TestClient
and prints one line per check. It does not modify anything in vibe/.

Mostly black-box: checks go through the HTTP API only. Two white-box exceptions:
setup() creates the admin with app.cli.create_admin (there is no API for it),
and OK5 reads the stored password hash straight from SQLite.

The probe lowers ROOMAPI_PBKDF2_ITERATIONS to 1000 for speed; the shipped
default in vibe/app/security.py is 600 000.

Run from the repo root with the vibe venv:
    Windows:      PYTHONPATH=vibe vibe/.venv/Scripts/python docs/evidence/vibe-round-1/probe.py
    macOS/Linux:  PYTHONPATH=vibe vibe/.venv/bin/python docs/evidence/vibe-round-1/probe.py
"""

import os
import sqlite3
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

os.environ.setdefault("ROOMAPI_PBKDF2_ITERATIONS", "1000")
os.environ.setdefault("ROOMAPI_SECRET_KEY", "probe-secret-key-that-is-long-enough-for-hs256")

from fastapi.testclient import TestClient  # noqa: E402

from app.cli import create_admin  # noqa: E402
from app.main import create_app  # noqa: E402

TOMORROW = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)


def iso(dt):
    return dt.isoformat()


def login(client, username, password):
    r = client.post("/auth/login", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@contextmanager
def fresh_api():
    """A new app on an empty database with an admin, user alice and room Aurora; cleaned up afterwards."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "probe.db")
        with TestClient(create_app(db), raise_server_exceptions=False) as client:
            create_admin(db, "admin", "adminpass123")
            admin = login(client, "admin", "adminpass123")
            client.post("/auth/register", json={"username": "alice", "password": "password123"})
            alice = login(client, "alice", "password123")
            room = client.post("/rooms", json={"name": "Aurora", "capacity": 8}, headers=admin).json()
            yield client, admin, alice, room, db


def book(client, h, room_id, start, end):
    return client.post("/bookings", json={"room_id": room_id, "start_time": start, "end_time": end}, headers=h)


def report(pid, what, r, note=""):
    print(f"{pid} | {what} | HTTP {r.status_code} | {note}")


def main():
    # P1 Booking length is unbounded
    with fresh_api() as (c, admin, alice, room, _):
        r = book(c, alice, room["id"], iso(TOMORROW), iso(TOMORROW + timedelta(days=3650)))
        report("P1", "alice books one room for 10 years", r, "accepted" if r.status_code == 201 else r.text)

    # P2 No opening hours
    with fresh_api() as (c, admin, alice, room, _):
        r = book(c, alice, room["id"], iso(TOMORROW + timedelta(hours=3)), iso(TOMORROW + timedelta(hours=4)))
        report("P2", "booking 03:00-04:00 UTC", r, "accepted" if r.status_code == 201 else r.text)

    # P3 Deactivating a room leaves its future bookings active
    with fresh_api() as (c, admin, alice, room, _):
        b = book(c, alice, room["id"], iso(TOMORROW + timedelta(hours=9)), iso(TOMORROW + timedelta(hours=10))).json()
        c.patch(f"/rooms/{room['id']}", json={"is_active": False}, headers=admin)
        r = c.get(f"/bookings/{b['id']}", headers=alice)
        rr = c.get(f"/rooms/{room['id']}", headers=alice)
        report("P3", "room deactivated after alice booked it", r,
               f"booking status={r.json().get('status')}, room lookup for alice HTTP {rr.status_code}")

    # P4 Huge integer IDs cause an unhandled error
    with fresh_api() as (c, admin, alice, room, _):
        r = c.get(f"/rooms/{2**70}", headers=alice)
        report("P4a", "GET /rooms/2**70", r, r.text[:80])
        r = book(c, alice, 2**70, iso(TOMORROW + timedelta(hours=9)), iso(TOMORROW + timedelta(hours=10)))
        report("P4b", "POST /bookings with room_id 2**70", r, r.text[:80])

    # P5 A date at the edge of the calendar causes an unhandled error
    with fresh_api() as (c, admin, alice, room, _):
        r = book(c, alice, room["id"], "9999-12-31T23:00:00-05:00", "9999-12-31T23:30:00-05:00")
        report("P5", "booking on 9999-12-31 at UTC-5 (overflows year 9999 in UTC)", r, r.text[:80])

    # P6 Times without an offset are silently read as UTC
    with fresh_api() as (c, admin, alice, room, _):
        local = TOMORROW.replace(tzinfo=None) + timedelta(hours=9)
        r = book(c, alice, room["id"], local.isoformat(), (local + timedelta(hours=1)).isoformat())
        report("P6", f"booking sent as naive {local.time()} (meant as Helsinki summer time, UTC+3)", r,
               f"stored start_time={r.json().get('start_time')} (09:00 UTC = 12:00 Helsinki summer time)")

    # P7 Weak passwords accepted
    with fresh_api() as (c, admin, alice, room, _):
        r = c.post("/auth/register", json={"username": "weak", "password": "aaaaaaaa"})
        report("P7", "register with password 'aaaaaaaa'", r, "accepted" if r.status_code == 201 else r.text)

    # P8 No limit on failed logins
    with fresh_api() as (c, admin, alice, room, _):
        codes = {c.post("/auth/login", data={"username": "alice", "password": f"wrong{i}"}).status_code for i in range(50)}
        r = c.post("/auth/login", data={"username": "alice", "password": "password123"})
        report("P8", "50 wrong passwords, then the right one", r, f"wrong attempts returned {sorted(codes)}; no lockout or delay")

    # Checks that held
    with fresh_api() as (c, admin, alice, room, db):
        c.post("/auth/register", json={"username": "bob", "password": "password123"})
        bob = login(c, "bob", "password123")
        a = book(c, alice, room["id"], iso(TOMORROW + timedelta(hours=9)), iso(TOMORROW + timedelta(hours=10))).json()
        r = book(c, bob, room["id"], iso(TOMORROW + timedelta(hours=9, minutes=30)), iso(TOMORROW + timedelta(hours=11)))
        report("OK1", "overlapping booking on the same room", r, "rejected" if r.status_code == 409 else "ACCEPTED")
        r = c.delete(f"/bookings/{a['id']}", headers=bob)
        report("OK2", "bob cancels alice's booking", r, "refused" if r.status_code == 404 else "ALLOWED")
        r = book(c, alice, room["id"], iso(TOMORROW - timedelta(days=2)), iso(TOMORROW - timedelta(days=2) + timedelta(hours=1)))
        report("OK3", "booking in the past", r, "rejected" if r.status_code == 422 else "ACCEPTED")
        r = book(c, alice, room["id"], iso(TOMORROW + timedelta(hours=12)), iso(TOMORROW + timedelta(hours=11)))
        report("OK4", "end before start", r, "rejected" if r.status_code == 422 else "ACCEPTED")
        conn = sqlite3.connect(db)
        h = conn.execute("SELECT password_hash FROM users WHERE username='alice'").fetchone()[0]
        conn.close()
        print(f"OK5 | password storage (white-box: read from SQLite) | - | stored as {h.split('$')[0]} (salted hash, not plain text)")


if __name__ == "__main__":
    main()
