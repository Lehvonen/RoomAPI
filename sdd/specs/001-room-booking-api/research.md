# Research: Room Booking API

All technical unknowns for [plan.md](plan.md) are resolved below. The constitution fixes the main stack (FastAPI, SQLite via SQLAlchemy, Pydantic, pytest, uv).

## R1. Overlap protection under simultaneous requests (FR-013, NFR-005)

- **Decision**: Check for overlaps and insert the booking inside one SQLite write transaction started with `BEGIN IMMEDIATE`. The pysqlite driver's own transaction handling is turned off, and SQLAlchemy's `begin` event emits `BEGIN IMMEDIATE`, following the SQLAlchemy documentation's recipe for SQLite. Overlap test: `existing.start < new.end AND new.start < existing.end` on active bookings of the same room.
- **Rationale**: `BEGIN IMMEDIATE` takes the database write lock before the check, so two requests can't both see a free slot. One process and one file need nothing more.
- **Alternatives considered**: a unique constraint (can't express range overlap); application-level locks (break with more than one worker); optimistic retry (more code for the same result).

## R2. Password hashing (NFR-001)

- **Decision**: Argon2id through `argon2-cffi`'s `PasswordHasher`, with its default parameters.
- **Rationale**: the constitution allows bcrypt or Argon2. Argon2id is the current OWASP recommendation, and `PasswordHasher` salts each hash and encodes its parameters, so they can be raised later.
- **Alternatives considered**: bcrypt (limited to 72 bytes, and FR-002 allows 128 characters); passlib (no longer maintained).

## R3. Access tokens (FR-003, NFR-002)

- **Decision**: JWT signed with HS256 using PyJWT. Claims: `sub` (user id), `iat`, `exp` = 60 minutes. The secret comes from `ROOMAPI_SECRET_KEY`, and the app refuses to start without it, except in tests, which set it. There is no logout (clarification 4).
- **Rationale**: stateless, standard, and FastAPI's OAuth2 password flow gives the interactive docs a working "Authorize" button (NFR-007).
- **Alternatives considered**: server-side sessions (state that logout would need, but logout was ruled out); a random secret per start (vibe's choice, which silently logs everyone out on restart).

## R4. Time handling (FR-012, FR-017, FR-010)

- **Decision**: request models use Pydantic's `AwareDatetime`, so times without an offset are rejected with 422. Times are converted to UTC and stored as UTC. Opening hours are checked by converting start and end to `ZoneInfo("Europe/Helsinki")`. Both must fall on the same local date, within 08:00–18:00. The `tzdata` package supplies the zone data on Windows. Responses serialise UTC with a `Z` suffix.
- **Rationale**: no guessing (constitution IV), and local clock time handles the switches between summer and winter time automatically.
- **Alternatives considered**: storing local time (ambiguous for an hour each autumn); fixed offsets (wrong half of the year).

## R5. Out-of-range input (NFR-004)

- **Decision**:
  - IDs in paths and bodies are constrained to 1 … 2^63−1 (the SQLite integer range), giving 422 outside it.
  - The 90-day horizon (FR-011) is checked before any timezone conversion. A failure to convert a time (`OverflowError`, near year 9999) is caught and becomes 422.
  - Text fields have maximum lengths.
  - A last-resort exception handler logs the error and returns 500, but the invalid-input test set asserts that it never fires.
- **Rationale**: the vibe probe found three inputs causing unhandled errors (HTTP 500). Each one gets an explicit bound here.
- **Alternatives considered**: catching all exceptions as 422, which would hide real bugs.

## R6. Login slow-down (NFR-009)

- **Decision**: a `failed_logins` table (username in lower case, time). Before checking a password, count that username's failures in the last 15 minutes. If there are 5 or more, wait 2 seconds before answering. A successful login deletes that username's failures. The delay length comes from `ROOMAPI_LOGIN_DELAY_SECONDS` (default 2) so it can be set explicitly in tests. There is no per-address counting and no lockout.
- **Rationale**: slows sequential guessing to under 30 attempts a minute per username, and can never lock anyone out (vibe's N1 and N1b). Parallel requests each wait side by side, so the limit holds for one-at-a-time guessing only (spec Assumptions).
- **Alternatives considered**: lockout (rejected in clarification 1); in-memory counters (lost on restart, and can't be checked by black-box tests across processes).

## R7. Black-box acceptance tests with a configurable base URL

- **Decision**: tests talk HTTP only, through a `client` fixture.
  - If `ROOMAPI_BASE_URL` is set, the fixture is an `httpx.Client` against that server.
  - Otherwise it is FastAPI's `TestClient` on an app with a fresh temporary database, so coverage is measured in-process.
  - Admin credentials for the tests come from the operator CLI (`python -m app.cli create-admin`), which the in-process fixture calls directly. Against an external server, the credentials come from `ROOMAPI_TEST_ADMIN` and `ROOMAPI_TEST_ADMIN_PASSWORD`.
- **Rationale**: the same suite later runs against the vibe version (Phase 5 comparison), and in-process runs keep CI fast with coverage.
- **Alternatives considered**: always starting a uvicorn subprocess (no coverage without extra setup); unit tests only (can't be reused against vibe).

## R8. Project and dependency management

- **Decision**: one uv project in `sdd/` (`pyproject.toml`, `uv.lock`), Python ≥ 3.11. Runtime dependencies: fastapi, uvicorn, sqlalchemy, pydantic, argon2-cffi, pyjwt, tzdata, python-multipart (for the login form). Development dependencies: pytest, pytest-cov, httpx.
- **Rationale**: matches the constitution; `uv sync` and `uv run pytest` work the same locally and in CI.
- **Alternatives considered**: pip with requirements files (vibe's approach, no lock file).
