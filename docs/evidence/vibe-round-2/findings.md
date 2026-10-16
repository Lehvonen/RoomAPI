# Vibe round 2: probe findings

The round-2 API (commit `b68a979`) passes all 9 checks that failed in round 1, and the 5 checks that held still hold. But the fix for unlimited login attempts introduced a new problem: anyone can lock a real user out for 15 minutes (N1). The agent picked every new limit itself, because the prompt named symptoms, not rules.

Probed 2026-10-16 with [`probe.py`](probe.py), the round-1 probe with only the changes round 2's new rules force (listed in its docstring). Raw output: [`probe-output.txt`](probe-output.txt). Method notes as in [round 1](../vibe-round-1/findings.md#method).

| ID | Check | Round 1 (`75113b5`) | Round 2 (`b68a979`) |
|---|---|---|---|
| P4a | `GET /rooms/{id}` with id 2^70 | HTTP 500 | 422, ID must be ≤ 2^63−1 |
| P4b | `POST /bookings` with room_id 2^70 | HTTP 500 | 422, ID must be ≤ 2^63−1 |
| P5 | Booking on 9999-12-31 23:00 at UTC-5 | HTTP 500 | 422, out of range |
| P3 | Admin deactivates a room with future bookings | Booking stays `active` | Booking `cancelled` in the same step |
| P1 | One user books one room for 10 years | Accepted | 422, at most 8 hours |
| P8 | 50 wrong passwords, then the right one | All 401, then success | 401 then 429; locked out |
| P2 | Booking 03:00–04:00 UTC (06:00 Helsinki) | Accepted | 422, only 07:00–20:00 local time |
| P6 | Time sent without an offset, meant as Helsinki time | Stored as UTC, 3 hours off | Read as Helsinki time; responses now carry `+03:00` |
| P7 | Register with password `aaaaaaaa` | Accepted | 422, at least 10 characters |
| **N1** | **New:** an attacker sends 5 wrong passwords for alice, then alice logs in correctly | — | **429: alice is locked out** |
| OK1 | Overlapping booking | Rejected, 409 | Rejected, 409 |
| OK2 | Another user cancels someone's booking | Refused, 404 | Refused, 404 |
| OK3 | Booking in the past | Rejected, 422 | Rejected, 422 ("Cannot book a time in the past") |
| OK4 | End before start | Rejected, 422 | Rejected, 422 |
| OK5 | Password storage (white-box) | Salted PBKDF2-SHA256 | Salted PBKDF2-SHA256 |

## What round 2 decided on its own

None of these numbers or behaviours were in the prompt:

- Maximum booking 8 hours; bookings only 07:00–20:00 local time, within one day
- Time zone `Europe/Helsinki`. Responses switched from UTC (`Z`) to local time with an offset (`+03:00`), which changes the API's output format for existing clients. Bookings stored before round 2 are not corrected.
- Passwords: at least 10 characters, letters plus a digit or symbol, at least 5 different characters, not containing the username, not on a common-password list
- Lockout: 5 failures per username or 20 per IP within 15 minutes, answered with 429. The agent itself warned that this lets anyone lock a user out (N1) and that behind a proxy all users share one IP limit.
- Deactivating a room cancels its upcoming bookings, and at startup the app also cancels upcoming bookings in rooms that were already inactive.

## Who found these, and how

**Found by: AI; human review follows in the pull request.** The round-2 code was written by a fresh Claude Code agent (`claude-opus-5-5`) that saw only the round-2 prompt. The probe was re-run and this comparison written by the Claude Code session that wrote the round-1 probe, acting on Ivar Lehvonen's delegation. Its changes to the probe are listed in the probe's docstring. N1 was added because the round-2 agent flagged the risk in its own reply ([`round-2-output.md`](../../vibe/round-2-output.md)).
