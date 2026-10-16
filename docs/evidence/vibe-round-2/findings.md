# Vibe round 2: probe findings

The round-2 API (commit `b68a979`) passes all 9 checks that failed in round 1, and the 5 checks that held still hold. But the fix for unlimited login attempts introduced a new problem: anyone can lock a real user out for 15 minutes (N1). From one IP address, 20 failures with any usernames, even ones that don't exist, lock out every user behind that address (N1b). The agent picked every new limit itself, because the prompt named symptoms, not rules.

Probed 2026-10-16 with [`probe.py`](probe.py), the round-1 probe with only the changes round 2's new rules force, plus the new checks N1 and N1b (all listed in its docstring). Raw output: [`probe-output.txt`](probe-output.txt). Method notes as in [round 1](../vibe-round-1/findings.md#method).

| ID | Check | Round 1 (`75113b5`) | Round 2 (`b68a979`) |
|---|---|---|---|
| P4a | `GET /rooms/{id}` with id 2^70 | HTTP 500 | 422, ID must be ≤ 2^63−1 |
| P4b | `POST /bookings` with room_id 2^70 | HTTP 500 | 422, ID must be ≤ 2^63−1 |
| P5 | Booking on 9999-12-31 23:00 at UTC-5 | HTTP 500 | 422, out of range |
| P3 | Admin deactivates a room with future bookings | Booking stays `active` | Booking `cancelled` in the same step |
| P1 | One user books one room for 10 years | Accepted | 422, at most 8 hours |
| P8 | 50 wrong passwords, then the right one | All 401, then success | 401 then 429; locked out |
| P2 | Booking 03:00–04:00 UTC (outside Helsinki opening hours) | Accepted | 422, only 07:00–20:00 local time |
| P6 | Time sent without an offset, meant as Helsinki local time | Read as UTC, so 3 hours off | Read as Helsinki time; still stored as UTC, but returned in local time (`+03:00` in summer, `+02:00` in winter) |
| P7 | Register with password `aaaaaaaa` | Accepted | 422, at least 10 characters |
| **N1** | **New:** an attacker sends 5 wrong passwords for alice, then alice logs in correctly | — | **429: alice is locked out** |
| **N1b** | **New:** 20 wrong logins for 20 non-existent usernames from one IP, then alice logs in correctly from the same IP | — | **429: alice is locked out.** Any shared address (campus or office NAT, a proxy) locks out everyone behind it. The agent's own test `test_login_lockout_per_ip_across_usernames` asserts exactly this. |
| OK1 | Overlapping booking | Rejected, 409 | Rejected, 409 |
| OK2 | Another user cancels someone's booking | Refused, 404 | Refused, 404 |
| OK3 | Booking in the past | Rejected, 422 | Rejected, 422 ("Cannot book a time in the past") |
| OK4 | End before start | Rejected, 422 | Rejected, 422 |
| OK5 | Password storage (white-box) | Salted PBKDF2-SHA256 | Salted PBKDF2-SHA256 |

## Found in code review (no probe check)

| ID | Issue | Where | Type |
|---|---|---|---|
| R1 | The lockout check isn't atomic. `lockout_seconds()` runs before the failed attempt is recorded, and outside a transaction, so parallel requests can get more than 5 guesses in. Single-request tests can't show it. | `vibe/app/routers/auth.py`, `login()` | Security (race condition) |
| R2 | The startup cleanup is inconsistent with `PATCH /rooms`. It cancels bookings in inactive rooms but leaves `cancelled_by` empty, while PATCH records the admin. It also runs on every startup and changes data without anyone asking. | `vibe/app/db.py`, `init_db()` | Logic |

## What round 2 decided on its own

None of these numbers or behaviours were in the prompt:

- Maximum booking 8 hours; bookings only 07:00–20:00 local time, within one day
- Time zone `Europe/Helsinki`. **Responses switched from UTC (`Z`) to local time with an offset (`+03:00`), an API contract change nobody asked for**: existing clients get a different format. Bookings stored before round 2 are not corrected.
- Passwords: at least 10 characters, letters plus a digit or symbol, at least 5 different characters, not containing the username, not on a common-password list
- Lockout: 5 failures per username or 20 per IP within 15 minutes, answered with 429. The agent warned that this lets anyone lock a user out (N1) and that behind a proxy all users share one IP limit; N1b shows the same happens with any shared address.
- Deactivating a room cancels its upcoming bookings. At every startup the app also cancels upcoming bookings in rooms that were already inactive, without recording who cancelled them (R2).

## Who found these, and how

**Found by: AI + human.**

- The round-2 code was written by a fresh Claude Code agent (`claude-opus-5-5`) that saw only the round-2 prompt.
- The probe was re-run and this comparison written by the Claude Code session that wrote the round-1 probe, acting on Ivar Lehvonen's delegation. Its changes to the probe are listed in the probe's docstring.
- N1 was added because the round-2 agent flagged the risk in its own reply ([`round-2-output.md`](../../vibe/round-2-output.md)).
- Kristoffer Elfving-Millan found N1b's full scope (from the agent's own test), R1 and R2 when reviewing PR #15. He also re-ran the tests (33 passed) and the probe.
