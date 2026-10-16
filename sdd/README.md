# SDD version: Room Booking API

Built with Specification-Driven Development (GitHub Spec Kit). The specification, plan and task list are in [`specs/001-room-booking-api/`](specs/001-room-booking-api/), and the project rules in [`.specify/memory/constitution.md`](.specify/memory/constitution.md).

FastAPI over SQLite (SQLAlchemy 2), Argon2id password hashes, 60-minute JWT access tokens. Python 3.11 or newer, managed with uv.

## Run it (from this `sdd/` folder)

```bash
uv sync
export ROOMAPI_SECRET_KEY="change-me-to-a-long-random-string"   # required; PowerShell: $env:ROOMAPI_SECRET_KEY = "..."
uv run python -m app.cli create-admin admin                      # prompts for a password (10-128 characters)
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs, click **Authorize** and log in. The OpenAPI document is also exported to [`../docs/openapi.json`](../docs/openapi.json).

## Test it

```bash
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

By default every test runs in-process on a fresh temporary database. To run the black-box acceptance tests against a running server instead, for example the vibe-coded version:

```bash
ROOMAPI_BASE_URL=http://127.0.0.1:8000 ROOMAPI_TEST_ADMIN=admin ROOMAPI_TEST_ADMIN_PASSWORD=... uv run pytest tests/acceptance
```

Each requirement's tests are listed in [`specs/001-room-booking-api/traceability.md`](specs/001-room-booking-api/traceability.md).

## Settings

| Variable | Default | Purpose |
|---|---|---|
| `ROOMAPI_SECRET_KEY` | none (required) | JWT signing key |
| `ROOMAPI_DB` | `roomapi.db` | SQLite file |
| `ROOMAPI_TOKEN_MINUTES` | `60` | token lifetime |
| `ROOMAPI_LOGIN_DELAY_SECONDS` | `2` | wait after 5 failed logins for a username within 15 minutes |

The booking rules are fixed by the spec, not configurable: 08:00–18:00 Helsinki time, at most 4 hours, at most 90 days ahead.
