# Vibe-coded version

Built with loose prompts and no specification, as the baseline for comparison.

Status: Frozen as of 2026-10-16, commit b68a979 (after 2 prompt rounds). Do not edit after.

## Room Booking API

FastAPI + SQLite (stdlib `sqlite3`, no ORM). JWT bearer auth, PBKDF2 password hashing.

### Run it (Windows PowerShell, from this `vibe/` folder)

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt

$env:ROOMAPI_SECRET_KEY = "change-me-to-a-long-random-string"   # optional; random per start if unset
.\.venv\Scripts\python -m app.cli create-admin admin            # prompts for a password (see password rules below)
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. Click **Authorize** and log in with a username and password to try every endpoint.
(macOS/Linux: use `.venv/bin/python` and `export ROOMAPI_SECRET_KEY=...`.)

Run the tests with `.\.venv\Scripts\python -m pytest`.

### Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `ROOMAPI_DB` | `vibe/roomapi.db` | SQLite file path |
| `ROOMAPI_SECRET_KEY` | random at startup | JWT signing key (set it, or tokens break on restart) |
| `ROOMAPI_TOKEN_MINUTES` | `60` | Token lifetime |
| `ROOMAPI_TIMEZONE` | `Europe/Helsinki` | Local time zone: times without an offset are read in it, responses use it |
| `ROOMAPI_OPENING_TIME` | `07:00` | Earliest booking start (local time) |
| `ROOMAPI_CLOSING_TIME` | `20:00` | Latest booking end (local time) |
| `ROOMAPI_MAX_BOOKING_MINUTES` | `480` | Maximum booking length (8 hours) |
| `ROOMAPI_LOGIN_MAX_FAILURES` | `5` | Failed logins per username before it is locked |
| `ROOMAPI_LOGIN_MAX_FAILURES_PER_IP` | `20` | Failed logins per IP address before it is locked |
| `ROOMAPI_LOGIN_WINDOW_MINUTES` | `15` | Window for counting failed logins (and lock length) |

### Endpoints

All endpoints except register, login and health need `Authorization: Bearer <token>`.

| Method | Path | Who | Notes |
|---|---|---|---|
| POST | `/auth/register` | anyone | JSON `{username, password}` |
| POST | `/auth/login` | anyone | **form** fields `username`, `password` → `{access_token}`; 429 after too many failures |
| GET | `/users/me` | user | |
| GET | `/rooms` | user | `?min_capacity=`, admins: `?include_inactive=true` |
| GET | `/rooms/{id}` | user | |
| GET | `/rooms/{id}/availability` | user | `?start=&end=` (default: today, local time; max 31 days) → `booked` and `free` slots (free = within opening hours) |
| POST | `/rooms` | admin | `{name, capacity, location?, description?, is_active?}` |
| PATCH | `/rooms/{id}` | admin | any subset of the fields; `is_active=false` hides a room and cancels its upcoming bookings |
| POST | `/bookings` | user | `{room_id, start_time, end_time}`; 409 if it overlaps |
| GET | `/bookings` | user | own bookings; `?include_cancelled`, `?upcoming_only`, `?room_id`; admins: `?all_users=true` |
| GET | `/bookings/{id}` | owner/admin | |
| DELETE | `/bookings/{id}` | owner/admin | cancels the booking (kept with status `cancelled`) |

### Behaviour notes

- Times are ISO-8601. Times without an offset are Finnish local time (`Europe/Helsinki`, summer time handled). Responses are in local time with an explicit offset (e.g. `+03:00`). Stored as UTC.
- Bookings must start and end on the same day between 07:00 and 20:00 local time and last at most 8 hours (configurable).
- Deactivating a room cancels its upcoming and ongoing bookings (past ones stay as history). Reactivating it does not restore them. On startup, any active upcoming bookings in rooms that were already inactive are cancelled too.
- IDs must be between 1 and 2^63-1 (SQLite's integer range); larger values get 422. Dates that cannot be represented (around year 1 or the end of year 9999) get 422.
- Passwords: at least 10 characters, letters plus a digit or symbol, at least 5 different characters, must not contain the username, and must not be a common password. This applies to new users only. Existing passwords keep working.
- Login: 5 failed attempts for a username, or 20 from one IP address, within 15 minutes lock further attempts (429 with `Retry-After`) until the window passes. A successful login resets the username's count.
- Bookings are half-open intervals, so 09:00–10:00 and 10:00–11:00 don't clash.
- The overlap check and insert run in one `BEGIN IMMEDIATE` transaction, so concurrent requests can't double-book.
- You can't book in the past. Regular users can't cancel a booking that has already ended; admins can.
- Other users' bookings return 404 (not 403), so booking IDs aren't revealed.
- Usernames and room names are case-insensitively unique.
- Admins are created or promoted only through `python -m app.cli create-admin <username>`. There is no API for it.
