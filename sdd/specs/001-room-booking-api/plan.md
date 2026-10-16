# Implementation Plan: Room Booking API

**Branch**: `spec/sdd-init` | **Date**: 2026-10-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-room-booking-api/spec.md`

## Summary

A REST API where employees register, log in, see rooms and their availability, and book, list and cancel bookings, while admins manage rooms. The technical approach:

- FastAPI over SQLite, with SQLAlchemy 2.
- Overlap protection inside a `BEGIN IMMEDIATE` transaction.
- Explicit-offset times stored in UTC; opening hours checked in Europe/Helsinki.
- Argon2id password hashes and 60-minute JWT access tokens.
- A login slow-down that never locks accounts.

Acceptance tests are black-box HTTP tests, so the same suite can run against the vibe version.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI, Uvicorn, SQLAlchemy 2, Pydantic v2, argon2-cffi, PyJWT, tzdata, python-multipart

**Storage**: SQLite file (path from `ROOMAPI_DB`, not committed); a fresh temporary file per test

**Testing**: pytest, pytest-cov, httpx (black-box via `TestClient` in-process, or `ROOMAPI_BASE_URL`)

**Target Platform**: local developer machine (Windows, macOS, Linux); CI on GitHub Actions (Ubuntu)

**Project Type**: web service (REST API)

**Performance Goals**: every request under 500 ms with 1,000 bookings stored (NFR-006), except logins delayed by NFR-009

**Constraints**: no other services (constitution V); no 500 on any client input (NFR-004); single process

**Scale/Scope**: one organisation; tens of rooms, hundreds of users, thousands of bookings

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How the plan satisfies it | Pre-research | Post-design |
|---|---|---|---|
| I. Specification First | Every endpoint in [contracts/api.md](contracts/api.md) cites its FR/NFR; nothing without a requirement. The NFR-006/NFR-009 conflict was fixed in the spec before planning. | Pass | Pass |
| II. Test-First | Acceptance tests from the spec's scenarios are written and committed before implementation (tasks phase); a traceability table maps every FR/NFR to tests. | Pass | Pass |
| III. Secure by Default | Argon2id (R2); token on every protected endpoint (R3); per-resource owner/admin checks; explicit bounds on every input (R5). | Pass | Pass |
| IV. Explicit Time Handling | `AwareDatetime` rejects times without an offset; UTC storage and output; Helsinki only for opening hours (R4). | Pass | Pass |
| V. Simplicity | Only the constitution's stack plus the small libraries it implies (hashing, JWT, time zone data, form parsing). One package, three routers. | Pass | Pass |

No violations, so Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-room-booking-api/
├── spec.md              # /speckit-specify and /speckit-clarify output
├── plan.md              # This file
├── research.md          # Phase 0: decisions R1–R8
├── data-model.md        # Phase 1: tables, rules, state changes
├── quickstart.md        # Phase 1: run and validation guide
├── contracts/
│   └── api.md           # Phase 1: endpoint contract and vibe mapping
├── checklists/
│   └── requirements.md  # spec quality checklist
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (`sdd/`)

```text
sdd/
├── pyproject.toml
├── uv.lock
├── app/
│   ├── __init__.py
│   ├── main.py          # app factory, routers, error handlers, /health
│   ├── config.py        # settings from ROOMAPI_* environment variables
│   ├── db.py            # engine, sessions, BEGIN IMMEDIATE, schema creation
│   ├── models.py        # SQLAlchemy models: User, Room, Booking, FailedLogin
│   ├── schemas.py       # Pydantic request and response models, input bounds
│   ├── security.py      # Argon2 hashing, JWT, current-user and admin dependencies
│   ├── timerules.py     # UTC conversion, opening hours, 4 h limit, 90-day horizon
│   ├── cli.py           # operator command: create-admin
│   └── routers/
│       ├── auth.py      # register, login (with slow-down), users/me
│       ├── rooms.py     # list, get, create, update/deactivate, availability
│       └── bookings.py  # create, list mine, cancel
└── tests/
    ├── conftest.py      # client fixture (in-process or ROOMAPI_BASE_URL), users, admin, rooms, time helpers
    ├── acceptance/      # one file per user story, plus NFR tests (invalid input, concurrency, timing, slow-down)
    └── unit/            # time-rule edge cases (DST days, day boundaries)
```

**Structure Decision**: a single project in `sdd/`, beside the `specs/` folder that Spec Kit manages. There is no frontend. Tests are split into black-box acceptance tests, reusable against vibe, and a few unit tests for the time rules, where black-box tests can't reach every edge.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Test-First (II): the foundation modules (`timerules.py`, `security.py`, `schemas.py`) landed in group A (#16) before their tests (T019 and the story tests). | A test needs the app factory, database and harness to exist. The foundation is that harness, and it has no behaviour a user can reach yet. | Writing the foundation tests first would mean building a second throwaway harness. Every user-reachable behaviour is still test-first: each story pull request commits its failing tests before its implementation. |
