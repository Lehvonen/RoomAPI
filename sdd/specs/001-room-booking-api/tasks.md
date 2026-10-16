---

description: "Task list for the Room Booking API"
---

# Tasks: Room Booking API

**Input**: Design documents from `/specs/001-room-booking-api/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/api.md](contracts/api.md)

**Tests**: required. The constitution (II, Test-First) makes tests mandatory, and they are written and committed before each story's implementation, where they must fail.

**Organization**: tasks are grouped by user story, so each story can be built and tested on its own. All paths are relative to `sdd/`. **Issue groups** (one GitHub issue each, delivered as one or more small pull requests) are named at the start of each phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: the user story the task belongs to (US1–US5)

---

## Phase 1: Setup (Shared Infrastructure)

**Issue group A: Project setup and foundation** (Phases 1–2)

- [X] T001 Create the uv project in `pyproject.toml`: `requires-python = ">=3.11"`; dependencies fastapi, uvicorn, sqlalchemy>=2, pydantic>=2, argon2-cffi, pyjwt, tzdata, python-multipart; dev dependencies pytest, pytest-cov, httpx. Run `uv lock` to create `uv.lock`
- [X] T002 [P] Create the package skeleton `app/__init__.py`, `app/routers/__init__.py`, `tests/__init__.py`, `tests/acceptance/__init__.py`, `tests/unit/__init__.py`
- [X] T003 [P] Add `.gitignore` entries for `*.db`, `.venv/`, `.coverage`, `htmlcov/` in `sdd/.gitignore`
- [X] T004 [P] Add the GitHub Actions workflow `.github/workflows/sdd-tests.yml` (repository root): on push and pull_request, `astral-sh/setup-uv`, `uv sync` and `uv run pytest --cov=app --cov-report=term-missing`, with working directory `sdd`. The 80% gate (`--cov-fail-under=80`, SC-005) is switched on in T035, once every story has tests

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: no user story work can begin until this phase is complete.

- [X] T005 Implement settings in `app/config.py`, read from environment variables: `ROOMAPI_DB` (default `roomapi.db`), `ROOMAPI_SECRET_KEY` (required: refuse to start without it), `ROOMAPI_TOKEN_MINUTES` (60), `ROOMAPI_LOGIN_DELAY_SECONDS` (2), plus constants for time zone `Europe/Helsinki`, opening hours 08:00–18:00, maximum length 4 h and horizon 90 days
- [X] T006 Implement the engine, session dependency and schema creation in `app/db.py`. Turn off pysqlite's own transaction handling and emit `BEGIN IMMEDIATE` on SQLAlchemy's `begin` event (research R1); `PRAGMA foreign_keys=ON`
- [X] T007 Implement the SQLAlchemy models in `app/models.py`, exactly as in data-model.md:
  - User: username "3–50 characters from `A–Z a–z 0–9 _ . -`", unique case-insensitive (`COLLATE NOCASE`)
  - Room: name "1–100 characters", unique case-insensitive; capacity "1 … 10,000"; location "up to 200 characters"; description "up to 2,000 characters"; `is_active` default true
  - Booking: `CHECK (end_time > start_time)`; status `active` or `cancelled`; `cancelled_at`, `cancelled_by`; index on `(room_id, status, start_time, end_time)`
  - FailedLogin: username lower-cased, `attempted_at`
- [X] T008 [P] Implement the time rules in `app/timerules.py`:
  - `to_utc(aware) -> datetime`, raising a validation error on `OverflowError`
  - `check_booking_window(start, end, now)`, enforcing end > start, start ≥ now, start ≤ now + 90 days (checked before conversion), and the same Helsinki date within 08:00–18:00 with length ≤ 4 h. Each failure gives its own plain-English message
  - `opening_window(date) -> (opens_utc, closes_utc)`
- [X] T009 [P] Implement password hashing (Argon2id `PasswordHasher`) and JWT create and decode (HS256; `sub`, `iat`, `exp`) in `app/security.py`, plus the `get_current_user` (401) and `require_admin` (403) dependencies
- [X] T010 [P] Implement the shared Pydantic types in `app/schemas.py`:
  - `Id = Annotated[int, Field(ge=1, le=2**63-1)]`
  - `AwareDatetime` inputs
  - a UTC serializer that outputs `Z`
  - the User, Room, Booking and Availability response models from contracts/api.md, with User never including the password or hash
- [X] T011 Implement the app factory in `app/main.py`: include the routers, and `GET /health`. Only the specific time-conversion errors become 422 (research R5): `timerules` turns `OverflowError` into a validation error, and there is no catch-all `ValueError` handler, so real bugs still surface. The app factory takes an optional database path for tests
- [X] T012 Implement the operator command `python -m app.cli create-admin <username> [--password]` in `app/cli.py`. It creates an admin, or promotes an existing user. The password must be 10–128 characters (FR-006, FR-002)
- [X] T013 Implement the test harness in `tests/conftest.py` (research R7):
  - a `client` fixture that is a `TestClient(create_app(tmp_db))` or, when `ROOMAPI_BASE_URL` is set, an `httpx.Client(base_url=...)`
  - an `admin` fixture (in-process: via `app.cli`; external: `ROOMAPI_TEST_ADMIN` and `ROOMAPI_TEST_ADMIN_PASSWORD`)
  - `register_and_login` and `auth` helpers
  - `helsinki(days_ahead, hh, mm)`, which returns an ISO string with the correct offset
  - `ROOMAPI_LOGIN_DELAY_SECONDS=0.2` by default, overridden in the slow-down test
  - a smoke test of `GET /health` (no token needed, NFR-002) in `tests/acceptance/test_health.py`, so CI has a passing test from the start

**Checkpoint**: the foundation is ready. `uv run pytest` runs the health smoke test, and CI is green.

---

## Phase 3: User Story 1 - Register and log in (Priority: P1) 🎯 MVP

**Issue group B: Accounts (US1)**

**Goal**: users can register, log in and see their profile.

**Independent Test**: register, log in, call `GET /users/me`.

### Tests for User Story 1 (write first, must fail) ⚠️

- [X] T014 [P] [US1] Acceptance tests in `tests/acceptance/test_us1_accounts.py`:
  - User Story 1, scenarios 1–4
  - FR-001: username rules, and "ALICE" refused after "alice"
  - FR-002: 9-character password refused, 10 accepted, 129 refused
  - FR-004: identical message for a wrong password and an unknown user
  - FR-005: no password field in the profile
  - FR-006: `is_admin: true` in the registration body is ignored
  - NFR-002: `/users/me` with no token, an expired token or a tampered token gives 401

### Implementation for User Story 1

- [X] T015 [US1] Implement `POST /auth/register` (201, 409 name taken) and `GET /users/me` in `app/routers/auth.py`, with registration models in `app/schemas.py`: username "3–50 characters from `A–Z a–z 0–9 _ . -`", password "10–128 characters"
- [X] T016 [US1] Implement `POST /auth/login` (form fields; 200 token; 401 with the same message for an unknown user and a wrong password) in `app/routers/auth.py`, with a dummy hash check for unknown users so the timing matches

**Checkpoint**: US1 tests pass. This is the MVP.

---

## Phase 4: User Story 2 - Book a room (Priority: P1)

**Issue group C: Bookings (US2)**

**Goal**: users book active rooms, following every booking rule, with no overlaps.

**Independent Test**: book a free slot; an overlapping request is refused; a back-to-back one is accepted.

### Tests for User Story 2 (write first, must fail) ⚠️

- [X] T017 [P] [US2] Acceptance tests in `tests/acceptance/test_us2_booking.py`:
  - User Story 2, scenarios 1–4
  - FR-011: past start, and a start 91 days ahead, refused
  - FR-012: 08:00–12:00 accepted; 07:30–08:30, 17:00–18:30, 09:00–13:30 and 17:00 to the next day's 09:00 refused
  - FR-013: overlap gives 409; back-to-back accepted; a cancelled booking doesn't block
  - FR-017: a time without an offset gives 422; a `+03:00` input is returned as UTC `Z`
  - booking an inactive or missing room gives 404
- [X] T018 [P] [US2] Concurrency test in `tests/acceptance/test_nfr_concurrency.py`: 20 threads request the same free slot and exactly 1 gets 201 (User Story 2 scenario 5, NFR-005, SC-002)
- [X] T019 [P] [US2] Unit tests for `app/timerules.py` in `tests/unit/test_timerules.py`: boundaries at exactly 08:00 and 18:00, exactly 4 h, the 90-day edge, the DST days 2026-10-25 and 2027-03-28, and the year-9999 overflow

### Implementation for User Story 2

- [X] T020 [US2] Implement `POST /bookings` in `app/routers/bookings.py`:
  - validate with `timerules.check_booking_window`
  - in a `BEGIN IMMEDIATE` transaction: the room exists and is active (404), the overlap check `start < new.end AND new.start < end` on active bookings (409), then insert
  - return 201 with UTC times

**Checkpoint**: US1 and US2 work on their own. Users can book.

---

## Phase 5: User Story 3 - See rooms and availability (Priority: P2)

**Issue group D: Rooms, availability and my bookings (US3 + US4)**

**Goal**: users list active rooms and see a day's booked and free intervals within opening hours.

**Independent Test**: create rooms and bookings; compare the list and the availability.

### Tests for User Story 3 (write first, must fail) ⚠️

- [X] T021 [P] [US3] Acceptance tests in `tests/acceptance/test_us3_rooms_availability.py`:
  - User Story 3, scenarios 1–2
  - FR-007: an inactive room is hidden from list and get (404)
  - FR-010: a day with 10:00–11:00 booked gives free 08:00–10:00 and 11:00–18:00, in UTC
  - `date` missing or malformed gives 422

### Implementation for User Story 3

- [X] T022 [US3] Implement `GET /rooms` (active, ordered by name) and `GET /rooms/{room_id}` (404 if missing, or inactive for non-admins) in `app/routers/rooms.py`
- [X] T023 [US3] Implement `GET /rooms/{room_id}/availability?date=` in `app/routers/rooms.py`, using `timerules.opening_window`: booked intervals clipped to the window, and free intervals as the gaps

**Checkpoint**: US3 works on its own.

---

## Phase 6: User Story 4 - See and cancel my bookings (Priority: P2)

**Goal**: users list their upcoming bookings and cancel their own.

**Independent Test**: book two, list, cancel one, and check that the slot is free again.

### Tests for User Story 4 (write first, must fail) ⚠️

- [X] T024 [P] [US4] Acceptance tests in `tests/acceptance/test_us4_my_bookings.py`:
  - User Story 4, scenarios 1–3
  - FR-014: only your own, only active and not ended, oldest first
  - FR-015: cancel gives 204; then status `cancelled` with `cancelled_at` and `cancelled_by` set; cancelling again gives 409; another user's booking gives 403; a missing booking gives 404
  - FR-016: no edit endpoint exists (PUT and PATCH on `/bookings/{id}` give 405)

### Implementation for User Story 4

- [X] T025 [US4] Implement `GET /bookings/me` in `app/routers/bookings.py`
- [X] T026 [US4] Implement `DELETE /bookings/{booking_id}` in `app/routers/bookings.py`: owner or admin (else 403); 409 if already cancelled, or if ended for a non-admin; set `cancelled_at` and `cancelled_by`

**Checkpoint**: US1–US4 work on their own.

---

## Phase 7: User Story 5 - Manage rooms and bookings as admin (Priority: P3)

**Issue group E: Admin (US5)**

**Goal**: admins create, edit and deactivate rooms and cancel any booking.

**Independent Test**: as admin, create, rename, deactivate and cancel; as a user, every one of these is refused.

### Tests for User Story 5 (write first, must fail) ⚠️

- [ ] T027 [P] [US5] Acceptance tests in `tests/acceptance/test_us5_admin.py`:
  - User Story 5, scenarios 1–5
  - FR-008: name unique regardless of case, on create and on rename (409); capacity 0 gives 422
  - FR-009: deactivating with a future booking gives 409 with the count; after cancelling it, deactivation succeeds and the room is hidden and unbookable; reactivating works
  - NFR-003: a regular user gets 403 on POST and PATCH `/rooms`
  - FR-015: an admin cancels another user's booking, and `cancelled_by` is the admin

### Implementation for User Story 5

- [ ] T028 [US5] Implement `POST /rooms` and `PATCH /rooms/{room_id}` in `app/routers/rooms.py` (admin only):
  - name "1–100 characters", capacity "1 … 10,000", location "up to 200 characters", description "up to 2,000 characters"
  - 409 on a duplicate name
  - setting `is_active=false` gives 409 while the room has active bookings that haven't ended, with the count in the message

**Checkpoint**: all user stories work.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Issue group F: Non-functional requirements, traceability and docs**

- [ ] T029 [P] Invalid-input test set in `tests/acceptance/test_nfr_invalid_input.py` (NFR-004, SC-004): IDs 0, −1 and 2^70 in every path and body; dates near year 9999; malformed JSON; missing fields; over-long text. Assert there is never a 500, and always a 4xx with a message
- [ ] T030 [P] Login slow-down test in `tests/acceptance/test_nfr_login_slowdown.py` (NFR-009): with the delay set to 2 s, the 6th failure within 15 minutes takes ≥ 2 s; a correct password after 10 failures still logs in; failures for non-existent usernames don't affect other users
- [ ] T031 Implement the login slow-down in `app/routers/auth.py`, using the `failed_logins` table (research R6)
- [ ] T032 [P] Timing test in `tests/acceptance/test_nfr_performance.py` (NFR-006): with 1,000 bookings seeded, each operation responds in under 500 ms
- [ ] T033 [P] Security checks in `tests/acceptance/test_nfr_security.py` (NFR-001): the stored hash starts with `$argon2id$` and differs for two users with the same password; no response body contains the password
- [ ] T034 [P] Interface documentation test in `tests/acceptance/test_nfr_docs.py` (NFR-007): `/openapi.json` lists every endpoint in contracts/api.md, with its error responses
- [ ] T035 Write the traceability table from each FR, NFR and SC to its tests in `specs/001-room-booking-api/traceability.md`, and switch on the CI coverage gate `--cov-fail-under=80` (SC-005) in `.github/workflows/sdd-tests.yml`
- [ ] T036 [P] Export the OpenAPI document to `../docs/openapi.json`, and add the run instructions to `sdd/README.md`
- [ ] T037 Run the [quickstart.md](quickstart.md) validation, including the suite against the vibe version via `ROOMAPI_BASE_URL`, and save the output in `../docs/evidence/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)**: these block every story.
- **US1 (Phase 3)**: needs only the foundation. Every later story's tests log in, so US1 comes first.
- **US2, US3, US4, US5**: each needs the foundation and US1. US4 also needs US2's `POST /bookings` to create test data. US5's FR-009 test also needs US2 and US4.
- **Polish (Phase 8)**: after the stories. T031 (implementation) follows T030 (its test).

### Within each user story

Tests first (committed, failing) → implementation → the story's tests pass → pull request.

### Parallel Opportunities

- T002–T004 in parallel; T008–T010 in parallel.
- After US1: the test tasks T017, T018, T019, T021, T024 and T027 can be written in parallel (different files).
- Polish test tasks T029, T030, T032, T033 and T034 in parallel.

---

## Parallel Example: User Story 2

```bash
Task: "Acceptance tests in tests/acceptance/test_us2_booking.py"
Task: "Concurrency test in tests/acceptance/test_nfr_concurrency.py"
Task: "Unit tests for app/timerules.py in tests/unit/test_timerules.py"
```

---

## Implementation Strategy

### MVP first

Setup → Foundational → US1. Stop and validate: register, log in, `/users/me`.

### Incremental delivery

One issue group per pull request (or a few small pull requests): A → B → C → D → E → F. Each one merges only when its tests and CI pass. Each pull request carries its tests in an earlier commit than its implementation, so the history shows test-first.

### Mapping to GitHub issues

| Group | Issue | Tasks | Covers |
|---|---|---|---|
| A. Project setup and foundation | #16 | T001–T013 | constitution, NFR-002 base |
| B. Accounts | #17 | T014–T016 | US1, FR-001–FR-006 |
| C. Bookings | #18 | T017–T020 | US2, FR-011–FR-013, FR-017, NFR-005 |
| D. Rooms, availability and my bookings | #19 | T021–T026 | US3, US4, FR-007, FR-010, FR-014–FR-016 |
| E. Admin | #20 | T027–T028 | US5, FR-008, FR-009, NFR-003 |
| F. NFRs, traceability, docs | #21 | T029–T037 | NFR-001, NFR-004, NFR-006, NFR-007, NFR-009, SC-001–SC-005 |

---

## Notes

- [P] tasks touch different files and depend on no unfinished task.
- Commit messages name the requirement or report section: `test(FR-013): …`, `feat(FR-013): …`.
- Verify that the tests fail before implementing.
