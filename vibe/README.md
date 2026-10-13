# Vibe-coded version

Built with loose prompts and no specification, as the baseline for comparison.

Status: in progress
<!-- Change to "Frozen as of <date>, commit <hash>" when done. Do not edit after. -->

## Room Booking API

FastAPI + SQLite (stdlib `sqlite3`, no ORM). JWT bearer auth, PBKDF2 password hashing.

### Run it (Windows PowerShell, from this `vibe/` folder)

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt

$env:ROOMAPI_SECRET_KEY = "change-me-to-a-long-random-string"   # optional; random per start if unset
.\.venv\Scripts\python -m app.cli create-admin admin            # prompts for a password (min 8 chars)
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

### Endpoints

All endpoints except register, login and health need `Authorization: Bearer <token>`.

| Method | Path | Who | Notes |
|---|---|---|---|
| POST | `/auth/register` | anyone | JSON `{username, password}` |
| POST | `/auth/login` | anyone | **form** fields `username`, `password` → `{access_token}` |
| GET | `/users/me` | user | |
| GET | `/rooms` | user | `?min_capacity=`, admins: `?include_inactive=true` |
| GET | `/rooms/{id}` | user | |
| GET | `/rooms/{id}/availability` | user | `?start=&end=` (default: today UTC, max 31 days) → `booked` and `free` slots |
| POST | `/rooms` | admin | `{name, capacity, location?, description?, is_active?}` |
| PATCH | `/rooms/{id}` | admin | any subset of the fields; `is_active=false` hides a room |
| POST | `/bookings` | user | `{room_id, start_time, end_time}`; 409 if it overlaps |
| GET | `/bookings` | user | own bookings; `?include_cancelled`, `?upcoming_only`, `?room_id`; admins: `?all_users=true` |
| GET | `/bookings/{id}` | owner/admin | |
| DELETE | `/bookings/{id}` | owner/admin | cancels the booking (kept with status `cancelled`) |

### Behaviour notes

- Times are ISO-8601. Times without an offset are treated as UTC. Responses are in UTC.
- Bookings are half-open intervals, so 09:00–10:00 and 10:00–11:00 don't clash.
- The overlap check and insert run in one `BEGIN IMMEDIATE` transaction, so concurrent requests can't double-book.
- You can't book in the past. Regular users can't cancel a booking that has already ended; admins can.
- Other users' bookings return 404 (not 403), so booking IDs aren't revealed.
- Usernames and room names are case-insensitively unique.
- Admins are created or promoted only through `python -m app.cli create-admin <username>`. There is no API for it.
