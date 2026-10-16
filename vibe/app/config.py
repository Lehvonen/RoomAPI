"""Settings read from environment variables, with defaults for an office in Finland."""

import os
from datetime import time, timedelta
from zoneinfo import ZoneInfo

# SQLite INTEGER is a signed 64-bit value; anything larger cannot be an ID.
SQLITE_MAX_INT = 2**63 - 1

# Times without an offset are interpreted in this zone, and responses are given in it.
LOCAL_TZ = ZoneInfo(os.environ.get("ROOMAPI_TIMEZONE", "Europe/Helsinki"))

# Bookings must start and end on the same local day between these times.
OPENING_TIME = time.fromisoformat(os.environ.get("ROOMAPI_OPENING_TIME", "07:00"))
CLOSING_TIME = time.fromisoformat(os.environ.get("ROOMAPI_CLOSING_TIME", "20:00"))
if CLOSING_TIME <= OPENING_TIME:
    raise RuntimeError("ROOMAPI_CLOSING_TIME must be later than ROOMAPI_OPENING_TIME")

MAX_BOOKING_LENGTH = timedelta(minutes=int(os.environ.get("ROOMAPI_MAX_BOOKING_MINUTES", "480")))

# Login throttling: this many failed attempts within the window blocks further attempts.
LOGIN_WINDOW = timedelta(minutes=int(os.environ.get("ROOMAPI_LOGIN_WINDOW_MINUTES", "15")))
LOGIN_MAX_FAILURES_PER_USER = int(os.environ.get("ROOMAPI_LOGIN_MAX_FAILURES", "5"))
LOGIN_MAX_FAILURES_PER_IP = int(os.environ.get("ROOMAPI_LOGIN_MAX_FAILURES_PER_IP", "20"))
