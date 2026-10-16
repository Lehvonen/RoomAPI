# Vibe round 2: agent output (verbatim)

> The agent's final reply, copied in full and unedited, except that the six absolute `C:\Users\lehvo\RoomAPI\vibe\...` paths are shortened to `vibe\...`. The code it describes is in commit `b68a979`.

---

I fixed all six problems. The test suite now has 33 tests (the original 21 plus 12 new ones, one or more per problem) and they all pass. I only touched files inside `vibe/` and ran no git commands.

**What changed for each problem**
1. **Very large IDs** now get a 422 error instead of a 500. IDs must be between 1 and 2^63-1, the largest number the database can store. This covers room and booking IDs in the URL, `room_id` in a booking, and the `room_id` and `min_capacity` filters.
2. **Dates at the very end of year 9999** (or the very start of year 1) now get a 422 instead of a 500. The fix covers new bookings and the availability window. A booking during opening hours on 9999-12-31 still works.
3. **Deactivating a room** now cancels its upcoming and ongoing bookings in the same step, so no new booking can slip in between. Past bookings stay as history, and reactivating the room does not bring the cancelled ones back. On startup, the app also cancels upcoming bookings in rooms that were already inactive.
4. **Booking limits:** a booking can be at most 8 hours long and must start and end on the same day between 07:00 and 20:00 Finnish time. The `free` list in the availability endpoint now only shows open hours, so it matches what can actually be booked. All three limits can be changed with settings.
5. **Time zone:** times without a time zone are now read as Finnish time, including summer time. Times are still stored in UTC. Responses now come back in Finnish time with the offset shown (e.g. `+03:00`), not in UTC. Bookings saved before this fix were stored as UTC and are not corrected.
6. **Passwords and login attempts:**
   - **New passwords** must be at least 10 characters, include letters plus a digit or symbol, use at least 5 different characters, not contain the username, and not be on a short list of common passwords. The same rules apply to `create-admin`. Existing passwords keep working.
   - **Login lock:** 5 failed logins for one username, or 20 from one IP address, within 15 minutes lock further attempts with a 429 error that says how long to wait. A successful login resets that username's count.
   - Locking a username also means anyone can lock a real user out for 15 minutes by guessing wrong on purpose. If the API runs behind a proxy, every request looks like it comes from the same IP, so the per-IP limit would apply to everyone together.

**Files**
- New: `vibe\app\config.py` holds the new settings.
- Changed in `vibe\app\`:
  - `db.py`: time zone handling, the startup cleanup, and a new table that records failed logins.
  - `schemas.py`: password rules and ID limits.
  - `routers\bookings.py`: booking length, opening hours and ID limits.
  - `routers\rooms.py`: deactivation cancels bookings, availability uses opening hours, ID limits.
  - `routers\auth.py`: the login lock.
- `vibe\requirements.txt`: added `tzdata==2025.2`. Windows doesn't include the time zone data, so without it the app can't find `Europe/Helsinki`. I already installed it into `vibe\.venv`.
- `vibe\tests\conftest.py` and `tests\test_api.py`: the test passwords had to change because the old ones are now too weak, and `slot()` now uses Finnish time. One existing test expectation changed: free slots now only cover 07:00–20:00. The new tests are at the end of `test_api.py`.
- `vibe\README.md`: the new rules and settings are documented.

I tested startup on a copy of `roomapi.db` and deleted the copy afterwards. The new table was added and nothing needed cancelling; the real database file has not been changed.

**How to run it** (PowerShell, from `vibe`)
```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
$env:ROOMAPI_SECRET_KEY = "change-me-to-a-long-random-string"
.\.venv\Scripts\python -m app.cli create-admin admin
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```
Then open http://127.0.0.1:8000/docs. Run the tests with `.\.venv\Scripts\python -m pytest`.

**Settings you can change** (environment variables):
- `ROOMAPI_TIMEZONE` (default `Europe/Helsinki`)
- `ROOMAPI_OPENING_TIME` / `ROOMAPI_CLOSING_TIME` (`07:00` / `20:00`)
- `ROOMAPI_MAX_BOOKING_MINUTES` (`480`)
- `ROOMAPI_LOGIN_MAX_FAILURES` (`5`), `ROOMAPI_LOGIN_MAX_FAILURES_PER_IP` (`20`), `ROOMAPI_LOGIN_WINDOW_MINUTES` (`15`)
