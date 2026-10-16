"""SQLite access: connection handling, schema, and datetime conversion helpers."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from fastapi import Request

from .config import LOCAL_TZ

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "roomapi.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    is_admin      INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS rooms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    capacity    INTEGER NOT NULL CHECK (capacity > 0),
    location    TEXT,
    description TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS bookings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id      INTEGER NOT NULL REFERENCES rooms(id),
    user_id      INTEGER NOT NULL REFERENCES users(id),
    start_time   TEXT    NOT NULL,
    end_time     TEXT    NOT NULL,
    status       TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled')),
    created_at   TEXT    NOT NULL,
    cancelled_at TEXT,
    cancelled_by INTEGER REFERENCES users(id),
    CHECK (end_time > start_time)
);

CREATE INDEX IF NOT EXISTS idx_bookings_room_time ON bookings (room_id, status, start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings (user_id, start_time);

CREATE TABLE IF NOT EXISTS failed_logins (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL COLLATE NOCASE,
    ip          TEXT    NOT NULL,
    attempted_at TEXT   NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_failed_logins_user ON failed_logins (username, attempted_at);
CREATE INDEX IF NOT EXISTS idx_failed_logins_ip ON failed_logins (ip, attempted_at);
"""


def db_path() -> str:
    return os.environ.get("ROOMAPI_DB", str(DEFAULT_DB_PATH))


def connect(path: str) -> sqlite3.Connection:
    # isolation_level=None -> autocommit; multi-statement work uses transaction() explicitly.
    conn = sqlite3.connect(path, timeout=10, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: str) -> None:
    conn = connect(path)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)
        # Rooms deactivated before this rule existed may still hold upcoming bookings.
        now = to_db(now_utc())
        conn.execute(
            "UPDATE bookings SET status = 'cancelled', cancelled_at = ?"
            " WHERE status = 'active' AND end_time > ?"
            " AND room_id IN (SELECT id FROM rooms WHERE is_active = 0)",
            (now, now),
        )
    finally:
        conn.close()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Write transaction that takes the write lock up front, so check-then-insert is atomic."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    conn = connect(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()


# All timestamps are stored as UTC ISO-8601 strings with a fixed format, so that
# plain string comparison in SQL matches chronological order. Times sent without
# an offset are local time (LOCAL_TZ); responses are converted back to local time.

def to_utc(dt: datetime) -> datetime:
    """Normalize to UTC. Raises ValueError (never OverflowError) for out-of-range dates."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LOCAL_TZ)
    try:
        utc = dt.astimezone(timezone.utc).replace(microsecond=0)
        utc.astimezone(LOCAL_TZ)  # must also be representable as local time for responses
    except (OverflowError, ValueError):
        raise ValueError("date is outside the supported range")
    return utc


def to_local(dt: datetime) -> datetime:
    return dt.astimezone(LOCAL_TZ)


def to_db(dt: datetime) -> str:
    return to_utc(dt).isoformat()


def from_db(value: str | None) -> datetime | None:
    return to_local(datetime.fromisoformat(value)) if value is not None else None


def now_utc() -> datetime:
    return to_utc(datetime.now(timezone.utc))
