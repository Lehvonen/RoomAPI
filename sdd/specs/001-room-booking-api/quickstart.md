# Quickstart: Room Booking API

How to run the SDD version and prove it meets the spec. Endpoint details: [contracts/api.md](contracts/api.md). Data rules: [data-model.md](data-model.md).

## Prerequisites

- Python 3.11 or newer
- uv

## Set up and run (from `sdd/`)

```bash
uv sync
export ROOMAPI_SECRET_KEY="change-me-to-a-long-random-string"   # PowerShell: $env:ROOMAPI_SECRET_KEY = "..."
uv run python -m app.cli create-admin admin                      # prompts for a password (10–128 characters)
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. Click **Authorize** and log in.

## Validate

| Check | Command | Expected |
|---|---|---|
| Whole acceptance suite, in-process, with coverage | `uv run pytest --cov=app --cov-report=term-missing` | all pass; coverage ≥ 80% (SC-003, SC-005) |
| Same suite against a running server | `ROOMAPI_BASE_URL=http://127.0.0.1:8000 ROOMAPI_TEST_ADMIN=admin ROOMAPI_TEST_ADMIN_PASSWORD=... uv run pytest tests/acceptance` | all pass |
| Same suite against the vibe version | as above, with the vibe server's URL and admin | results recorded per test for the comparison (Phase 5) |

## Manual smoke test (User Story 1 → 2 → 4)

1. `POST /auth/register` with a new username and a 10+ character password → 201.
2. `POST /auth/login` → 200 with a token. Authorize with it.
3. As admin, `POST /rooms` `{"name": "Aurora", "capacity": 8}` → 201.
4. `POST /bookings` for tomorrow 10:00–11:00 with `+03:00` (summer) or `+02:00` (winter) → 201; the response shows UTC.
5. The same booking again → 409. The same without an offset → 422.
6. `GET /bookings/me` → the booking. `DELETE /bookings/{id}` → 204.
