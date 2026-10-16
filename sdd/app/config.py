"""Settings from ROOMAPI_* environment variables, and the fixed booking rules (spec FR-011, FR-012)."""

import os
from dataclasses import dataclass
from datetime import time, timedelta
from zoneinfo import ZoneInfo

# Booking rules decided in the spec; fixed, not configurable.
TIMEZONE = ZoneInfo("Europe/Helsinki")
OPENING_TIME = time(8, 0)
CLOSING_TIME = time(18, 0)
MAX_BOOKING_LENGTH = timedelta(hours=4)
BOOKING_HORIZON = timedelta(days=90)

# NFR-009: slow-down after repeated failed logins.
LOGIN_FAILURE_LIMIT = 5
LOGIN_FAILURE_WINDOW = timedelta(minutes=15)

# Largest integer SQLite can store; IDs outside 1..MAX_ID are rejected (NFR-004).
MAX_ID = 2**63 - 1


@dataclass(frozen=True)
class Settings:
    db_path: str
    secret_key: str
    token_ttl: timedelta
    login_delay_seconds: float


def get_settings() -> Settings:
    secret = os.environ.get("ROOMAPI_SECRET_KEY", "")
    if not secret:
        raise RuntimeError("ROOMAPI_SECRET_KEY must be set; the app refuses to start without it.")
    return Settings(
        db_path=os.environ.get("ROOMAPI_DB", "roomapi.db"),
        secret_key=secret,
        token_ttl=timedelta(minutes=int(os.environ.get("ROOMAPI_TOKEN_MINUTES", "60"))),
        login_delay_seconds=float(os.environ.get("ROOMAPI_LOGIN_DELAY_SECONDS", "2")),
    )
