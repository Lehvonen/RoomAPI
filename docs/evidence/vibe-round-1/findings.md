# Vibe round 1: probe findings

The round-1 API (commit `75113b5`) fails 9 of 14 probe checks. 4 are real bugs: 3 inputs cause an unhandled error (HTTP 500), and deactivating a room leaves its bookings in limbo. The other 5 are rules the prompt never specified, where the agent picked a default without asking. The 5 checks on overlap, ownership, past dates, time order and password storage hold.

Probed 2026-10-16 with [`probe.py`](probe.py) through FastAPI's TestClient, each check on a fresh throwaway database. Raw output: [`probe-output.txt`](probe-output.txt).

| ID | Check | Result | Type | Severity |
|---|---|---|---|---|
| P4a | `GET /rooms/{id}` with id 2^70 | Unhandled error, HTTP 500 | Bug: input validation | High |
| P4b | `POST /bookings` with room_id 2^70 | Unhandled error, HTTP 500 | Bug: input validation | High |
| P5 | Booking on 9999-12-31 23:00 at UTC-5 (past year 9999 in UTC) | Unhandled error, HTTP 500 | Bug: input validation | Medium |
| P3 | Admin deactivates a room with future bookings | Bookings stay `active`, but the owner gets 404 on the room | Bug: logic | Medium |
| P1 | One user books one room for 10 years | Accepted | Unspecified in prompt → agent chose no maximum length | Medium |
| P8 | 50 wrong passwords, then the right one | All 401, then login succeeds | Unspecified in prompt → agent chose no lockout or delay (security) | Medium |
| P2 | Booking 03:00–04:00 | Accepted | Unspecified in prompt → agent chose no opening hours | Low |
| P6 | Time sent without an offset, meant as Helsinki summer time (UTC+3) | Stored as UTC, 3 hours off | Unspecified in prompt → agent chose to read naive times as UTC | Low |
| P7 | Register with password `aaaaaaaa` | Accepted | Unspecified in prompt → agent chose length ≥ 8 as the only rule (security) | Low |
| OK1 | Overlapping booking on the same room | Rejected, 409 | — | Holds |
| OK2 | Another user cancels someone's booking | Refused, 404 | — | Holds |
| OK3 | Booking in the past | Rejected, 422 | — | Holds |
| OK4 | End before start | Rejected, 422 | — | Holds |
| OK5 | Password storage (white-box) | Salted PBKDF2-SHA256, not plain text | — | Holds |

Severity: High = any logged-in user can cause an unhandled error with one call; Medium = wrong data or abuse possible; Low = surprising but documented or minor.

## Method

- **Mostly black-box.** Every check goes through the HTTP API, with two white-box exceptions: `setup` creates the admin through `app.cli.create_admin` (the API has no way to do it), and OK5 reads the stored password hash straight from SQLite.
- **Iterations.** The probe lowers PBKDF2 to 1000 iterations for speed. The shipped default in `vibe/app/security.py` is 600 000.
- **Independent checks.** Each check runs on its own fresh database, so no check depends on another's leftovers.

## Who found these, and how

**Found by: AI + human.**

- `probe.py` and the choice of P1–P8 were written by Claude Code (model `claude-opus-5-5`) in a session prompted by Ivar Lehvonen. OK1–OK4, the password-storage check (OK5) and the timezone check (P6) follow the checks the team's plan listed for the vibe version: overlapping bookings, cancelling someone else's booking, password storage, and timezones, past dates, and end before start. The agent read the round-1 code first and chose the rest (P1–P5, P7, P8) from what the prompt left unspecified.
- Kristoffer Elfving-Millan reviewed the findings in PR #14 and re-ran the probe with the same 14 results.

Prompt that started this work (Ivar Lehvonen, 2026-10-16, verbatim):

```text
Kristoffer approved and merged it, check the repo and plan the next step and apply with the same method(s) as previous issue
```
